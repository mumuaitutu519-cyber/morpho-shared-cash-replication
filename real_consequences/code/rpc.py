from pathlib import Path
import rpc_limiter
import json,urllib.request,urllib.error,time,sys,hashlib,gzip
E=Path(__file__).resolve().parents[1]
URL='https://base.gateway.tenderly.co'
def selector(s):return json.loads((E/'code/function_selectors.json').read_text())[s]
def word(x):return f'{int(x,16) if isinstance(x,str) else int(x):064x}'
def request(method,params,key=None):
 q={'jsonrpc':'2.0','id':1,'method':method,'params':params};k=key or hashlib.sha256(json.dumps(q,sort_keys=True).encode()).hexdigest();p=E/'raw/rpc'/(k+'.json.gz');p.parent.mkdir(exist_ok=True)
 if p.exists():
  cached=json.load(gzip.open(p,'rt'))['response']
  if 'result' in cached and cached['result'] is not None:return cached
 for i in range(5):
  try:
   rpc_limiter.wait(URL,1)
   req=urllib.request.Request(URL,json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'});r=json.load(urllib.request.urlopen(req,timeout=40))
   if 'error' in r and any(x in str(r['error']).lower() for x in ['rate limit','timeout','too many']):raise RuntimeError(r['error'])
   with gzip.open(p,'wt') as f:json.dump({'url':URL,'request':q,'response':r},f)
   return r
  except Exception:
   if i==4:raise
   time.sleep(2**i)
def call(to,data,block):return request('eth_call',[{'to':to,'data':data},hex(block)])
if __name__=='__main__':
 v='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';owner='0xbf3d76bf465a68283ea2755148e2e4155b1643cb';b=27525795
 for sig,args in [('maxWithdraw(address)',word(owner)),('totalAssets()',''),('withdrawQueueLength()','')]:
  print(sig,call(v,selector(sig)+args,b),flush=True)
