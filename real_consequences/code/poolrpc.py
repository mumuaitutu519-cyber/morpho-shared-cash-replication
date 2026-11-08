"""Paced independent public archive providers; response-level source and attempts."""
from pathlib import Path
import json,time,urllib.request,urllib.error,tempfile,hashlib,threading
import rpc_limiter
PROVIDERS=[('https://rpc.baseazul.dev',50,70.),('https://base.drpc.org',3,10.),('https://base.api.onfinality.io/public',1,.1),('https://base-public.nodies.app',3,10.),('https://base-mainnet.public.blastapi.io',3,10.),('https://base.gateway.tenderly.co',1,6.)]
rpc_limiter.RATES.update({u:r for u,b,r in PROVIDERS});lock=threading.Lock();turn=0
def next_time(url):
 p=Path(tempfile.gettempdir())/('jrf_rpc_pacing_'+hashlib.sha256(url.encode()).hexdigest()[:16]);cp=rpc_limiter.cooldown_path(url);values=[time.time()]
 for f in [p,cp]:
  try:values.append(float(f.read_text()))
  except (FileNotFoundError,ValueError):pass
 return max(values)
def choose(avoid):
 global turn
 with lock:
  offset=turn%len(PROVIDERS);turn+=1;ordered=PROVIDERS[offset:]+PROVIDERS[:offset];eligible=[x for x in ordered if x[0] not in avoid] or ordered
  return min(eligible,key=lambda x:next_time(x[0]))
def request_batch(queries):
 answers={};attempts={q['id']:[] for q in queries};pending=list(queries)
 while pending:
  avoid={a['url'] for a in attempts[pending[0]['id']]};url,limit,rate=choose(avoid);part=pending[:limit];rpc_limiter.wait(url,len(part));status=200
  try:
   req=urllib.request.Request(url,json.dumps(part).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'});response=json.load(urllib.request.urlopen(req,timeout=35))
   if isinstance(response,list):byid={r.get('id'):r for r in response}
   else:byid={q['id']:response for q in part}
  except urllib.error.HTTPError as ex:
   status=ex.code;body=ex.read().decode()[:4000]
   try:r=json.loads(body)
   except Exception:r={'error':{'message':body,'http_status':status}}
   if isinstance(r,list):byid={z.get('id'):z for z in r}
   else:byid={q['id']:r for q in part}
   if status==429:
    delay=ex.headers.get('Retry-After');rpc_limiter.backoff(url,body if not delay else '429 resets in '+delay+'s')
   elif status in [401,403] and 'rate limit' not in body.lower():rpc_limiter.backoff(url,'429 resets in 86400s')
  except Exception as ex:byid={q['id']:{'error':{'message':str(ex)}} for q in part}
  consumed=set()
  for q in part:
   i=q['id'];r=byid.get(i,{'error':{'message':'missing response id'}});attempts[i].append({'url':url,'response':r,'http_status':status})
   if 'error' in r and any(s in str(r).lower() for s in ['rate limit','too many','budget']):rpc_limiter.backoff(url,str(r))
   if ('result' in r and r['result'] is not None) or len(attempts[i])>=len(PROVIDERS):answers[i]={**r,'_source_url':url,'_attempts':attempts[i]};consumed.add(i)
  pending=[q for q in pending if q['id'] not in consumed]
  # Rotate failed calls behind unattempted ones; the next provider is independently selected.
  failed=[q for q in part if q['id'] not in consumed];failed_ids={q['id'] for q in failed};pending=[q for q in pending if q['id'] not in failed_ids]+failed
 return answers
