from audit_history import *
R2=ROOT/'raw/history_audit_tenderly';R2.mkdir(exist_ok=True)
failed=[json.loads(p.read_text()) for p in R.glob('2025*.json') if not json.loads(p.read_text())['decoded']]
def fallback(a):
 dest=R2/(a['date']+'.json')
 if dest.exists():return
 out={k:a[k] for k in ('date','timestamp','block','calls')};out['attempts']=[];out['decoded']=None
 for n in (1,2):
  x={'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'url':'https://base.gateway.tenderly.co','request':a['attempts'][0]['request'],'attempt':n}
  try:
   rr=requests.post(x['url'],json=x['request'],timeout=50);x.update(status=rr.status_code,body=rr.text);d=rr.json();x['response']=d
   if rr.status_code!=200 or 'result' not in d:raise ValueError(str(d.get('error',rr.status_code)))
   ans=decode(d['result']);assert len(ans)==len(a['calls']);out['decoded']=ans
  except Exception as e:x['error']=str(e)
  out['attempts'].append(x)
  if out['decoded'] is not None:break
  time.sleep(2)
 dest.write_text(json.dumps(out));time.sleep(.7)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(fallback,failed))
print('fallback completed',len(failed))
