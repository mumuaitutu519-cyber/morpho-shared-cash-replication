"""Reuse the existing paced public archive pool, with immutable response-level provenance."""
from pathlib import Path
import sys,json,hashlib,datetime
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';sys.path.insert(0,str(R/'real_consequences/code'));import poolrpc
# Providers that passed this task's archived multicall probe; retain conservative pacing.
poolrpc.PROVIDERS=[('https://base.gateway.tenderly.co',1,6.),('https://base-mainnet.public.blastapi.io',3,10.),('https://mainnet.base.org',1,1.),('https://developer-access-mainnet.base.org',1,1.),('https://xrpc.cl/base',1,2.)]
poolrpc.rpc_limiter.RATES.update({u:r for u,b,r in poolrpc.PROVIDERS})
RAW=P/'raw/event_states';RPC=P/'raw/rpc_pool';RPC.mkdir(parents=True,exist_ok=True)
def query(file,method,params):
 if file.exists():
  x=json.loads(file.read_text())
  if 'result' in x.get('response',{}):return x['response']['result']
 q={'jsonrpc':'2.0','id':1,'method':method,'params':params};answer=poolrpc.request_batch([q])[1];packet={'request':q,'response':answer,'url':answer.get('_source_url'),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};file.write_text(json.dumps(packet))
 if 'result' not in answer or answer['result'] is None:raise RuntimeError(str(answer))
 return answer['result']
def named(name,method,params):return query(RAW/(name+'.json'),method,params)
def generic(chain,method,params):
 assert chain==8453
 key=hashlib.sha256(json.dumps([chain,method,params],sort_keys=True).encode()).hexdigest();return query(RPC/(key+'.json'),method,params)
