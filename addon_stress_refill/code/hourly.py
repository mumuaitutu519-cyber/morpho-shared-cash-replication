"""Exact hourly archive reads, frozen discovery cohorts, UTC closest-block selection."""
from pathlib import Path
import ast,json,concurrent.futures,hashlib
import numpy as np,pandas as pd
from Crypto.Hash import keccak
from rpc import A,R,rpc,multi
from preflight import state
H=A/'out/hourly_raw';H.mkdir(exist_ok=True)
source=ast.parse((R/'code/empirical/collect_chain.py').read_text())
def constant(name):return next(ast.literal_eval(n.value) for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets))
M=constant('M');MC=constant('MC')
other=ast.parse((R/'additional_evidence/code/collect_morpho.py').read_text())
CHAIN_CONFIG=next(ast.literal_eval(n.value) for n in other.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CONFIG' for t in n.targets))
def morpho(chain):return CHAIN_CONFIG[chain][0].lower() if chain in CHAIN_CONFIG else M
word=lambda x:f'{int(x):064x}'
def sel(s):return '0x'+keccak.new(data=s.encode(),digest_bits=256).hexdigest()[:8]
# Reuse only the pure ABI codecs, never the original collector's writes.
ns={'word':word,'sel':sel};code=ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in ['encode','decode']],type_ignores=[]);exec(compile(code,'frozen_codecs','exec'),ns)
encode=ns['encode'];decode=ns['decode']
def batches(chain,items):
    jobs=[];cuts=[]
    for block,calls in items:
        start=len(jobs)
        for i in range(0,len(calls),800):jobs.append(('eth_call',[{'to':MC,'data':encode(calls[i:i+800]),'gas':'0x1c9c380'},hex(block)]))
        cuts.append((start,len(jobs)))
    result=multi(chain,jobs);return [[a for raw in result[lo:hi] for a in decode(raw)] for lo,hi in cuts]

def targets():
    return list(pd.date_range('2025-10-02','2025-10-17T23:00:00',freq='h',tz='UTC'))+list(pd.date_range('2025-10-27','2025-11-21T23:00:00',freq='h',tz='UTC'))

def ref(chain):
    p=R/(f'additional_evidence/cross_chain/raw/morpho_{chain}_2025-10-31.json' if chain in [1,8453] else f'additional_evidence/raw/morpho_{chain}_2025-10-31.json')
    return json.loads(p.read_text())

def blocks(chain,ts):
    suffix='' if len(ts)==1008 else '_'+hashlib.sha256(str(ts).encode()).hexdigest()[:10]
    path=H/f'blocks_{chain}{suffix}.json'
    if path.exists():return json.loads(path.read_text())
    r=ref(chain);period={8453:2.,1:12.,42161:.25}[chain];earliest=int(ts[0].timestamp());latest=int(ts[-1].timestamp())
    left=max(1,r['block']+int((earliest-r['timestamp'])/period)-500000);right=r['block']+int((latest-r['timestamp'])/period)+500000
    bounds=multi(chain,[('eth_getBlockByNumber',[hex(b),False]) for b in [left,right]])
    lo=np.full(len(ts),left,np.int64);hi=np.full(len(ts),right,np.int64);lt=np.full(len(ts),int(bounds[0]['timestamp'],16),np.int64);ht=np.full(len(ts),int(bounds[1]['timestamp'],16),np.int64);target=np.array([int(t.timestamp()) for t in ts]);assert lt[0]<target.min() and ht[0]>target.max()
    headers={left:bounds[0],right:bounds[1]}
    for iteration in range(64):
        todo=np.where(hi-lo>1)[0]
        if len(todo)==0:break
        mid={i:int(max(lo[i]+1,min(hi[i]-1,lo[i]+int((hi[i]-lo[i])*(target[i]-lt[i])/(ht[i]-lt[i]))))) for i in todo}
        unique=sorted(set(mid.values()));new=multi(chain,[('eth_getBlockByNumber',[hex(b),False]) for b in unique]);headers.update(zip(unique,new))
        for i,b in mid.items():
            stamp=int(headers[b]['timestamp'],16)
            if stamp<target[i]:lo[i]=b;lt[i]=stamp
            else:hi[i]=b;ht[i]=stamp
        print('blocks',chain,iteration,len(todo),flush=True)
    assert (hi-lo==1).all()
    records=[]
    for i,t in enumerate(ts):
        b=int(lo[i] if target[i]-lt[i]<=ht[i]-target[i] else hi[i]);h=headers[b]
        records.append(dict(utc=t.isoformat(),target=int(target[i]),block=b,timestamp=int(h['timestamp'],16),hash=h['hash'],pre_boundary_block=int(lo[i]),next_boundary_block=int(hi[i]),distance_seconds=abs(int(h['timestamp'],16)-int(target[i]))))
    path.write_text(json.dumps(records));return records

def cohort(chain,timestamp):
    if chain==8453:return json.loads((R/'raw/inherited/selected_vaults.json').read_text())
    path=R/(f'additional_evidence/cross_chain/raw/discovery_{chain}.json' if chain==1 else 'additional_evidence/raw/morpho_discovery_42161.json')
    data=json.loads(path.read_text())['response']['data']['vaults'];assert data['pageInfo']['count']==data['pageInfo']['countTotal']
    asset='0x'+word(ref(chain)['market'][next(iter(ref(chain)['market']))]['params'][0])[-40:]
    return [x for x in data['items'] if x['asset']['address'].lower()==asset and x['creationTimestamp']<=timestamp]

def collect(chain,records):
    contract=morpho(chain)
    for offset in range(0,len(records),12):
        chunk=[r for r in records[offset:offset+12] if not (H/f"{chain}_{r['target']}.json").exists()]
        if not chunk:continue
        states=[];items=[];fns=['totalAssets()','withdrawQueueLength()','lostAssets()','lastTotalAssets()','MORPHO()','asset()']
        for r in chunk:
            vs=cohort(chain,r['timestamp']);asset=constant('ASSET') if chain==8453 else vs[0]['asset']['address'].lower()
            calls=[(v['address'],sel(f)) for v in vs for f in fns]+[(asset,sel('balanceOf(address)')+contract[2:].zfill(64))];items.append((r['block'],calls));states.append((r,vs,asset))
        answers=batches(chain,items);zs=[];qitems=[]
        for (r,vs,asset),answer in zip(states,answers):
            vaults=[];calls=[]
            for i,v in enumerate(vs):
                a=answer[i*6:i*6+6];assert all(a[j] for j in [0,1,3,4,5]);assert a[4][0]==int(contract,16) and a[5][0]==int(asset,16)
                vaults.append(dict(address=v['address'].lower(),name=v['name'],totalAssets=a[0][0],length=a[1][0],lostAssets=a[2][0] if a[2] else None,lastTotalAssets=a[3][0]));calls.extend((v['address'],sel('withdrawQueue(uint256)')+word(j)) for j in range(a[1][0]))
            z=dict(name=r['utc'],block=r['block'],block_hash=r['hash'],timestamp=r['timestamp'],chain=chain,target=r['target'],vaults=vaults,morpho_token_balance=answer[-1][0],asset=asset,positions={v['address']:{} for v in vaults});zs.append(z);qitems.append((r['block'],calls))
        queues=batches(chain,qitems);mitems=[];allkeys=[]
        for z,answer in zip(zs,queues):
            idx=0
            for v in z['vaults']:v['queue']=['0x'+word(x[0]) for x in answer[idx:idx+v['length']]];idx+=v['length']
            mids=sorted({m for v in z['vaults'] for m in v['queue']});calls=[]
            for m in mids:calls.extend([(contract,sel('market(bytes32)')+m[2:]),(contract,sel('idToMarketParams(bytes32)')+m[2:])])
            keys=[]
            for v in z['vaults']:
                for m in v['queue']:calls.append((contract,sel('position(bytes32,address)')+m[2:]+v['address'][2:].zfill(64)));keys.append((v['address'],m))
            allkeys.append((mids,keys));mitems.append((z['block'],calls))
        answers=batches(chain,mitems);ritems=[];rkeys=[]
        for z,(mids,keys),answer in zip(zs,allkeys,answers):
            z['market']={};calls=[];rm=[]
            for i,m in enumerate(mids):
                a,params=answer[2*i:2*i+2];assert a is not None and params is not None;assert params[0]==int(z['asset'],16);z['market'][m]=dict(state=a,params=params)
                if params[3] and a[2] and z['timestamp']>a[4]:calls.append(('0x'+word(params[3])[-40:],sel('borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))')+''.join(word(x) for x in params+a)));rm.append(m)
            for (v,m),a in zip(keys,answer[2*len(mids):]):assert a is not None;z['positions'][v][m]=a
            ritems.append((z['block'],calls));rkeys.append(rm)
        answers=batches(chain,ritems)
        for z,rm,answer in zip(zs,rkeys,answers):
            for m,a in zip(rm,answer):assert a is not None;z['market'][m]['borrowRate']=a[0]
            _,vaults,_=state(z);assert max(abs(v['gap']) for v in vaults)<=1
            (H/f"{chain}_{z['target']}.json").write_text(json.dumps(z))
        failure=H/f'failure_{chain}.json'
        if failure.exists():failure.unlink()
        print('hours',chain,min(offset+12,len(records)),len(records),flush=True)

def run_chain(chain):
    try:
        records=blocks(chain,targets());pending=[r for r in records if not (H/f"{chain}_{r['target']}.json").exists()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
            fs=[workers.submit(collect,chain,pending[i:i+48]) for i in range(0,len(pending),48)]
            for f in concurrent.futures.as_completed(fs):f.result()
        print('CHAIN COMPLETE',chain,len(records),flush=True)
    except Exception as e:
        (H/f'failure_{chain}.json').write_text(json.dumps({'chain':chain,'error':str(e)},indent=2));raise

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(run_chain,c):c for c in [8453,1,42161]}
        for f in concurrent.futures.as_completed(futures):f.result()
