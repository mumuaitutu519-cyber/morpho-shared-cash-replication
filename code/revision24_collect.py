"""Fixed 94 deposit-equivalent eth_call requests at their block-end states."""
import csv,json,gzip,hashlib
from pathlib import Path
from revision24_rpc import ROOT,RAW,query,selector,call,withdraw,PWORD
from revision24_rpc import encode_bytes_array,decode_bytes_array
OUT=ROOT/'reports/revision24'
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2)+'\n')
def main():
 rows=list(csv.DictReader((ROOT/'reports/revision22/vault_entry_joint_records.csv').open()))
 assert len(rows)==94 and len({x['tx'] for x in rows})==93
 assert int(query('drpc_chain','eth_chainId',[],'drpc')['result'],16)==8453
 receipts={x['tx_hash']:x for x in json.loads((ROOT/'reports/revision6/domain_6_receipts.json').read_text())['items']}
 done=[]
 for x in sorted(rows,key=lambda x:(int(x['block']),int(x['log_index']))):
  b=int(x['block']);receipt=json.load(gzip.open(ROOT/receipts[x['tx']]['file'],'rt'))['response']['result']
  header=query(f'drpc_header_{b}','eth_getBlockByNumber',[hex(b),False],'drpc')['result']
  assert header['hash']==receipt['blockHash'] and int(header['timestamp'],16)==int(x['timestamp'])
  i=int(receipt['transactionIndex'],16);assert header['transactions'][i]==x['tx']
  data=selector('multicall(bytes[])')+encode_bytes_array([selector('balanceOf(address)')+PWORD,selector('maxWithdraw(address)')+PWORD])
  views=query(f'drpc_views_{b}','eth_call',[call(data),hex(b)],'drpc')
  if 'result' not in views:raise RuntimeError(f'Views unavailable at {b}: {views}')
  s,w=map(lambda a:int(a,16),decode_bytes_array(views['result'],2))
  conv=query(f'drpc_claim_{b}','eth_call',[call(selector('convertToAssets(uint256)')+f'{s:064x}'),hex(b)],'drpc')
  if 'result' not in conv:raise RuntimeError(f'Claim unavailable at {b}: {conv}')
  c=int(conv['result'],16);d=int(x['deposit_micro'])
  response=query(f'drpc_withdraw_{b}_{x["log_index"]}','eth_call',[call(withdraw(d)),hex(b)],'drpc')
  status='unresolved';burn=None;error=response.get('error')
  if isinstance(response.get('result'),str) and len(response['result'])==66:
   burn=int(response['result'],16);assert 0<burn<=s;status='success'
  elif isinstance(error,dict) and error.get('data')==selector('NotEnoughLiquidity()'):status='liquidity_revert'
  elif isinstance(error,dict) and str(error.get('data','')).startswith('0x'):status='other_contract_revert'
  result={**x,'post_block_hash':header['hash'],'transaction_index':i,'block_transactions':len(header['transactions']),
   'later_block_transactions':len(header['transactions'])-i-1,'state_boundary':'deposit_block_end',
   'post_shares_raw':str(s),'post_claim_micro':str(c),'post_capacity_micro':str(w),'deposit_equivalent_execution':status,
   'burned_shares_raw':str(burn) if burn is not None else '', 'execution_error':json.dumps(error,separators=(',',':')) if error else '',
   'deposit_exceeds_capacity':d>w,'post_coverage':w/c,'deposit_capacity_ratio':w/d,
   'post_coverage_below_25pct':4*w<c,'header_archive':f'data/raw/revision24/drpc_header_{b}.body',
   'execution_archive':f'data/raw/revision24/drpc_withdraw_{b}_{x["log_index"]}.body'}
  if status in ['success','liquidity_revert']:assert (status=='success')==(d<=w)
  done.append(result)
  with (OUT/'deposit_block_end_calls.csv').open('w',newline='') as f:
   wr=csv.DictWriter(f,fieldnames=list(done[0]));wr.writeheader();wr.writerows(done)
  save('collection_progress.json',{'completed':len(done),'planned':94,'statuses':{k:sum(z['deposit_equivalent_execution']==k for z in done) for k in ['success','liquidity_revert','other_contract_revert','unresolved']},'state_boundary':'block end, not transaction-index replay','read_only':True})
  print(len(done),b,status,'D/W',round(d/w,4),flush=True)
 save('raw_manifest.json',{str(p.relative_to(ROOT)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(RAW.iterdir()) if p.is_file() and not p.name.startswith('.')})
if __name__=='__main__':main()
