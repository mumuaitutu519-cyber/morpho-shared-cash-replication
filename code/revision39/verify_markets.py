from pathlib import Path
import pandas as pd,json,requests,concurrent.futures,sys,datetime
sys.path.insert(0,str(Path('code').resolve()));from revision24_rpc import selector
O=Path('reports/revision39_pilot');b=pd.read_csv('reports/revision6/withdrawal_capacity.csv').set_index('date');r=pd.read_parquet(O/'shared_positions.parquet');jobs=r[r.date.isin(['2025-01-16','2025-06-30','2025-11-30'])][['date','market','cash_raw']].drop_duplicates().to_dict('records');M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb'
def job(v):
 day=v['date'];block=int(b.loc[day,'block']);body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':M,'data':selector('market(bytes32)')+v['market'][2:]},hex(block)]};p=O/'raw'/('rpc_market_'+v['market']+'_'+day+'.json')
 try:
  if p.exists():a=json.loads(p.read_text())
  else:
   response=requests.post('https://base.drpc.org',json=body,timeout=35).json();a={'request':body,'response':response,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p.write_text(json.dumps(a))
  res=a['response'];raw=res.get('result');vals=[int(raw[i:i+64],16) for i in range(2,len(raw),64)] if raw else [];cash=vals[0]-vals[2] if len(vals)==6 else None
  return {**v,'block':block,'rpc_cash_raw':cash,'gap_usdc':(cash-v['cash_raw'])/1e6 if cash is not None else None,'error':str(res.get('error',''))}
 except Exception as e:return {**v,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:rows=list(ex.map(job,jobs))
f=pd.DataFrame(rows);f.to_csv(O/'direct_market_cash_checks.csv',index=False);print('checks',len(f),'success',f.rpc_cash_raw.notna().sum(),'maxgap',f.gap_usdc.abs().max());print(f[f.gap_usdc.abs().gt(.000001)|f.rpc_cash_raw.isna()].to_string(index=False))
