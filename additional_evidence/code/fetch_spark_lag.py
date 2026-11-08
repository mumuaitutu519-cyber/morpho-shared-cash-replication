from pathlib import Path
import json,urllib.request,gzip,time,hashlib
A=Path(__file__).resolve().parents[1]; D=A/'raw/spark_jan15';D.mkdir(parents=True,exist_ok=True)
u='https://portal.sqd.dev/datasets/base-mainnet/stream'
q={'type':'evm','fromBlock':25054927,'toBlock':25098126,'fields':{'block':{'number':True,'timestamp':True,'hash':True},'log':{'logIndex':True,'transactionHash':True,'address':True,'topics':True,'data':True}},'logs':[{'address':['0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'],'topic0':['0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7','0xfbde797d201c681b91056529119e0b02407c7bb96a4a2c75c01fc9667232c8db']} ]}
(D/'query.json').write_text(json.dumps(q,indent=2));pages=[]
while q['fromBlock']<=q['toBlock']:
 start=q['fromBlock'];p=D/f'{start}.jsonl'
 if p.exists():b=p.read_bytes()
 else:
  for attempt in range(5):
   try:
    req=urllib.request.Request(u,json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'})
    with urllib.request.urlopen(req,timeout=50) as r:b=r.read()
    rows=[json.loads(x) for x in b.splitlines() if x];assert rows
    p.write_bytes(b);break
   except Exception:
    if attempt==4:raise
    time.sleep(3)
 rows=[json.loads(x) for x in b.splitlines() if x];last=rows[-1]['header']['number'];assert start<=last<=q['toBlock'];pages.append({'from':start,'last':last,'file':p.name,'sha256':hashlib.sha256(b).hexdigest(),'logs':sum(len(r.get('logs',[])) for r in rows)});q['fromBlock']=last+1
(D/'coverage.json').write_text(json.dumps({'url':u,'pages':pages,'complete':q['fromBlock']==25098127},indent=2));print(json.dumps(pages),flush=True)
