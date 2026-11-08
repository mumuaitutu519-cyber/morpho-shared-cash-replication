"""Balance and order attribution over a complete, fixed Base observation window."""
from pathlib import Path
import requests,json,hashlib,pandas as pd,numpy as np
from scipy.optimize import linprog
from revision24_rpc import selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';U='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913';lo=34450000;hi=34758680
balances={}
for block in [lo-1,hi]:
 q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':U,'data':selector('balanceOf(address)')+A[2:].zfill(64)},hex(block)]};p=O/'raw'/f'ethena_boundary_{block}.json'
 if p.exists():ob=json.loads(p.read_text())
 else:
  r=requests.post('https://base.drpc.org',json=q,timeout=35);ob={'request':q,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2))
 assert 'result' in ob['response'],ob;balances[block]=int(ob['response']['result'],16)
d=pd.read_csv(O/'ethena_usdc_ledger.csv',dtype={'amount_raw':str}).sort_values(['block','log_index']);bal=balances[lo-1];sources=sorted(d[d.to.eq(A)]['from'].unique());out=[]
for r in d.to_dict('records'):
 amount=int(r['amount_raw']);bal+=amount if r['to']==A else -amount;assert bal>=0;out.append({**r,'balance_after_raw':str(bal)})
assert bal==balances[hi];p=pd.DataFrame(out);p.to_csv(O/'ethena_reconciled_ledger.csv',index=False)
# One common feasible set per source over the entire window, in USDC units.
# Other sources compete, but separately reported source marginal endpoints are not added.
withdraw=p[p['from'].eq(A)].copy();assert withdraw.to.eq('0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a').all();N=len(withdraw);bounds=withdraw.amount_raw.map(lambda x:(0,int(x)/1e6)).tolist();answers=[];groups=[]
for source in sources:
 F=0;k=0;lhs=[];rhs=[]
 for r in p.to_dict('records'):
  if r['to']==A:
   if r['from']==source:F+=int(r['amount_raw'])/1e6
  else:
   k+=1;row=np.zeros(N);row[:k]=1;lhs.extend([row,-row]);rhs.extend([F,int(r['balance_after_raw'])/1e6-F])
 mat=np.array(lhs);rhs=np.array(rhs);joint=[]
 for sign in [1,-1]:
  f=linprog(sign*np.ones(N),A_ub=mat,b_ub=rhs,bounds=bounds,method='highs');assert f.success,f.message;joint.append(sign*f.fun)
 groups.append({'source':source,'total_inflow_usdc':sum(int(r['amount_raw'])/1e6 for r in p.to_dict('records') if r['to']==A and r['from']==source),'joint_lower_usdc':joint[0],'joint_upper_usdc':joint[1]})
 for i,r in enumerate(withdraw.to_dict('records')):
  ends=[]
  for sign in [1,-1]:
   c=np.zeros(N);c[i]=sign;f=linprog(c,A_ub=mat,b_ub=rhs,bounds=bounds,method='highs');assert f.success;ends.append(sign*f.fun)
  answers.append({'tx':r['tx'],'source':source,'deposit_usdc':int(r['amount_raw'])/1e6,'lower_usdc':ends[0],'upper_usdc':ends[1]})
pd.DataFrame(answers).to_csv(O/'ethena_source_attribution.csv',index=False);pd.DataFrame(groups).to_csv(O/'ethena_source_totals.csv',index=False);summary={'start_block':lo,'end_block':hi,'opening_balance_raw':str(balances[lo-1]),'ending_balance_raw':str(balances[hi]),'incoming_transfers':int(p.to.eq(A).sum()),'deposits':N,'source_totals':groups,'scope':'Observed immediate Base wallet transfers, not fiat funding or upstream cross-chain provenance. Windows cover account ledger continuously; LP source bounds do not impose FIFO.'};(O/'ethena_funding_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
