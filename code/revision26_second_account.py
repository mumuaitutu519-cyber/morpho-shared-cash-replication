"""Retain independent account identity source and deposit receipts; no inferred funding labels."""
from pathlib import Path
import pandas as pd,requests,json,hashlib,datetime
from concurrent.futures import ThreadPoolExecutor
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';U='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
p=pd.read_parquet(R/'reports/revision5/vault_economic_events.parquet');p=p[p.onBehalf.eq(A)];p.to_csv(O/'second_account_events.csv',index=False)
url='https://paragraph.com/@ethena-labs/custodian-attestations-of-assets-backing-usde-august-2'
r=requests.get(url,timeout=40);(O/'raw/ethena_august_attestation.html').write_bytes(r.content)
(O/'second_account_identity.json').write_text(json.dumps({'address':A,'source':url,'report_date':'2025-08-29','snapshot_date':'2025-08-27','source_sha256':hashlib.sha256(r.content).hexdigest(),'claim':'Ethena Labs attestation links this address as Coinbase Web3 Wallet 3. Same address operates the observed Base deposits. No universal institution representativeness claim.'},indent=2))
def fetch(tx):
 f=O/'raw'/('second_receipt_'+tx+'.json');body={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionReceipt','params':[tx]}
 if f.exists(): ob=json.loads(f.read_text())
 else:
  rr=requests.post('https://base.drpc.org',json=body,timeout=50);ob={'request':body,'response':rr.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(rr.content).hexdigest()};f.write_text(json.dumps(ob,indent=2))
 rec=ob['response'].get('result');assert rec,ob
 out=[]
 for z in rec['logs']:
  if z['address'].lower()==U and len(z['topics'])==3:
   fr='0x'+z['topics'][1][-40:];to='0x'+z['topics'][2][-40:]
   if A in [fr,to]:out.append({'tx':tx,'block':int(rec['blockNumber'],16),'transaction_index':int(rec['transactionIndex'],16),'log_index':int(z['logIndex'],16),'from':fr,'to':to,'amount_raw':str(int(z['data'],16)),'mint_to_owner':int(fr,16)==0 and to==A})
 return out
rows=[]
with ThreadPoolExecutor(max_workers=3) as ex:
 for result in ex.map(fetch,p[p.type.eq('Deposit')].tx): rows.extend(result)
d=pd.DataFrame(rows);d.to_csv(O/'second_account_deposit_usdc_transfers.csv',index=False);print(d.to_string(index=False));print('same_transaction_mints',d.mint_to_owner.sum())
