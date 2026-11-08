"""Complete bounded USDC ledger for the independent wallet; preserve stream coverage."""
from pathlib import Path
import requests,json,hashlib,datetime,pandas as pd
from revision22_audit_fees import TRANSFER
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';U='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913';url='https://portal.sqd.dev/datasets/base-mainnet/finalized-stream';start=34450000;end=34758680;cursor=start;rows=[];pages=[]
while cursor<=end:
 q={'type':'evm','fromBlock':cursor,'toBlock':end,'includeAllBlocks':False,'fields':{'block':{'number':True,'hash':True,'timestamp':True},'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},'logs':[{'address':[U],'topic0':[TRANSFER],'topic1':['0x'+A[2:].zfill(64)]},{'address':[U],'topic0':[TRANSFER],'topic2':['0x'+A[2:].zfill(64)]}]};p=O/'raw'/f'second_transfers_{cursor}.json';b=p.with_suffix('.body')
 if not p.exists():
  r=requests.post(url,json=q,timeout=50);b.write_bytes(r.content);p.write_text(json.dumps({'url':url,'query':q,'status':r.status_code,'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
 meta=json.loads(p.read_text());assert meta['status']==200,b.read_text()[:1000];blocks=[json.loads(x) for x in b.read_text().splitlines() if x.strip()];assert blocks
 last=int(blocks[-1]['header']['number']);assert last>=cursor;pages.append({'from':cursor,'through':last,'file':str(b.relative_to(R))})
 for block in blocks:
  for l in block.get('logs',[]):rows.append({'block':block['header']['number'],'timestamp':block['header']['timestamp'],'tx':l['transactionHash'],'log_index':l['logIndex'],'from':'0x'+l['topics'][1][-40:],'to':'0x'+l['topics'][2][-40:],'amount_raw':str(int(l['data'],16))})
 cursor=last+1;print('through',last,'rows',len(rows),flush=True)
pd.DataFrame(rows).drop_duplicates(['tx','log_index']).to_csv(O/'second_account_usdc_ledger.csv',index=False);(O/'second_transfer_coverage.json').write_text(json.dumps({'start_block':start,'end_block':end,'pages':pages},indent=2))
