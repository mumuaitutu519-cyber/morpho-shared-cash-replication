"""Archive missing market withdrawals and borrows; immutable resumable SQD pages."""
from pathlib import Path
import sys,json,gzip,urllib.request,time,hashlib,concurrent.futures
import pandas as pd
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';RAW=P/'raw/operations';RAW.mkdir(parents=True,exist_ok=True)
URL='https://portal.sqd.dev/datasets/base-mainnet/stream';M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb'
p=pd.read_parquet(R/'outputs/empirical/positions.parquet');markets=sorted(p[p.date.between('2025-01-16','2026-03-30') & p.position.gt(0)].market.unique());assert len(markets)==33
sigs=json.loads((R/'data/raw/revision5/event_signatures.json').read_text());topics=[x['topic'] for x in sigs if x['signature'].startswith(('Withdraw(','Borrow('))]
Q={'type':'evm','fields':{'block':{'number':True,'timestamp':True,'hash':True},'log':{'logIndex':True,'transactionIndex':True,'transactionHash':True,'address':True,'topics':True,'data':True}},'logs':[{'address':[M],'topic0':topics,'topic1':markets}]}
start=25098127;end=25098126+439*43200
(P/'raw/operation_query.json').write_text(json.dumps({'url':URL,'query':Q,'start':start,'end':end,'markets':markets},indent=2))
def segment(job):
 lo,hi=job;folder=RAW/str(lo);folder.mkdir(exist_ok=True);cur=lo;count=0
 for p in sorted(folder.glob('*.meta.json')):
  if p.name.startswith('._'):continue
  m=json.loads(p.read_text())
  if m['from']==cur:cur=m['to']+1;count+=m['logs']
 while cur<=hi:
  q={**Q,'fromBlock':cur,'toBlock':hi};err=[]
  for attempt in range(4):
   try:
    req=urllib.request.Request(URL,json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0','Accept-Encoding':'gzip'})
    with urllib.request.urlopen(req,timeout=45) as response:
     b=response.read();b=gzip.decompress(b) if response.headers.get('Content-Encoding')=='gzip' else b
    rows=[json.loads(x) for x in b.splitlines() if x];assert rows;last=rows[-1]['header']['number'];assert cur<=last<=hi
    break
   except Exception as e:
    err.append(str(e));time.sleep(2**attempt)
  else:
   (folder/'error.json').write_text(json.dumps({'from':cur,'to':hi,'errors':err}));return {'start':lo,'complete':False,'error':err}
  file=folder/f'{cur}_{last}.jsonl.gz'
  with gzip.open(file,'wb') as f:f.write(b)
  logs=sum(len(r.get('logs',[])) for r in rows);file.with_suffix('.meta.json').write_text(json.dumps({'from':cur,'to':last,'logs':logs,'sha256':hashlib.sha256(b).hexdigest(),'file':file.name}));count+=logs;cur=last+1
 out={'start':lo,'end':hi,'complete':True,'logs':count};(folder/'complete.json').write_text(json.dumps(out));print(out,flush=True);return out
if __name__=='__main__':
 jobs=[(i,min(end,i+43200*14-1)) for i in range(start,end+1,43200*14)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:out=list(ex.map(segment,jobs))
 (P/'raw/operation_coverage.json').write_text(json.dumps(out,indent=2));print('segments',len(out),'complete',sum(x['complete'] for x in out),flush=True)
