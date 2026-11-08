"""Read-only Blockscout logs for all 170 preselected residual dates.

Archive requests and responses. A 1,000-record response is split, never treated
as complete. Stop on access restrictions. Do not contact old stopped RPCs.
"""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,ssl,threading,time,urllib.parse,urllib.request
import pandas as pd
from Crypto.Hash import keccak
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw/revision22/fees';OUT=ROOT/'reports/revision22'
VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
BASE='https://base.blockscout.com/api'
LOCK=threading.Lock();LAST=[0.0];STOP=threading.Event()
def topic(sig):
 h=keccak.new(digest_bits=256);h.update(sig.encode());return '0x'+h.hexdigest()
TOPIC={s:topic(s) for s in ['AccrueInterest(uint256,uint256)','Transfer(address,address,uint256)','SetFeeRecipient(address)']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def query(label,lo,hi,filters):
 RAW.mkdir(parents=True,exist_ok=True)
 name=f'{label}_{lo}_{hi}';body=RAW/(name+'.body');meta=RAW/(name+'.json')
 params={'module':'logs','action':'getLogs','fromBlock':lo,'toBlock':hi,'address':VAULT,**filters}
 url=BASE+'?'+urllib.parse.urlencode(params)
 if body.exists() and meta.exists():
  m=json.loads(meta.read_text());assert m['url']==url and m['sha256']==sha(body)
  if m['status']!=200:
   if m['status'] in [None,500,502,503,504] and hi-lo>=100:
    mid=(lo+hi)//2
    left,lf=query(label,lo,mid,filters);right,rf=query(label,mid+1,hi,filters)
    return left+right,lf+rf
   raise RuntimeError(f'Archived error: {name}')
 else:
  if STOP.is_set():raise RuntimeError('Stopped after provider error')
  with LOCK:
   delay=max(0,.60-(time.monotonic()-LAST[0]))
   if delay:time.sleep(delay)
   LAST[0]=time.monotonic()
  req=urllib.request.Request(url,headers={'User-Agent':'stablecoin-measurement-research/1.0'})
  try:
   with urllib.request.urlopen(req,timeout=40,context=ssl.create_default_context()) as response:data=response.read();status=response.status
  except Exception as e:
   data=e.read() if hasattr(e,'read') else repr(e).encode();status=getattr(e,'code',None)
   if status not in [None,500,502,503,504]:STOP.set()
  body.write_bytes(data)
  m={'url':url,'status':status,'queried_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':sha(body)}
  meta.write_text(json.dumps(m,indent=2)+'\n')
  if status!=200:
   if status in [None,500,502,503,504] and hi-lo>=100:
    mid=(lo+hi)//2
    left,lf=query(label,lo,mid,filters);right,rf=query(label,mid+1,hi,filters)
    return left+right,lf+rf
   raise RuntimeError(f'HTTP {status}; stopped: {name}')
 obj=json.loads(body.read_text())
 if obj.get('message')=='No logs found':logs=[]
 elif obj.get('status')=='1' and isinstance(obj.get('result'),list):logs=obj['result']
 else:STOP.set();raise RuntimeError(str(obj)[:500])
 for e in logs:
  assert lo<=int(e['blockNumber'],16)<=hi and e['address'].lower()==VAULT
  for k,v in filters.items():
   if k in ['topic0','topic1','topic2','topic3']:assert e['topics'][int(k[-1])]==v
 file={'file':str(body.relative_to(ROOT)),'sha256':sha(body),'metadata':str(meta.relative_to(ROOT)),
       'from_block':lo,'to_block':hi,'logs':len(logs),'filters':filters}
 if len(logs)>=1000:
  if lo==hi:raise RuntimeError('One block reaches log cap; cannot certify complete')
  mid=(lo+hi)//2
  left,lf=query(label,lo,mid,filters);right,rf=query(label,mid+1,hi,filters)
  return left+right,lf+rf
 return logs,[file]
def main():
 states=pd.read_csv(ROOT/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date')
 flow=pd.read_csv(ROOT/'reports/revision21/daily_flow_stock_reconciliation.csv',dtype=str)
 dates=[x.date for x in flow.itertuples() if int(x.unexplained_share_change_raw)!=0];assert len(dates)==170
 jobs=[]
 for date in dates:
  previous=(pd.Timestamp(date)-pd.Timedelta(days=1)).strftime('%Y-%m-%d')
  lo=int(states.loc[previous,'block'])+1;hi=int(states.loc[date,'block'])
  jobs.append((date,'accrue',lo,hi,{'topic0':TOPIC['AccrueInterest(uint256,uint256)']}))
  jobs.append((date,'mint',lo,hi,{'topic0':TOPIC['Transfer(address,address,uint256)'],
       'topic1':'0x'+'0'*64,'topic2':'0x'+PROXY[2:].rjust(64,'0'),
       'topic0_1_opr':'and','topic0_2_opr':'and','topic1_2_opr':'and'}))
 def work(job):
  date,kind,lo,hi,filters=job;logs,files=query(kind,lo,hi,filters)
  return {'date':date,'kind':kind,'logs':len(logs),'files':files}
 items=[]
 try:
  changes,files=query('recipient',int(states.loc['2025-01-15','block'])+1,int(states.loc['2025-11-30','block']),{'topic0':TOPIC['SetFeeRecipient(address)']})
  recipient={'logs':len(changes),'files':files}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   futures=[pool.submit(work,j) for j in jobs]
   for future in concurrent.futures.as_completed(futures):
    items.append(future.result())
    if len(items)%20==0:print('Complete fee date-kind ranges',len(items),'/',len(jobs),flush=True)
 except Exception as e:
  (OUT/'fee_collection_error.json').write_text(json.dumps({'error':repr(e),'complete_ranges':len(items)},indent=2)+'\n')
  raise
 assert len(items)==340
 out={'status':'PASS','target_dates':dates,'complete_date_kind_ranges':len(items),'recipient_changes':recipient,
      'items':sorted(items,key=lambda x:(x['date'],x['kind'])),'source':'Blockscout Base indexed raw logs; capped ranges recursively split',
      'topic_signatures':TOPIC}
 (OUT/'fee_collection_manifest.json').write_text(json.dumps(out,indent=2)+'\n')
 print('Fee collection complete',len(items),flush=True)
if __name__=='__main__':main()
