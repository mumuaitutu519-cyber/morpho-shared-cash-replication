from pathlib import Path
import requests,json,hashlib,datetime
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26/raw';old=json.loads((R/'data/raw/revision18/spark_history.json').read_text());body=old['request_body'];body['variables']['o']={'startTimestamp':1736899200,'endTimestamp':1764547200,'interval':'DAY'}
p=O/'spark_allocation.json'
if p.exists():ob=json.loads(p.read_text());assert ob['request']==body
else:
 r=requests.post('https://api.morpho.org/graphql',json=body,timeout=50);ob={'url':r.url,'status':r.status_code,'request':body,'response':r.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2));p.with_suffix('.body').write_bytes(r.content)
print(ob['status'],ob['response'].get('errors'));print('allocations',len(ob['response'].get('data',{}).get('vaultByAddress',{}).get('historicalState',{}).get('allocation',[])))
