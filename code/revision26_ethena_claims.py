from pathlib import Path
import pandas as pd,requests,json,time,hashlib
from revision24_rpc import selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';f=pd.read_csv(O/'ethena_daily_state_validation.csv',dtype={'rpc_shares_raw':str});rows=[]
for x in f.itertuples():
 p=O/'raw'/('ethena_claim_'+x.state_date+'.json');q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':'0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a','data':selector('convertToAssets(uint256)')+f'{int(x.rpc_shares_raw):064x}'},hex(x.block)]}
 if p.exists():ob=json.loads(p.read_text())
 else:
  time.sleep(1.2);r=requests.post('https://base.drpc.org',json=q,timeout=40);ob={'request':q,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2))
 assert 'result' in ob['response'],ob;claim=int(ob['response']['result'],16);rows.append({**x._asdict(),'rpc_claim_micro':str(claim),'exact_rpc_coverage':x.rpc_capacity_usdc*1e6/claim})
 if len(rows)%20==0:print('completed',len(rows),flush=True)
d=pd.DataFrame(rows);d.to_csv(O/'ethena_daily_exact_claims.csv',index=False);print({'states':len(d),'min_coverage':d.exact_rpc_coverage.min(),'below_quarter':d.exact_rpc_coverage.lt(.25).sum(),'below_full':d.exact_rpc_coverage.lt(1-1e-12).sum()})
