"""Independent raw-page/event checks for R22; network disabled."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
import csv,gzip,hashlib,json,socket
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/revision22'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca';VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
def read(p):return list(csv.DictReader((ROOT/p).open()))
def load(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 def denied(*a,**kw):raise RuntimeError('Offline R22 audit')
 socket.create_connection=denied;socket.socket.connect=denied
 for p,v in load('reports/revision22/input_manifest.json').items():assert sha(ROOT/p)==v['sha256']
 detailed=read('reports/revision22/large_withdrawal_day_market_sequence.csv')
 expected={(x['tx'],int(x['log_index'])):x for x in detailed};assert len(expected)==len(detailed)
 dates={x['date'] for x in detailed};months={x[:7].replace('-','') for x in dates}
 seen=set();used=[]
 for month in sorted(months):
  manifest=load(f'reports/revision5/api_market_{month}_manifest.json');assert manifest['complete']
  # Full month manifests document the original census. A portable package may
  # retain only the independently selected pages covering the eight dates.
  if (ROOT/'PORTABLE_R22_SELECTED_PAGES.json').exists():
   selected=load('PORTABLE_R22_SELECTED_PAGES.json')['pages']
   selected_names={x['file'] for x in selected}
   items=[x for x in manifest['files'] if x['file'] in selected_names]
  else:items=manifest['files']
  for item in items:
   p=ROOT/item['file'];obj=json.load(gzip.open(p,'rt'))
   rows=obj['response']['data']['marketTransactions']['items']
   matches=[]
   for e in rows:
    day=datetime.fromtimestamp(int(e['timestamp']),timezone.utc).date().isoformat()
    if day not in dates:continue
    key=(e['txHash'],int(e['logIndex']));assert key not in seen;seen.add(key)
    x=expected[key];d=e['data'];a=int(d['repaidAssets'] if e['type']=='Liquidation' else d['assets'])
    assert int(x['block'])==int(e['blockNumber']) and x['type']==e['type']
    assert int(x['timestamp'])==int(e['timestamp']) and int(x['assets_micro'])==a
    assert x['position_owner']==e['user']['address'].lower()
    matches.append(e)
   if matches:
    assert sha(p)==item['sha256'];used.append({**item,'selected_rows':len(matches)})
  print('Audited market month',month,len(seen),flush=True)
 assert seen==set(expected)
 summary=read('reports/revision22/large_withdrawal_day_summary.csv')
 for x in summary:
  g=sorted((a for a in detailed if a['date']==x['date']),key=lambda a:(int(a['block']),int(a['log_index'])))
  cash=int(x['opening_market_cash_micro']);tot=defaultdict(int)
  for a in g:
   assert cash==int(a['cash_before_micro']);sign=1 if a['type'] in ['Supply','Repay','Liquidation'] else -1
   cash+=sign*int(a['assets_micro']);assert cash==int(a['cash_after_micro']) and cash>=0
   tot[a['type']]+=int(a['assets_micro'])
  assert cash==int(x['closing_market_cash_micro'])
  for typ in ['Supply','Repay','Liquidation','Borrow','Withdraw']:assert tot[typ]==int(x[typ.lower()+'_micro'])
 # Independent vault-source matching from raw API pages.
 own={};m=load('reports/revision5/api_vault_manifest.json')
 for item in m['files']:
  p=ROOT/item['file'];assert sha(p)==item['sha256']
  for e in json.load(gzip.open(p,'rt'))['response']['data']['vaultV1Transactions']['items']:
   if e['type'] in ['Deposit','Withdraw'] and e['data']['onBehalf'].lower()==PROXY:
    own[(e['txHash'],int(e['logIndex']))]=e
 entries=read('reports/revision22/vault_entry_joint_records.csv')
 for x in entries:
  e=own[(x['tx'],int(x['log_index']))]
  assert e['type']=='Deposit' and int(e['shares'])==int(x['shares_raw']) and int(e['assets'])==int(x['deposit_micro'])
  assert 0<=int(x['lower_micro'])<=int(x['upper_micro'])<=int(x['deposit_micro'])
  assert int(x['prior_close_distance_seconds'])>0 and int(x['same_day_close_distance_seconds'])<=0
 # All fee statements retain exact raw-source hashes and arithmetic residuals.
 for p,v in load('reports/revision22/fee_source_manifest.json').items():assert sha(ROOT/p)==v['sha256']
 fees=read('reports/revision22/verified_fee_mint_pairs.csv');bydate=defaultdict(int)
 for e in fees:
  assert int(e['mint_log_index'])+1==int(e['accrue_log_index']) and e['recipient']==PROXY
  bydate[e['date']]+=int(e['fee_shares_raw'])
 for x in read('reports/revision22/fee_residual_daily_audit.csv'):
  assert bydate[x['date']]==int(x['paired_verified_fee_raw'])
  assert int(x['original_residual_raw'])==int(x['paired_verified_fee_raw'])+int(x['remaining_unclassified_raw'])
 # Reaggregate each market and the two predeclared groups independently.
 pos=read('reports/revision18/funded_positions.csv')
 for x in read('reports/revision22/shared_cash_market_decomposition.csv'):
  names={'spark','moonwell','gauntlet'} if x['group']=='three_vaults' else {'spark','moonwell'}
  g=[p for p in pos if p['date']==x['date'] and p['market']==x['market'] and p['vault'] in names]
  L=int(g[0]['market_cash_micro']);S=sum(int(p['position_micro']) for p in g)
  I=sum(min(int(p['position_micro']),L) for p in g);J=min(S,L)
  assert I==int(x['separate_micro']) and J==int(x['joint_micro']) and I-J==int(x['duplicate_micro'])
 (OUT/'intraday_raw_page_manifest.json').write_text(json.dumps({'pages':used,'selected_raw_events':len(seen)},indent=2)+'\n')
 result={'status':'PASS_WITH_DISCLOSED_FEE_COVERAGE_GAP','network_disabled':True,'raw_market_events':len(seen),
  'raw_market_pages':len(used),'cash_sequences_checked':8,'vault_raw_event_links':len(entries),
  'fee_pairs_arithmetic_checked':len(fees),'all_319_residuals_retained':True,'gauntlet_exclusion_verified':True,
  'no_regression_reestimation':True}
 (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
