"""Deposit-equivalent read-only withdrawal tests for the second named account."""
from pathlib import Path
import pandas as pd,requests,json,hashlib,time
from concurrent.futures import ThreadPoolExecutor
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';p=pd.read_csv(R/'reports/revision26/second_account_events.csv',dtype=str);p=p[p.type.eq('Deposit')].copy();p=p.merge(pd.read_csv(O/'ethena_usdc_ledger.csv')[['tx','block']],on='tx',validate='one_to_one')
def rpc(key,params):
 f=O/'raw'/('ethena_exit_'+key+'.json');q={'jsonrpc':'2.0','id':1,'method':'eth_call','params':params}
 if f.exists() and 'result' not in json.loads(f.read_text())['response'] and 'revert' not in json.dumps(json.loads(f.read_text())['response']).lower():
  f.rename(f.with_suffix('.error-'+str(time.time_ns())+'.json'))
 if f.exists():ob=json.loads(f.read_text())
 else:
  time.sleep(1.35)
  r=requests.post('https://base.drpc.org',json=q,timeout=35);ob={'url':'https://base.drpc.org','request':q,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest()};f.write_text(json.dumps(ob,indent=2))
 return ob['response']
def job(x):
 a=A[2:].zfill(64);amount=int(x.assets_raw);b=int(x.block);calls=[selector('balanceOf(address)')+a,selector('maxWithdraw(address)')+a];st=rpc(x.tx+'_views',[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(b)]);assert 'result' in st,st;sh,w=[int(z,16) for z in decode_bytes_array(st['result'],2)];cl=rpc(x.tx+'_claim',[{'to':V,'data':selector('convertToAssets(uint256)')+f'{sh:064x}'},hex(b)]);assert 'result' in cl;claim=int(cl['result'],16);exe=rpc(x.tx+'_withdraw',[{'from':A,'to':V,'gas':'0x989680','data':selector('withdraw(uint256,address,address)')+f'{amount:064x}'+a+a},hex(b)]);
 if 'result' in exe:assert len(exe['result'])==66
 status='success' if 'result' in exe else 'contract_revert' if 'revert' in json.dumps(exe).lower() else 'provider_error'
 return {'date':x.date,'tx':x.tx,'block':b,'deposit_raw':str(amount),'owner_shares_raw':str(sh),'claim_raw':str(claim),'capacity_raw':str(w),'coverage':w/claim,'capacity_to_deposit':w/amount,'execution_status':status,'execution_success':True if status=='success' else False if status=='contract_revert' else None,'execution_response':json.dumps(exe)}
with ThreadPoolExecutor(max_workers=1) as e:rows=list(e.map(job,p.itertuples()))
f=pd.DataFrame(rows);f.to_csv(O/'ethena_deposit_exit_tests.csv',index=False);print(f[['date','deposit_raw','capacity_to_deposit','coverage','execution_success']].to_string(index=False))
