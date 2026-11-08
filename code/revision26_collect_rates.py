"""Read-only historical API collection, fixed R25 dates; all responses archived."""
from pathlib import Path
import requests,json,hashlib,datetime
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26/raw';O.mkdir(parents=True,exist_ok=True)
V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
import sys
sys.path.insert(0,str(R/'code'))
from revision5_collect_liquidity import MARKET
options={'startTimestamp':1736899200,'endTimestamp':1764547200,'interval':'DAY'}
queries={
'vault_rates':('''query($v:String!,$o:TimeseriesOptions){vaultByAddress(address:$v,chainId:8453){address name historicalState{apy(options:$o){x y} netApy(options:$o){x y} fee(options:$o){x y} totalAssets(options:$o){x y} totalSupply(options:$o){x y}}}}''',{'v':V,'o':options}),
'market_rates':('''query($m:String!,$o:TimeseriesOptions){marketById(marketId:$m,chainId:8453){marketId historicalState{borrowApy(options:$o){x y} supplyApy(options:$o){x y} utilization(options:$o){x y} supplyAssets(options:$o){x y} borrowAssets(options:$o){x y}}}}''',{'m':MARKET,'o':options})}
for peer,addr in [('moonwell','0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca'),('gauntlet','0xc0c5689e6f4d256e861f65465b691aeecc0deb12')]:
 queries[peer+'_rates']=(queries['vault_rates'][0],{'v':addr,'o':options})
for name,(q,v) in queries.items():
 p=O/(name+'.json');body={'query':q,'variables':v}
 if p.exists(): obj=json.loads(p.read_text());assert obj['request']==body
 else:
  r=requests.post('https://api.morpho.org/graphql',json=body,timeout=50)
  obj={'url':r.url,'status':r.status_code,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request':body,'response':r.json(),'sha256':hashlib.sha256(r.content).hexdigest()};(O/(name+'.body')).write_bytes(r.content);p.write_text(json.dumps(obj,indent=2))
 print(name,obj['status'],obj['response'].get('errors'),flush=True)
 if obj['response'].get('data'):
  first=next(iter(obj['response']['data'].values()));print({k:len(v) for k,v in first['historicalState'].items()},flush=True)
