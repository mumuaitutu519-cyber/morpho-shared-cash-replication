"""Cross-check suspect APY series with historical IRM views; no outlier deletion."""
from pathlib import Path
import pandas as pd,requests,json,math,hashlib
from revision24_rpc import selector
from revision5_collect_liquidity import MARKET,MORPHO
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';M=next(x for x in json.loads((R/'reports/revision11/morpho_market_census.json').read_text()) if x['marketId']==MARKET)
params=''.join(a.lower().removeprefix('0x').zfill(64) for a in [M['loanAsset']['address'],M['collateralAsset']['address'],M['oracle']['address'],M['irmAddress']])+f"{int(M['lltv']):064x}"
states=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date');d=pd.read_csv(O/'daily_conditions.csv').set_index('date');out=[]
def rpc(name,to,data,block):
 p=O/'raw'/(name+'.json');body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':to,'data':data},hex(block)]}
 if p.exists():ob=json.loads(p.read_text());assert ob['request']==body
 else:
  r=requests.post('https://base.drpc.org',json=body,timeout=50);ob={'request':body,'response':r.json(),'status':r.status_code,'url':r.url,'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2));p.with_suffix('.body').write_bytes(r.content)
 assert 'result' in ob['response'],ob;return ob['response']['result']
for day in ['2025-02-19','2025-06-21','2025-11-30']:
 b=int(states.loc[day,'block']);raw=rpc('rate_state_'+day,MORPHO,selector('market(bytes32)')+MARKET[2:],b);nums=[int(raw[i:i+64],16) for i in range(2,len(raw),64)];assert len(nums)==6
 rate=int(rpc('rate_irm_'+day,M['irmAddress'],selector('borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))')+params+raw[2:],b),16)/1e18
 u=nums[2]/nums[0];annual=rate*31536000;borrow=math.expm1(annual);supply=math.expm1(annual*u*(1-nums[5]/1e18))
 out.append({'date':day,'borrow_rate_per_second':rate,'borrow_APR':annual,'borrow_APY':borrow,'supply_APY':supply,'stored_utilization':u,'api_borrow_APY':d.loc[day,'market_borrowApy'],'api_supply_APY':d.loc[day,'market_supplyApy'],'api_vault_APY':d.loc[day,'vault_apy']});print(out[-1],flush=True)
pd.DataFrame(out).to_csv(O/'rate_probe.csv',index=False)
