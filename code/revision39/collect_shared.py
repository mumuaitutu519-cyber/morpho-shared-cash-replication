from pathlib import Path
import requests,json,time,datetime,concurrent.futures
O=Path('reports/revision39_pilot/raw');OUT=O.parent

def call(name,q,v=None):
 p=O/(name+'.json')
 if p.exists():
  a=json.loads(p.read_text())
  if a.get('response',{}).get('data') and not a['response'].get('errors'):return a['response']['data']
 body={'query':q,'variables':v or {}}
 for attempt in range(3):
  try:
   r=requests.post('https://api.morpho.org/graphql',json=body,timeout=90);res=r.json();a={'request':body,'status':r.status_code,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':res};p.write_text(json.dumps(a));
   if not res.get('errors') and res.get('data'):return res['data']
   print(name,str(res.get('errors'))[:350],flush=True)
   break
  except Exception as e:print(name,str(e),flush=True);time.sleep(2)
 return None
if __name__=='__main__':
 allv=json.loads((O/'vaults_discovery.json').read_text())['response']['data']['vaults'];print('DISCOVERY',len(allv['items']),allv['pageInfo'],flush=True)
 vs=[x for x in allv['items'] if x['creationTimestamp']<1737072000];print('BASELINE candidates',len(vs),flush=True)
 q='query($a:String!){vaultByAddress(address:$a,chainId:8453){address name historicalState{totalAssets(options:{startTimestamp:1737072000,endTimestamp:1737072000,interval:DAY}){x y}}}}'
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  rr=list(ex.map(lambda x:call('baseline_'+x['address'].lower(),q,{'a':x['address']}),vs))
 ranking=[]
 for x,r in zip(vs,rr):
  if r:
   vals=r['vaultByAddress']['historicalState']['totalAssets'];val=next((z['y'] for z in vals if z['x']==1737072000),None)
   if val is not None:ranking.append({**x,'baseline_assets':int(val)})
 ranking.sort(key=lambda x:-x['baseline_assets']);(OUT/'baseline_ranking.json').write_text(json.dumps(ranking,indent=2));chosen=ranking[:10];(OUT/'selected_vaults.json').write_text(json.dumps(chosen,indent=2));print('SELECTED',[(v['name'],v['baseline_assets']/1e6) for v in chosen],flush=True)
 query='''query($a:String!,$o:TimeseriesOptions){vaultByAddress(address:$a,chainId:8453){address name asset{address symbol decimals} historicalState{totalAssets(options:$o){x y} allocation{supplyAssets(options:$o){x y} market{marketId loanAsset{address} collateralAsset{address symbol} historicalState{supplyAssets(options:$o){x y} borrowAssets(options:$o){x y}}}}}}}'''
 # One common daily grid, fixed before seeing overlap outcomes. Extended window 2025-01-16 through 2026-08-31.
 opts={'startTimestamp':1737072000,'endTimestamp':1788220800,'interval':'DAY'}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  rr=list(ex.map(lambda x:call('history_'+x['address'].lower(),query,{'a':x['address'],'o':opts}),chosen))
 print('HISTORIES',sum(x is not None for x in rr),'of',len(rr),flush=True)
 # Introspection locates public liquidity fields and their definitions.
 for typ in ['Vault','VaultHistory']:
  call('schema_'+typ,'query{__type(name:"'+typ+'"){fields{name description type{name kind ofType{name kind}}}}}')
