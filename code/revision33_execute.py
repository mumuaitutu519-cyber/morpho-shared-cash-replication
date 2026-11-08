from pathlib import Path
import pandas as pd,json,requests,time
from revision24_rpc import selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision33';RAW=O/'execution_raw';RAW.mkdir(exist_ok=True);V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';q=pd.read_csv(O/'execution_selection.csv',dtype=str);assert len(q)>=10;rows=[]
for r in q.itertuples():
 amount=int(r.claim_micro_before);data=selector('withdraw(uint256,address,address)')+f'{amount:064x}'+r.owner[2:].zfill(64)*2
 for phase,b in [('before',int(r.deposit_block)-1),('after',int(r.deposit_block))]:
  req={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'from':r.owner,'to':V,'data':data,'gas':'0x989680'},hex(b)]};p=RAW/f'{b}_{r.owner}.json'
  if p.exists():o=json.loads(p.read_text());assert o['request']==req
  else:
   time.sleep(1.6);resp=requests.post('https://base.drpc.org',json=req,timeout=40);o={'request':req,'response':resp.json(),'http_status':resp.status_code};p.write_text(json.dumps(o,indent=2));assert resp.status_code not in [401,403,429]
  z=o['response'];status='success' if 'result' in z else 'liquidity_revert' if z.get('error',{}).get('data')=='0x4323a555' else 'other_error';assert status!='other_error',z
  rows.append({'tx':r.tx,'owner':r.owner,'selection':r.selection,'phase':phase,'state_block':b,'request_micro':str(amount),'status':status})
pd.DataFrame(rows).to_csv(O/'fixed_request_executions.csv',index=False);print(pd.DataFrame(rows).to_string(index=False))
