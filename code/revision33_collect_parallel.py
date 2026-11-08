from pathlib import Path
import pandas as pd,numpy as np,json,requests,time,datetime,hashlib
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision33';RAW=O/'raw';RAW.mkdir(exist_ok=True);V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';S='0x2917956eff0b5eaf030abdb4ef4296df775009ca';E='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';URL='https://base.drpc.org'
a=pd.read_csv(R/'reports/revision24/deposit_timing_classification.csv',dtype=str).sort_values(['block','log_index'],key=lambda x:x.astype(int));v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v['date']=pd.to_datetime(v.date).dt.strftime('%Y-%m-%d');plans=[]
for tx,g in a.groupby('tx',sort=False):
 x=g.iloc[0];owners=list(dict.fromkeys([S,E]+v[(v.date==x.date)&~v.spark].nlargest(5,'prior_claim_usdc').owner.tolist()))
 plans.append({'tx':tx,'block':int(x.block),'timestamp':int(x.timestamp),'date':x.date,'deposit_count':len(g),'deposit_micro':str(sum(map(int,g.deposit_micro))),'owners':owners})
(O/'collection_plan.json').write_text(json.dumps(plans,indent=2));assert len(plans)==93
import threading
from concurrent.futures import ThreadPoolExecutor
counter=0
rate_lock=threading.Lock(); key_lock_guard=threading.Lock(); key_locks={}; next_start=0.0
cached_requests={}
for f in (R/'reports/revision29/raw').glob('*.json'):
 if f.name.startswith('._'):continue
 obj=json.loads(f.read_text())
 if 'request' in obj and 'result' in obj.get('response',{}):cached_requests[json.dumps(obj['request'],sort_keys=True)]=obj


def query(key,method,params):
 global counter
 req={'jsonrpc':'2.0','id':1,'method':method,'params':params};p=RAW/(key+'.json')
 if p.exists():
  obj=json.loads(p.read_text());assert obj['request']==req
  if 'result' in obj['response']:return obj['response']['result']
 old=cached_requests.get(json.dumps(req,sort_keys=True))
 if old is not None:p.write_text(json.dumps(old,indent=2));return old['response']['result']
 if method=='eth_getBlockByNumber':
  prior=R/'data/raw/revision24'/f'drpc_header_{int(params[0],16)}.body'
  if prior.exists():
   old=json.loads(prior.read_text())
   if old.get('result') is not None:p.write_text(json.dumps({'request':req,'response':old,'reused_from':str(prior)},indent=2));return old['result']
 if (O/'ACCESS_STOP.json').exists():raise RuntimeError('RPC access stopped; retained partial results remain valid')
 for attempt in range(3):
  with rate_lock:
   global next_start
   time.sleep(max(0,next_start-time.monotonic()));next_start=time.monotonic()+1.1
  if attempt:time.sleep(3*attempt)
  try:
   rr=requests.post(URL,json=req,timeout=40);resp=rr.json();obj={'request':req,'response':resp,'http_status':rr.status_code,'url':URL,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p.write_text(json.dumps(obj,indent=2));counter+=1
   if rr.status_code in [401,403,429] or any(s in json.dumps(resp).lower() for s in ['rate limit','api key required','unauthorized','access denied']):
    (O/'ACCESS_STOP.json').write_text(json.dumps(obj,indent=2));raise RuntimeError('Access restriction')
   if 'result' in resp and resp['result'] is not None:return resp['result']
  except requests.RequestException as err:
   p.with_suffix(f'.attempt{attempt}.json').write_text(json.dumps({'request':req,'transport_error':str(err)}))
  if attempt<2 and p.exists():p.rename(p.with_suffix(f'.attempt{attempt}.json'))
 raise RuntimeError(f'Unresolved RPC {key}')
def views(block,owners):
 calls=[]
 for owner in owners:calls.extend([selector('balanceOf(address)')+owner[2:].zfill(64),selector('maxWithdraw(address)')+owner[2:].zfill(64)])
 key=f'{block}_'+hashlib.sha256('|'.join(owners).encode()).hexdigest()[:12]
 vals=[int(x,16) for x in decode_bytes_array(query(key+'_views','eth_call',[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(block)]),len(calls))];shares=vals[::2];caps=vals[1::2]
 calls=[selector('convertToAssets(uint256)')+f'{s:064x}' for s in shares];claims=[int(x,16) for x in decode_bytes_array(query(key+'_claims','eth_call',[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(block)]),len(calls))]
 return shares,caps,claims

raw_query=query
def query(key,method,params):
 with key_lock_guard:lock=key_locks.setdefault(key,threading.Lock())
 with lock:return raw_query(key,method,params)

def collect_one(arg):
 phase,offset,p=arg;b=p['block']+offset
 head=query(f'header_{b}','eth_getBlockByNumber',[hex(b),False]);stamp=int(head['timestamp'],16);assert stamp==p['timestamp']+2*offset,(b,stamp,p['timestamp'],offset)
 sh,caps,cl=views(b,p['owners']);res=[]
 for owner,ss,cc,qq in zip(p['owners'],sh,caps,cl):res.append({'tx':p['tx'],'deposit_block':p['block'],'date':p['date'],'deposit_timestamp':p['timestamp'],'deposit_count':p['deposit_count'],'deposit_micro':p['deposit_micro'],'owner':owner,'identity':'Spark' if owner==S else 'Ethena' if owner==E else 'unnamed prior-top-five','phase':phase,'state_block':b,'state_timestamp':stamp,'state_hash':head['hash'],'shares_raw':str(ss),'claim_micro':str(qq),'capacity_micro':str(cc)})
 return res
rows=[]
for phase,offset in [('before',-1),('after',0),('one_hour',1800),('six_hours',10800),('one_day',43200)]:
 with ThreadPoolExecutor(max_workers=3) as pool:
  for i,res in enumerate(pool.map(collect_one,[(phase,offset,p) for p in plans])):
   rows.extend(res);pd.DataFrame(rows).to_csv(O/'holder_states.csv',index=False)
   (O/'progress.json').write_text(json.dumps({'phase':phase,'phase_transactions_completed':i+1,'planned_transactions':93,'owner_states':len(rows),'new_RPC_calls':counter,'read_only':True,'max_concurrent_requests':3,'minimum_request_start_interval_seconds':1.1},indent=2))
   if (i+1)%10==0:print(phase,i+1,'states',len(rows),flush=True)
print('COMPLETE',len(rows),flush=True)
