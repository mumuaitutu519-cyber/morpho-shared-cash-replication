"""Classify only raw paired fee mints; retain uncovered dates and residuals."""
from pathlib import Path
from collections import defaultdict
import bisect,csv,gzip,hashlib,json,statistics,urllib.parse
import pandas as pd
from Crypto.Hash import keccak
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/revision27'
VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
def topic(s):
 h=keccak.new(digest_bits=256);h.update(s.encode());return '0x'+h.hexdigest()
FEE=topic('AccrueInterest(uint256,uint256)');TRANSFER=topic('Transfer(address,address,uint256)')
RECIPIENT=topic('SetFeeRecipient(address)')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def main():
 states=pd.read_csv(ROOT/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date')
 flows=pd.read_csv(ROOT/'reports/revision21/daily_flow_stock_reconciliation.csv',dtype=str)
 boundaries=[int(x) for x in states.block];dates=list(states.index)
 raw={};files={};coverage=defaultdict(list)
 def add(e,p,block=None,tx=None):
  if e.get('address','').lower()!=VAULT:return
  b=block if block is not None else int(e['blockNumber'],16)
  if not boundaries[0]<b<=boundaries[-1]:return
  idx=e.get('logIndex');idx=int(idx,16) if isinstance(idx,str) else int(idx)
  tx=tx or e['transactionHash'];topics=[x.lower() for x in e['topics'] if x is not None]
  val={'block':b,'tx':tx.lower(),'log_index':idx,'topics':topics,'data':e['data'].lower()}
  key=(b,idx);rel=str(p.relative_to(ROOT))
  if key in raw:assert {k:raw[key][k] for k in val}==val
  else:raw[key]={**val,'sources':[]}
  if rel not in raw[key]['sources']:raw[key]['sources'].append(rel)
  if rel not in files:files[rel]={'sha256':sha(p),'bytes':p.stat().st_size}
 # Successful complete Blockscout subranges, including ranges collected before stop.
 for meta in sorted((ROOT/'data/raw/revision22/fees').glob('*.json')):
  if meta.name.startswith('.'):continue
  m=json.loads(meta.read_text());p=meta.with_suffix('.body')
  assert sha(p)==m['sha256']
  if m['status']!=200:continue
  obj=json.loads(p.read_text());logs=obj.get('result')
  if not isinstance(logs,list):continue
  query=urllib.parse.parse_qs(urllib.parse.urlparse(m['url']).query)
  if len(logs)<1000:
   coverage[query['topic0'][0]].append((int(query['fromBlock'][0]),int(query['toBlock'][0])))
  for e in logs:add(e,p)
 # Existing receipt samples are partial observations, never full-date coverage.
 receipt_manifest=json.loads((ROOT/'reports/revision6/domain_6_receipts.json').read_text())
 for item in receipt_manifest['items']:
  p=ROOT/item['file'];assert sha(p)==item['sha256']
  response=json.load(gzip.open(p,'rt'))['response']['result']
  if response is None:continue
  for e in response.get('logs',[]):add(e,p)
 # The independent partial SQD scan contributes verified events, not a full day.
 p=ROOT/'data/raw/revision22/sqd_fee_probe.body'
 if p.exists():
  meta=json.loads(p.with_suffix('.json').read_text())
  if meta['status']==200:
   blocks=[json.loads(line) for line in p.read_text().splitlines() if line]
   for block in blocks:
    for e in block.get('logs',[]):add(e,p,block=int(block['header']['number']))
   if blocks:coverage[FEE].append((meta['query']['fromBlock'],int(blocks[-1]['header']['number'])))
 # Complete raw log census for all original nonzero-residual dates.
 for item in json.loads((ROOT/'reports/revision27/fee_census_coverage.json').read_text()):
  p=ROOT/item['file'];meta=json.loads(p.read_text());assert meta['request']['method']=='eth_getLogs'
  logs=meta['response']['result'];assert isinstance(logs,list)
  for e in logs:add(e,p)
  for topic0 in [FEE,TRANSFER]:coverage[topic0].append((item['from'],item['through']))
 def covered(topic0,lo,hi):
  cursor=lo
  for a,b in sorted(coverage[topic0]):
   if a<=cursor<=b:cursor=b+1
   if cursor>hi:return True
  return False
 paired=[];unpaired=[];fee_by_day=defaultdict(int);raw_mints_by_day=defaultdict(int)
 for (block,idx),e in sorted(raw.items()):
  day=dates[bisect.bisect_left(boundaries,block)]
  if e['topics'][0]==TRANSFER and len(e['topics'])==3 and int(e['topics'][1],16)==0 and e['topics'][2][-40:]==PROXY[2:]:
   raw_mints_by_day[day]+=int(e['data'],16)
  if e['topics'][0]!=FEE:continue
  assert len(e['data'])==130
  amount=int(e['data'][66:],16)
  if amount==0:continue
  mint=raw.get((block,idx-1))
  if mint and mint['tx']==e['tx'] and mint['topics'][0]==TRANSFER and len(mint['topics'])==3 and int(mint['topics'][1],16)==0 and int(mint['data'],16)==amount:
   recipient='0x'+mint['topics'][2][-40:]
   if recipient==PROXY:
    fee_by_day[day]+=amount
    paired.append({'date':day,'block':block,'tx':e['tx'],'mint_log_index':idx-1,'accrue_log_index':idx,
       'recipient':recipient,'fee_shares_raw':str(amount),'fee_new_total_assets_micro':str(int(e['data'][2:66],16)),
       'sources':';'.join(sorted(set(mint['sources']+e['sources'])))})
  else:unpaired.append({'date':day,'block':block,'tx':e['tx'],'accrue_log_index':idx,'fee_shares_raw':str(amount),'sources':';'.join(e['sources'])})
 rows=[];cumulative=0;original_cumulative=0
 for f in flows.itertuples():
  day=f.date;prev=(pd.Timestamp(day)-pd.Timedelta(days=1)).strftime('%Y-%m-%d')
  lo=int(states.loc[prev,'block'])+1;hi=int(states.loc[day,'block'])
  full=covered(FEE,lo,hi) and covered(TRANSFER,lo,hi)
  residual=int(f.unexplained_share_change_raw);verified=fee_by_day[day];remaining=residual-verified
  assert remaining>=0,(day,residual,verified)
  if full:
   assert raw_mints_by_day[day]==int(f.minted_shares_raw)+verified
   assert remaining==0,(day,'Full raw coverage but unexplained gap')
  cumulative+=remaining;original_cumulative+=residual
  C=int(states.loc[day,'claim_micro']);shares=int(states.loc[day,'treasury_shares']);W=int(states.loc[day,'max_withdraw_micro'])
  omission_value=cumulative*C//shares
  rows.append({'date':day,'original_residual_raw':str(residual),'paired_verified_fee_raw':str(verified),'remaining_unclassified_raw':str(remaining),
    'complete_accrue_and_owner_mint_day':full,'raw_owner_mints_raw':str(raw_mints_by_day[day]),
    'unclassified_cumulative_raw':str(cumulative),'historical_shares_raw':str(shares),'unclassified_cumulative_pct_shares':100*cumulative/shares,
    'omitted_share_value_at_daily_average_price_micro':str(omission_value),'observed_claim_micro':str(C),'observed_capacity_micro':str(W),
    'coverage_overstatement_if_remaining_shares_omitted_pp':100*W/(C-omission_value)-100*W/C})
 pd.DataFrame(rows).to_csv(OUT/'fee_residual_daily_audit.csv',index=False)
 pd.DataFrame(paired).to_csv(OUT/'verified_fee_mint_pairs.csv',index=False)
 pd.DataFrame(unpaired).to_csv(OUT/'unpaired_fee_events.csv',index=False)
 save('fee_source_manifest.json',files)
 selected=[x for x in rows if int(x['original_residual_raw'])!=0]
 result={'status':'PASS_WITH_REMAINING_COVERAGE_GAP' if any(int(x['remaining_unclassified_raw']) for x in rows) else 'PASS_RESIDUAL_CLOSED','residual_target_days':170,'all_daily_balances':319,
  'complete_target_days':sum(x['complete_accrue_and_owner_mint_day'] for x in selected),
  'days_with_paired_verified_fees':sum(int(x['paired_verified_fee_raw'])>0 for x in selected),
  'paired_fee_events':len(paired),'unpaired_positive_fee_events':len(unpaired),
  'original_residual_raw':str(sum(int(x['original_residual_raw']) for x in rows)),
  'paired_verified_fee_raw':str(sum(int(x['paired_verified_fee_raw']) for x in rows)),
  'remaining_unclassified_raw':str(sum(int(x['remaining_unclassified_raw']) for x in rows)),
  'remaining_nonzero_days':sum(int(x['remaining_unclassified_raw'])>0 for x in rows),
  'max_daily_remaining_shares':max(int(x['remaining_unclassified_raw'])/1e18 for x in rows),
  'max_remaining_cumulative_pct_shares':max(x['unclassified_cumulative_pct_shares'] for x in rows),
  'max_coverage_overstatement_omission_pp':max(x['coverage_overstatement_if_remaining_shares_omitted_pp'] for x in rows),
  'terminal_omitted_share_value_micro':rows[-1]['omitted_share_value_at_daily_average_price_micro'],
  'contract_claim_and_capacity_changed':False,
  'scope':'Only exact paired raw zero-address owner Transfer immediately followed by AccrueInterest is classified as a fee mint. Complete log census over all 170 original nonzero-residual dates; other dates retain direct-state reconciliation and selected prior records. Omission benchmark is not a statistical bound or return.'}
 save('fee_residual_summary.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
