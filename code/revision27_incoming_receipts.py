from pathlib import Path
import pandas as pd,requests,json,hashlib
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';d=pd.read_csv(O/'ethena_usdc_ledger.csv');txs=d[d.to.eq(A)].tx.tolist()
def f(tx):
 p=O/'raw'/('incoming_'+tx+'.json');q={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionReceipt','params':[tx]}
 if p.exists():o=json.loads(p.read_text())
 else:
  r=requests.post('https://mainnet.base.org',json=q,timeout=35);o={'request':q,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(o,indent=2))
 rec=o['response']['result'];return {'tx':tx,'sender':rec['from'],'contract':rec['to'],'logs':len(rec['logs']),'log_addresses':sorted(set(z['address'] for z in rec['logs']))}
with ThreadPoolExecutor(max_workers=2) as e:rows=list(e.map(f,txs))
(O/'incoming_receipt_summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
