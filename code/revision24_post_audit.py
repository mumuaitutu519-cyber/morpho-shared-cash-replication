"""Offline audit of block-end calls and observed intervening operations."""
from pathlib import Path
from collections import Counter
import csv,json,gzip,hashlib,socket,statistics
import pandas as pd
from revision24_rpc import ROOT,RAW,selector,call,withdraw,PWORD,VAULT,PROXY
from revision24_rpc import decode_bytes_array,encode_bytes_array
OUT=ROOT/'reports/revision24';MORPHO='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb'
def read(p):return list(csv.DictReader((ROOT/p).open()))
def load(p):return json.loads((ROOT/p).read_text())
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2)+'\n')
def write(n,rows):
 with (OUT/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def raw(name,method,params):
 meta=load('data/raw/revision24/'+name+'.json');p=RAW/(name+'.body')
 assert meta['request']=={'jsonrpc':'2.0','id':1,'method':method,'params':params}
 assert meta['sha256']==hashlib.sha256(p.read_bytes()).hexdigest() and meta['http_status']==200
 return json.loads(p.read_bytes())
def main():
 def deny(*a,**k):raise RuntimeError('Offline R24 audit')
 socket.create_connection=deny;socket.socket.connect=deny
 rows=read('reports/revision24/deposit_block_end_calls.csv');assert len(rows)==94
 old={(x['tx'],x['log_index']):x for x in read('reports/revision22/vault_entry_joint_records.csv')}
 frames={x['destination_tx']:x for x in load('reports/revision6/domain_6_first_disposition_manifest.json')['items']}
 receipts={x['tx_hash']:x for x in load('reports/revision6/domain_6_receipts.json')['items']}
 market=pd.read_parquet(ROOT/'reports/revision5/market_economic_events.parquet')
 vault=pd.read_parquet(ROOT/'reports/revision5/vault_economic_events.parquet')
 events=[];stats=[];examples=[]
 for x in rows:
  assert all(x[k]==v for k,v in old[x['tx'],x['log_index']].items())
  b=int(x['block']);i=int(x['transaction_index']);d=int(x['deposit_micro'])
  h=raw(f'drpc_header_{b}','eth_getBlockByNumber',[hex(b),False])['result']
  recpath=ROOT/receipts[x['tx']]['file'];assert hashlib.sha256(recpath.read_bytes()).hexdigest()==receipts[x['tx']]['sha256']
  receipt=json.load(gzip.open(recpath,'rt'))['response']['result']
  assert h['hash']==receipt['blockHash']==x['post_block_hash'] and h['transactions'][i]==x['tx']
  assert int(receipt['transactionIndex'],16)==i and int(h['timestamp'],16)==int(x['timestamp'])
  viewsdata=selector('multicall(bytes[])')+encode_bytes_array([selector('balanceOf(address)')+PWORD,selector('maxWithdraw(address)')+PWORD])
  s,w=map(lambda t:int(t,16),decode_bytes_array(raw(f'drpc_views_{b}','eth_call',[call(viewsdata),hex(b)])['result'],2))
  c=int(raw(f'drpc_claim_{b}','eth_call',[call(selector('convertToAssets(uint256)')+f'{s:064x}'),hex(b)])['result'],16)
  rr=raw(f'drpc_withdraw_{b}_{x["log_index"]}','eth_call',[call(withdraw(d)),hex(b)])
  if 'result' in rr:
   status='success';assert 0<int(rr['result'],16)<=s
  elif rr.get('error',{}).get('data')==selector('NotEnoughLiquidity()'):status='liquidity_revert'
  else:status='other_or_unresolved'
  assert status==x['deposit_equivalent_execution'] and (s,c,w)==tuple(int(x[k]) for k in ['post_shares_raw','post_claim_micro','post_capacity_micro'])
  assert (d<=w)==(status=='success')
  assert abs(float(x['post_coverage'])-w/c)<1e-14 and abs(float(x['deposit_capacity_ratio'])-w/d)<1e-10
  assert x['post_coverage_below_25pct']==str(4*w<c) and x['deposit_exceeds_capacity']==str(d>w)
  file=next(z for z in frames[x['tx']]['files'] if '_usdc_logs.' in z['file']);p=ROOT/file['file']
  assert hashlib.sha256(p.read_bytes()).hexdigest()==file['sha256']
  logs=json.load(gzip.open(p,'rt'))['response']['result']
  later=[z for z in logs if int(z['transactionIndex'],16)>i]
  def address(t):return '0x'+t[-40:].lower()
  relevant=[z for z in later if {address(t) for t in z['topics'][1:]}&{VAULT,PROXY,MORPHO}]
  for z in relevant:
   assert z['blockHash']==h['hash'] and not z['removed']
   events.append({'deposit_tx':x['tx'],'deposit_log':x['log_index'],'block':b,'later_tx':z['transactionHash'],
    'transaction_index':int(z['transactionIndex'],16),'log_index':int(z['logIndex'],16),
    'from':address(z['topics'][1]),'to':address(z['topics'][2]),'usdc_micro':str(int(z['data'],16)),
    'source_file':file['file']})
  txpos={t:j for j,t in enumerate(h['transactions'])}
  common=market[(market.block==b)&market.tx.map(lambda t:txpos.get(t,-1)>i)]
  ve=vault[(vault.timestamp==int(x['timestamp']))&vault.tx.map(lambda t:txpos.get(t,-1)>i)]
  delta=sum(int(z.assets_raw)*(1 if z.type in ['Supply','Repay','Liquidation'] else -1) for z in common.itertuples())
  stats.append({**x,'later_relevant_usdc_transfers':len(relevant),'later_common_market_events':len(common),
   'later_common_market_net_cash_micro':str(delta),'later_prepared_vault_events':len(ve),
   'exact_last_transaction_state':i==len(h['transactions'])-1,
   'no_observed_following_cash_or_vault_event':len(relevant)==len(common)==len(ve)==0})
 write('deposit_post_state_audit.csv',stats)
 controls=load('reports/revision24/execution_controls.json')
 bs=sorted({int(x['block']) for x in rows});assert {x['block'] for x in controls}=={bs[0],bs[len(bs)//2],bs[-1]} and len(controls)==6
 for x in controls:
  rr=raw(f'drpc_control_{x["block"]}_{x["scenario"]}','eth_call',[call(withdraw(int(x['amount_micro']))),hex(x['block'])])
  assert rr==x['response']
  c=int(next(z['post_claim_micro'] for z in rows if int(z['block'])==x['block']))
  if x['scenario']=='micro':assert int(x['amount_micro'])==1 and int(rr['result'],16)>0
  else:assert int(x['amount_micro'])==2*c+1000000 and rr['error']['data']==selector('NotEnoughLiquidity()')
 if events:write('intervening_usdc_transfers.csv',events)
 else:(OUT/'intervening_usdc_transfers.csv').write_text('deposit_tx,deposit_log,block,later_tx,transaction_index,log_index,from,to,usdc_micro,source_file\n')
 total=sum(int(x['deposit_micro']) for x in stats)
 summary={'events':94,'transactions':len({x['tx'] for x in stats}),'deposit_micro':str(total),
  'statuses':dict(Counter(x['deposit_equivalent_execution'] for x in stats)),
  'below_quarter_block_end':sum(4*int(x['post_capacity_micro'])<int(x['post_claim_micro']) for x in stats),
  'below_quarter_but_deposit_executes':sum(4*int(x['post_capacity_micro'])<int(x['post_claim_micro']) and x['deposit_equivalent_execution']=='success' for x in stats),
  'capacity_to_deposit_min':min(float(x['deposit_capacity_ratio']) for x in stats),
  'capacity_to_deposit_median':statistics.median(float(x['deposit_capacity_ratio']) for x in stats),
  'later_transactions_min':min(int(x['later_block_transactions']) for x in stats),
  'later_transactions_median':statistics.median(int(x['later_block_transactions']) for x in stats),
  'later_transactions_max':max(int(x['later_block_transactions']) for x in stats),
  'last_transaction_events':sum(x['exact_last_transaction_state'] for x in stats),
  'events_with_later_relevant_usdc':sum(x['later_relevant_usdc_transfers']>0 for x in stats),
  'events_with_later_common_market_operations':sum(x['later_common_market_events']>0 for x in stats),
  'events_with_later_prepared_vault_operations':sum(x['later_prepared_vault_events']>0 for x in stats),
  'no_observed_following_cash_or_vault_events':sum(x['no_observed_following_cash_or_vault_event'] for x in stats),
  'state_boundary':'Final state of the deposit block. Timestamp equality does not establish transaction-position equality.',
  'coverage_limit':'Full raw block USDC transfer records plus the prepared common-market and vault event ledgers; not a full trace of every later operation or unlogged configuration update.',
  'read_only':True,'network_disabled_for_audit':True,'external_independent_replication':False}
 summary['execution_controls_verified']=6
 save('post_state_summary.json',summary);print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
