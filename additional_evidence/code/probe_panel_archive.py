from pathlib import Path
import json,urllib.request,time,concurrent.futures
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';RAW=P/'raw/event_states'
f=next(f for f in sorted(RAW.glob('*_vaults.json')) if not f.name.startswith('._'));q=json.loads(f.read_text())['request']
urls=['https://rpc.baseazul.dev','https://base.gateway.tenderly.co','https://mainnet.base.org','https://developer-access-mainnet.base.org','https://xrpc.cl/base','https://base.drpc.org','https://base-public.nodies.app','https://base-mainnet.public.blastapi.io']
def run(url):
 start=time.monotonic()
 try:
  r=json.load(urllib.request.urlopen(urllib.request.Request(url,json.dumps([q]).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'}),timeout=10));z=r[0] if isinstance(r,list) else r;return {'url':url,'seconds':time.monotonic()-start,'success':len(z.get('result',''))>2,'response':z}
 except Exception as e:return {'url':url,'seconds':time.monotonic()-start,'success':False,'error':str(e)}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(run,urls))
(P/'raw/archive_multicall_probes.json').write_text(json.dumps({'request':q,'results':results},indent=2))
for r in results:print(r['url'],r['seconds'],r['success'],r.get('error',str(r.get('response',{}).get('error',''))),flush=True)
