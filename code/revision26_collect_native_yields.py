"""Collect market-weighted native-rate inputs; raw vault APY is quarantined."""
from pathlib import Path
import requests,json,hashlib,datetime
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26/raw'
q='''query($address:String!,$o:TimeseriesOptions){vaultByAddress(address:$address,chainId:8453){address name historicalState{totalAssets(options:$o){x y} fee(options:$o){x y} allocation{supplyAssets(options:$o){x y} market{marketId historicalState{supplyAssets(options:$o){x y} borrowAssets(options:$o){x y} supplyApy(options:$o){x y}}}}}}}'''
for n,a in [('spark','0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'),('moonwell','0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca'),('gauntlet','0xc0c5689e6f4d256e861f65465b691aeecc0deb12')]:
 body={'query':q,'variables':{'address':a,'o':{'startTimestamp':1736899200,'endTimestamp':1764547200,'interval':'DAY'}}};p=O/(n+'_native_inputs.json')
 if p.exists():ob=json.loads(p.read_text());assert ob['request']==body
 else:
  r=requests.post('https://api.morpho.org/graphql',json=body,timeout=50);ob={'url':r.url,'status':r.status_code,'request':body,'response':r.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2));p.with_suffix('.body').write_bytes(r.content)
 print(n,ob['status'],ob['response'].get('errors'),flush=True)
