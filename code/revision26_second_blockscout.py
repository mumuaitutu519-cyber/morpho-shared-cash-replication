from pathlib import Path
import requests,json,hashlib,pandas as pd
from revision22_audit_fees import TRANSFER
O=Path(__file__).resolve().parents[1]/'reports/revision26';A='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c';rows=[]
for topic in ['topic1','topic2']:
 params={'module':'logs','action':'getLogs','fromBlock':34450000,'toBlock':34758680,'address':'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913','topic0':TRANSFER,topic:'0x'+A[2:].zfill(64),'topic0_'+topic+'_opr':'and'}
 # Explorer topic operator is topic0_1_opr / topic0_2_opr.
 params.pop('topic0_'+topic+'_opr');params['topic0_'+topic[-1]+'_opr']='and'
 r=requests.get('https://base.blockscout.com/api',params=params,timeout=45);p=O/'raw'/('second_blockscout_'+topic+'.json');p.write_text(json.dumps({'url':r.url,'status':r.status_code,'sha256':hashlib.sha256(r.content).hexdigest(),'response':r.json()},indent=2));print(topic,r.status_code,r.text[:500],flush=True)
 ob=r.json();assert isinstance(ob.get('result'),list),ob;assert len(ob['result'])<1000
 for l in ob['result']: rows.append({'block':int(l['blockNumber'],16),'tx':l['transactionHash'],'log_index':int(l['logIndex'],16),'from':'0x'+l['topics'][1][-40:],'to':'0x'+l['topics'][2][-40:],'amount_raw':str(int(l['data'],16))})
d=pd.DataFrame(rows).drop_duplicates(['tx','log_index']).sort_values(['block','log_index']);d.to_csv(O/'second_account_usdc_ledger.csv',index=False);print(d.to_string(index=False))
