from pathlib import Path
import requests,json,hashlib,datetime,pandas as pd
from concurrent.futures import ThreadPoolExecutor
from revision22_audit_fees import TRANSFER
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';U='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913';lo=34450000;hi=34758680
jobs=[(l,min(l+9999,hi),n) for l in range(lo,hi+1,10000) for n in [1,2]]
def job(x):
 l,h,n=x;topics=[TRANSFER,'0x'+A[2:].zfill(64)] if n==1 else [TRANSFER,None,'0x'+A[2:].zfill(64)];q={'jsonrpc':'2.0','id':1,'method':'eth_getLogs','params':[{'address':U,'fromBlock':hex(l),'toBlock':hex(h),'topics':topics}]};f=O/'raw'/f'official_ethena_logs_{l}_{h}_{n}.json'
 if f.exists():o=json.loads(f.read_text())
 else:
  r=requests.post('https://mainnet.base.org',json=q,timeout=40);o={'request':q,'response':r.json(),'status':r.status_code,'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};f.write_text(json.dumps(o,indent=2))
 assert isinstance(o['response'].get('result'),list),o['response'];return x,o['response']['result']
rows=[];coverage=[]
with ThreadPoolExecutor(max_workers=2) as ex:
 for (l,h,n),logs in ex.map(job,jobs):
  coverage.append({'from':l,'through':h,'direction':n,'logs':len(logs)})
  for z in logs:rows.append({'block':int(z['blockNumber'],16),'tx':z['transactionHash'],'log_index':int(z['logIndex'],16),'from':'0x'+z['topics'][1][-40:],'to':'0x'+z['topics'][2][-40:],'amount_raw':str(int(z['data'],16))})
  if logs:print(l,n,len(logs),flush=True)
pd.DataFrame(rows).drop_duplicates(['tx','log_index']).sort_values(['block','log_index']).to_csv(O/'ethena_usdc_ledger.csv',index=False);(O/'ethena_log_coverage.json').write_text(json.dumps(coverage,indent=2));print('done',len(rows))
