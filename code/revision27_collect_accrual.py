"""Read pending fee state to reconstruct exact ERC4626 asset conversions."""
from pathlib import Path
import json,requests,hashlib,time,pandas as pd
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';s=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date');fees=pd.read_csv(R/'reports/revision26/native_yields.csv').set_index('date');rows=[]
for day,r in s.iterrows():
 fee_api=fees.loc[day,'spark_fee'];b=int(r.block)
 if fee_api==0:fee=0;last=None;huge=None
 else:
  p=O/'raw'/('accrual_'+day+'.json');calls=[selector('fee()'),selector('lastTotalAssets()'),selector('convertToAssets(uint256)')+f'{10**36:064x}'];q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':'0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a','data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(b)]}
  if p.exists():ob=json.loads(p.read_text())
  else:
   time.sleep(1.35);resp=requests.post('https://base.drpc.org',json=q,timeout=40);ob={'request':q,'response':resp.json(),'sha256':hashlib.sha256(resp.content).hexdigest()};p.write_text(json.dumps(ob,indent=2))
  assert 'result' in ob['response'],ob;fee,last,huge=[int(z,16) for z in decode_bytes_array(ob['response']['result'],3)];assert fee/1e18==fee_api
 assets=int(r.total_assets_micro);shares=int(r.total_shares);fa=max(assets-last,0)*fee//10**18 if last is not None else 0;fs=fa*(shares+10**12)//(assets-fa+1);den=shares+fs+10**12;num=assets+1
 if huge is not None:assert 10**36*num//den==huge,(day,'large-unit conversion mismatch')
 spark=int(r.treasury_shares)*num//den;assert spark==int(r.claim_micro),(day,'Spark direct claim mismatch',spark,r.claim_micro)
 rows.append({'date':day,'block':b,'assets_numerator':str(num),'shares_denominator':str(den),'fee_raw':str(fee),'pending_fee_shares_raw':str(fs),'last_total_assets_raw':str(last) if last is not None else '', 'conversion_probe_raw':str(huge) if huge is not None else ''})
 if len(rows)%20==0:print('states',len(rows),flush=True)
pd.DataFrame(rows).to_csv(O/'exact_conversion_states.csv',index=False);print('all320 Spark direct claims exact')
