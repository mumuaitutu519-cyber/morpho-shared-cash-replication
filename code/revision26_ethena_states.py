"""Validate every positive >=1 USDC incumbent state for independently named wallet."""
from pathlib import Path
import pandas as pd,requests,json,hashlib,datetime,time
from concurrent.futures import ThreadPoolExecutor
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';p=pd.read_parquet(O/'owner_day_panel.parquet');p=p[p.owner.eq(A)&p.risk_set_incumbent];s=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date')
def job(x):
 day=(pd.Timestamp(x.date)-pd.Timedelta(days=1)).strftime('%Y-%m-%d');b=int(s.loc[day,'block']);calls=[selector('balanceOf(address)')+A[2:].zfill(64),selector('maxWithdraw(address)')+A[2:].zfill(64)];body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(b)]};f=O/'raw'/('ethena_state_'+day+'.json')
 if f.exists() and 'result' not in json.loads(f.read_text())['response']:
  backup=f.with_suffix('.rate_limit.json');f.rename(backup)
 if f.exists():ob=json.loads(f.read_text())
 else:
  time.sleep(1.2)
  r=requests.post('https://base.drpc.org',json=body,timeout=45);ob={'request':body,'response':r.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest()};f.write_text(json.dumps(ob,indent=2))
 assert 'result' in ob['response'],ob;sh,w=[int(z,16) for z in decode_bytes_array(ob['response']['result'],2)];claim=sh*int(s.loc[day,'total_assets_micro'])/int(s.loc[day,'total_shares'])/1e6;return {'date':str(x.date),'state_date':day,'block':b,'rpc_shares_raw':str(sh),'rpc_capacity_usdc':w/1e6,'claim_usdc':claim,'rpc_coverage':w/1e6/claim,'event_opening_shares':x.opening_shares,'share_gap_units':sh/1e18-x.opening_shares,'cash_benchmark_coverage':x.prior_cash_coverage}
with ThreadPoolExecutor(max_workers=1) as ex:rows=list(ex.map(job,p.itertuples()))
f=pd.DataFrame(rows);f.to_csv(O/'ethena_daily_state_validation.csv',index=False);print({'states':len(f),'max_share_gap':f.share_gap_units.abs().max(),'min_rpc_coverage':f.rpc_coverage.min(),'below_full':f.rpc_coverage.lt(1-1e-8).sum(),'below_quarter':f.rpc_coverage.lt(.25).sum()})
