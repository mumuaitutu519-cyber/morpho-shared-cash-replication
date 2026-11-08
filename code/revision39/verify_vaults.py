from pathlib import Path
import pandas as pd,json,requests,concurrent.futures,sys,datetime
sys.path.insert(0,str(Path('code').resolve()));from revision24_rpc import selector
O=Path('reports/revision39_pilot');vs=json.loads((O/'selected_vaults.json').read_text());b=pd.read_csv('reports/revision6/withdrawal_capacity.csv').set_index('date');c=pd.read_csv(O/'shared_reconciliation.csv');jobs=[(v,day) for v in vs for day in ['2025-01-16','2025-06-30','2025-11-30']]
def job(arg):
 v,day=arg;block=int(b.loc[day,'block']);body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':v['address'],'data':selector('totalAssets()')},hex(block)]};p=O/'raw'/('rpc_assets_'+v['address'].lower()+'_'+day+'.json')
 try:
  if p.exists():a=json.loads(p.read_text())
  else:
   r=requests.post('https://base.drpc.org',json=body,timeout=30);a={'request':body,'response':r.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p.write_text(json.dumps(a))
  res=a['response'];actual=int(res['result'],16) if 'result' in res else None;stamp=int((pd.Timestamp(day,tz='UTC')+pd.Timedelta(days=1)).timestamp());api=int(c[(c.vault.eq(v['address'].lower()))&c.timestamp.eq(stamp)].assets_raw.iloc[0]);return {'name':v['name'],'vault':v['address'],'date':day,'block':block,'api_usdc':api/1e6,'rpc_usdc':actual/1e6 if actual is not None else None,'gap_usdc':(actual-api)/1e6 if actual is not None else None,'error':str(res.get('error',''))}
 except Exception as e:return {'name':v['name'],'date':day,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:r=list(ex.map(job,jobs))
f=pd.DataFrame(r);f.to_csv(O/'direct_vault_asset_checks.csv',index=False);print(f.to_string(index=False));print('completed',f.rpc_usdc.notna().sum(),'maxgap',f.gap_usdc.abs().max())
