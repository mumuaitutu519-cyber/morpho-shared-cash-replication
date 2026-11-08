from pathlib import Path
import pandas as pd,numpy as np,json,requests,math,hashlib
from concurrent.futures import ThreadPoolExecutor
from revision24_rpc import selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';states=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date');jobs=[]
for name in ['moonwell','gauntlet']:
 h=next(iter(json.loads((O/'raw'/f'{name}_native_inputs.json').read_text())['response']['data'].values()))['historicalState']
 for day in ['2025-02-19','2025-06-21','2025-11-30']:
  ts=int((pd.Timestamp(day)+pd.Timedelta(days=1)).timestamp());values=[(next((int(z['y']) for z in x['supplyAssets'] if z['x']==ts and z['y'] is not None),0),x) for x in h['allocation']];amt,x=max(values,key=lambda z:z[0]);market=x['market'];api=next(float(z['y']) for z in market['historicalState']['supplyApy'] if z['x']==ts);jobs.append({'peer':name,'date':day,'market':market['marketId'],'amount':amt,'api':api})
def rpc(key,to,data,b):
 p=O/'raw'/('peer_rate_'+key+'.json');q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':data},hex(b)]}
 if p.exists():ob=json.loads(p.read_text())
 else:
  r=requests.post('https://base.drpc.org',json=q,timeout=45);ob={'request':q,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2))
 assert 'result' in ob['response'],ob;return ob['response']['result']
def job(x):
 b=int(states.loc[x['date'],'block']);key=x['peer']+'_'+x['date'];pa=rpc(key+'_params',M,selector('idToMarketParams(bytes32)')+x['market'][2:],b);st=rpc(key+'_state',M,selector('market(bytes32)')+x['market'][2:],b);words=[pa[i:i+64] for i in range(2,len(pa),64)];irm='0x'+words[3][-40:];rate=(0 if int(irm,16)==0 else int(rpc(key+'_irm',irm,selector('borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))')+pa[2:]+st[2:],b),16)/1e18);nums=[int(st[i:i+64],16) for i in range(2,len(st),64)];apy=math.expm1(rate*31536000*nums[2]/nums[0]*(1-nums[5]/1e18));return {**x,'rpc_supply_apy':apy,'difference':apy-x['api']}
with ThreadPoolExecutor(max_workers=3) as ex:out=list(ex.map(job,jobs))
pd.DataFrame(out).to_csv(O/'peer_native_rate_validation.csv',index=False);print(pd.DataFrame(out).to_string(index=False))
