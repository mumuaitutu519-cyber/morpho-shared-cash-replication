"""Public Base RPC fee and treasury mint census, bounded and resumable."""
from pathlib import Path
import requests,json,hashlib,datetime,time,pandas as pd
from concurrent.futures import ThreadPoolExecutor
from revision22_audit_fees import FEE,TRANSFER,VAULT,PROXY
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';s=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv');lo=int(s.block.iloc[0])+1;hi=int(s.block.iloc[-1]);targets=pd.read_csv(R/'reports/revision22/fee_residual_daily_audit.csv',dtype=str);targets=targets[targets.original_residual_raw.map(int).ne(0)];state=s.set_index('date');jobs=[]
for day in targets.date:
 first=int(state.loc[(pd.Timestamp(day)-pd.Timedelta(days=1)).strftime('%Y-%m-%d'),'block'])+1;last=int(state.loc[day,'block']);jobs.extend((l,min(l+9999,last),'all') for l in range(first,last+1,10000))
def job(x):
 l,h,typ=x;topics=[[FEE,TRANSFER]];q={'jsonrpc':'2.0','id':1,'method':'eth_getLogs','params':[{'address':VAULT,'fromBlock':hex(l),'toBlock':hex(h),'topics':topics}]};p=O/'raw'/f'fee_census_{l}_{h}_{typ}.json'
 if p.exists() and not isinstance(json.loads(p.read_text())['response'].get('result'),list):
  p.rename(p.with_suffix('.error-'+str(time.time_ns())+'.json'))
 if p.exists():ob=json.loads(p.read_text())
 else:
  for attempt in range(4):
   time.sleep(1.1 if attempt==0 else 5*attempt)
   r=requests.post('https://mainnet.base.org',json=q,timeout=50);ob={'url':'https://mainnet.base.org','request':q,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p.write_text(json.dumps(ob,indent=2))
   if isinstance(ob['response'].get('result'),list):break
   if attempt<3:p.rename(p.with_suffix('.error-'+str(time.time_ns())+'.json'))
 assert isinstance(ob['response'].get('result'),list),ob['response'];return {'from':l,'through':h,'type':typ,'logs':len(ob['response']['result']),'file':str(p.relative_to(R))}
coverage=[]
with ThreadPoolExecutor(max_workers=1) as e:
 for item in e.map(job,jobs):
  coverage.append(item)
  if len(coverage)%20==0: print('completed',len(coverage),'/',len(jobs),'through',item['through'],flush=True)
(O/'fee_census_coverage.json').write_text(json.dumps(coverage,indent=2));print('complete',sum(x['logs'] for x in coverage))
