"""Public, frozen-period market/vault census; archive requests and complete pagination."""
from __future__ import annotations
import argparse, gzip, hashlib, json, time, urllib.request
from pathlib import Path
import pandas as pd
from fetch_ethereum_full import get_json, post_sqd, utc_now, SSL_CONTEXT, TRANSFER_TOPIC

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/revision5'; OUT=ROOT/'reports/revision5'
BASE='https://portal.sqd.dev/datasets/base-mainnet'
MARKET='0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836'
MORPHO='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb'
VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
USDC='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
CREATION=19326981
START=int(pd.Timestamp('2024-11-18',tz='UTC').timestamp())
END=int(pd.Timestamp('2025-12-01',tz='UTC').timestamp())
FIELDS={'block':{'number':True,'timestamp':True},'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}}

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def padded(a):return '0x'+a[2:].rjust(64,'0')
def archive_json(name,obj):
    p=RAW/name;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2)+'\n');return p

def bounds():
    p=RAW/'bounds.json'
    if p.exists():return json.loads(p.read_text())
    response=get_json(f'{BASE}/timestamps/{END}/block',attempts=3)
    obj={'queried_at':utc_now(),'url':f'{BASE}/timestamps/{END}/block','response':response,
         'from_market_block':CREATION,'to_block':int(response['block_number'])-1,'start_utc':START,'end_exclusive_utc':END}
    archive_json('bounds.json',obj);return obj

def collect_chunk(kind,start,end,filters,stream='/stream'):
    p=RAW/kind/f'blocks_{start}_{end}.jsonl.gz';p.parent.mkdir(parents=True,exist_ok=True)
    meta=p.with_suffix('.meta.json')
    if p.exists() and meta.exists():
        m=json.loads(meta.read_text());assert m['sha256']==digest(p);return m
    temporary=p.with_suffix('.part');cursor=start;pages=logs=0;last_ts=None;began=utc_now()
    with gzip.open(temporary,'wt') as f:
        while cursor<=end:
            query={'type':'evm','fromBlock':cursor,'toBlock':end,'fields':FIELDS,'logs':filters}
            records=[json.loads(l) for l in post_sqd(BASE+stream,query,attempts=4).splitlines() if l.strip()]
            assert records and cursor<=int(records[-1]['header']['number'])<=end
            assert all(cursor<=int(b['header']['number'])<=end for b in records)
            f.write(json.dumps({'query':query,'queried_at':utc_now(),'records':records},separators=(',',':'))+'\n')
            logs+=sum(len(b.get('logs',[])) for b in records);pages+=1
            cursor=int(records[-1]['header']['number'])+1;last_ts=records[-1]['header']['timestamp']
            print('page',kind,pages,cursor,logs,flush=True)
            if pages>1000:raise RuntimeError('Pagination guard')
    temporary.replace(p)
    m={'kind':kind,'from_block':start,'to_block':end,'last_timestamp':last_ts,'pages':pages,'logs':logs,'started_at':began,
       'completed_at':utc_now(),'file':str(p.relative_to(ROOT)),'sha256':digest(p),'endpoint':BASE+stream,'filters':filters}
    meta.write_text(json.dumps(m,indent=2)+'\n')
    print(kind,start,end,logs,pages,flush=True);return m

def collect_history():
    p=RAW/'market_history.json'
    if p.exists():return
    query='''query History($id: String!, $chain: Int!, $options: TimeseriesOptions) {
      marketById(marketId: $id, chainId: $chain) { marketId historicalState {
        supplyAssets(options: $options) { x y }
        borrowAssets(options: $options) { x y }
        utilization(options: $options) { x y }
        borrowApy(options: $options) { x y }
      }}
    }'''
    payload={'query':query,'variables':{'id':MARKET,'chain':8453,'options':{'startTimestamp':START-86400,'endTimestamp':END,'interval':'DAY'}}}
    endpoint='https://api.morpho.org/graphql'
    req=urllib.request.Request(endpoint,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'ghost-redemptions-research/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=60,context=SSL_CONTEXT) as f:response=json.loads(f.read())
        archive_json('market_history.json',{'url':endpoint,'request':payload,'queried_at':utc_now(),'response':response})
        print('historical API', 'errors' if 'errors' in response else 'received',flush=True)
    except Exception as e:
        archive_json('market_history_error.json',{'url':endpoint,'request':payload,'queried_at':utc_now(),'error':repr(e)})
        print('Historical API unavailable:',repr(e),flush=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['market','vault','treasury','history','probe','all'],default='all')
    parser.add_argument('--chunk',type=int,default=50000000)
    parser.add_argument('--stream',choices=['/stream','/finalized-stream'],default='/finalized-stream')
    args=parser.parse_args()
    RAW.mkdir(exist_ok=True,parents=True);OUT.mkdir(exist_ok=True,parents=True)
    if args.kind=='probe':
        results=[]
        for span,filter_ in [(0,{'address':[MORPHO],'topic1':[MARKET]}),(999,{'address':[MORPHO]}),(999,{'address':[MORPHO],'topic1':[MARKET]})]:
            q={'type':'evm','fromBlock':CREATION,'toBlock':CREATION+span,'fields':FIELDS,'logs':[filter_]}
            req=urllib.request.Request(BASE+'/stream',data=json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'ghost-redemptions-research/1.0'})
            try:
                with urllib.request.urlopen(req,timeout=35,context=SSL_CONTEXT) as f:r={'status':f.status,'body':f.read().decode()}
            except Exception as e:r={'error':repr(e),'body':e.read().decode(errors='replace') if hasattr(e,'read') else ''}
            results.append({'query':q,'queried_at':utc_now(),'response':r});print(span,str(r)[:600],flush=True)
        archive_json('sqd_probe.json',results);return
    if args.kind in ['all','history']:collect_history()
    if args.kind=='history':return
    b=bounds();end=b['to_block'];definitions={
      'market':(CREATION,[{'address':[MORPHO],'topic1':[MARKET]}]),
      'vault':(0,[{'address':[VAULT]}]),
      'treasury':(CREATION,[{'address':[USDC],'topic0':[TRANSFER_TOPIC],'topic1':[padded(PROXY)]},
                           {'address':[USDC],'topic0':[TRANSFER_TOPIC],'topic2':[padded(PROXY)]}])}
    items=[]
    for kind,(start,filters) in definitions.items():
        if args.kind not in ['all',kind]:continue
        chunk=args.chunk
        for lo in range(start,end+1,chunk):
            items.append(collect_chunk(kind,lo,min(lo+chunk-1,end),filters,args.stream))
    all_items=[]
    for kind in definitions:
        for p in sorted((RAW/kind).glob('*.meta.json')):all_items.append(json.loads(p.read_text()))
    manifest={'created_at':utc_now(),'plan_sha256':digest(ROOT/'artifacts/REVISION5_LIQUIDITY_RESPONSE_PLAN.md'),'bounds':b,'items':all_items}
    (OUT/'collection_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
