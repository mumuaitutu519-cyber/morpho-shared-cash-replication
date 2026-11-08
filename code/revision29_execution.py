from pathlib import Path
import pandas as pd,json,time,requests
from revision24_rpc import selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision29';E='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
s=pd.read_csv(O/'holder_before_after_states.csv',dtype=str);q=s[(s.owner==E)&(s.phase=='before')&(s.claim_micro.astype('int64')>0)];rows=[]
for r in q.itertuples():
 amount=int(r.claim_micro);data=selector('withdraw(uint256,address,address)')+f'{amount:064x}'+E[2:].zfill(64)*2
 for phase,block in [('before',int(r.deposit_block)-1),('after',int(r.deposit_block))]:
  body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'from':E,'to':V,'data':data,'gas':'0x989680'},hex(block)]};p=O/'raw'/f'{r.deposit_block}_{phase}_ethena_fixed_withdraw.json'
  if p.exists():o=json.loads(p.read_text());assert o['request']==body
  else:
   time.sleep(1.5);res=requests.post('https://base.drpc.org',json=body,timeout=45);o={'request':body,'response':res.json(),'url':'https://base.drpc.org'};p.write_text(json.dumps(o,indent=2))
  resp=o['response'];status='success' if 'result' in resp else 'liquidity_revert' if '4323a555' in json.dumps(resp) else 'other_error'
  rows.append({'deposit_block':r.deposit_block,'phase':phase,'request_usdc':amount/1e6,'status':status,'response':json.dumps(resp)})
pd.DataFrame(rows).to_csv(O/'ethena_fixed_request_execution.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
