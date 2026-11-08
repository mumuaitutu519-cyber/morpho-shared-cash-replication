"""Paced RPC reads with durable success/failure provenance, from archived config."""
from pathlib import Path
import ast, json, time, hashlib, urllib.request, urllib.error,threading
A=Path(__file__).resolve().parents[1];R=Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/Replication_Package')
C=A/'out/rpc';C.mkdir(exist_ok=True)
tree=ast.parse((R/'additional_evidence/code/chain_access.py').read_text())
URLS=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='URLS' for t in n.targets))
denied=set()
pace_lock=threading.Lock();next_request={};last_slow={};rates={u:(6. if c==8453 else 3.) for c,urls in URLS.items() for u in urls}
def pace(url,units=1):
    while True:
        with pace_lock:
            now=time.monotonic();wait=next_request.get(url,now)-now
            if wait<=0:next_request[url]=now+units/rates[url];return
        time.sleep(min(5,wait))
def slow(url):
    with pace_lock:
        now=time.monotonic()
        if now-last_slow.get(url,0)>30:rates[url]=max(.25,rates[url]/2);last_slow[url]=now
        next_request[url]=max(now+15,next_request.get(url,0))
        (A/'out/active_rpc_rates.json').write_text(json.dumps(rates,indent=2))
for f in C.glob('*.errors.json'):
    z=json.loads(f.read_text())
    if isinstance(z,dict):
        for err in z.get('attempts',[]):
            if 'HTTP Error 403' in err['error']:denied.add((err['url'],z['request']['method']))
def rpc(chain,method,params,attempts=3):
    req={'jsonrpc':'2.0','id':1,'method':method,'params':params}
    key=hashlib.sha256(json.dumps([chain,req],sort_keys=True).encode()).hexdigest()
    path=C/(key+'.json')
    if path.exists():return json.loads(path.read_text())['response']['result']
    errorfile=C/(key+'.errors.json')
    errs=json.loads(errorfile.read_text()).get('attempts',[]) if errorfile.exists() else []
    for url in URLS[chain]:
        if (url,method) in denied:continue
        for attempt in range(attempts):
            time.sleep(min(8,1.0*2**attempt))
            try:
                q=urllib.request.Request(url,json.dumps(req).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'})
                pace(url)
                with urllib.request.urlopen(q,timeout=15) as response:z=json.load(response)
                if z.get('result') is None:raise ValueError(str(z))
                path.write_text(json.dumps({'url':url,'chain':chain,'request':req,'response':z}))
                return z['result']
            except Exception as ex:
                errs.append({'url':url,'attempt':len(errs)+1,'error':str(ex),'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())})
                errorfile.write_text(json.dumps({'chain':chain,'request':req,'attempts':errs},indent=2))
                if isinstance(ex,urllib.error.HTTPError) and ex.code==403:
                    denied.add((url,method));break
                if isinstance(ex,urllib.error.HTTPError) and ex.code==429:slow(url);time.sleep(15*2**attempt)
    raise RuntimeError(f'{chain} {method}: {len(errs)} failed attempts; see {key}.errors.json')

def probe():
    # Historical blocks and Morpho address are read from the frozen states.
    source=ast.parse((R/'code/empirical/collect_chain.py').read_text())
    morpho=next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='M' for t in n.targets))
    jobs=[(8453,R/'raw/chain_panel/2025-10-09_decoded.json'),(1,R/'additional_evidence/cross_chain/raw/morpho_1_2025-10-31.json'),(42161,R/'additional_evidence/raw/morpho_42161_2025-10-31.json')]
    rows=[]
    for chain,path in jobs:
        z=json.loads(path.read_text());block=z['block'];v=z['vaults'][0]['address']
        for method,params in [('eth_getBlockByNumber',[hex(block),False]),('eth_call',[{'to':v,'data':'0x01e1d114'},hex(block)])]:
            try:
                result=rpc(chain,method,params);status='PASS'
            except Exception as ex:status=str(ex)
            rows.append({'chain':chain,'block':block,'method':method,'status':status})
            print(rows[-1],flush=True)
    (A/'out/rpc_probe.json').write_text(json.dumps(rows,indent=2))

def multi(chain,queries):
    """JSON-RPC batch reads; every item retains its own immutable response."""
    result=[None]*len(queries);pending=[]
    for i,(method,params) in enumerate(queries):
        req={'jsonrpc':'2.0','id':1,'method':method,'params':params}
        key=hashlib.sha256(json.dumps([chain,req],sort_keys=True).encode()).hexdigest();p=C/(key+'.json')
        if p.exists():result[i]=json.loads(p.read_text())['response']['result']
        else:pending.append((i,method,params,p))
    size=3
    for offset in range(0,len(pending),size):
        chunk=pending[offset:offset+size];qs=[{'jsonrpc':'2.0','id':i+1,'method':m,'params':p} for i,m,p,_ in chunk];done=False
        for url in URLS[chain]:
            if all((url,m) in denied for _,m,_,_ in chunk):continue
            for attempt in range(3):
                time.sleep(.25*2**attempt)
                try:
                    req=urllib.request.Request(url,json.dumps(qs).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'})
                    pace(url,len(qs))
                    with urllib.request.urlopen(req,timeout=45) as f:zs=json.load(f)
                    assert isinstance(zs,list),str(zs)[:300]
                    answer={x['id']:x for x in zs}
                    assert all(answer.get(i+1,{}).get('result') is not None for i,_,_,_ in chunk),str(zs)[:500]
                    for i,m,p,path in chunk:
                        z=answer[i+1];result[i]=z['result'];path.write_text(json.dumps({'chain':chain,'url':url,'request':{'jsonrpc':'2.0','id':i+1,'method':m,'params':p},'cache_canonical_id':1,'response':z}))
                    done=True;break
                except Exception as e:
                    key=hashlib.sha256(json.dumps(qs,sort_keys=True).encode()).hexdigest();err=C/(key+'.batch.errors.json')
                    old=json.loads(err.read_text()) if err.exists() else []
                    old.append({'chain':chain,'url':url,'attempt':attempt+1,'error':str(e),'queries':len(qs)});err.write_text(json.dumps(old,indent=2))
                    if isinstance(e,urllib.error.HTTPError) and e.code==403:
                        denied.update((url,m) for _,m,_,_ in chunk);break
                    if isinstance(e,urllib.error.HTTPError) and e.code==429:slow(url);time.sleep(15*2**attempt)
            if done:break
        if not done:
            for i,m,p,path in chunk:result[i]=rpc(chain,m,p)
    return result

if __name__=='__main__':probe()
