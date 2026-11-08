from pathlib import Path
import requests,json,datetime
O=Path('reports/revision39_pilot/raw')
qs={
'vaults_discovery':'query { vaults(first:1000, where:{chainId_in:[8453],assetAddress_in:["0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"]},orderBy:TotalAssetsUsd,orderDirection:Desc){ items {address name creationTimestamp listed asset{address symbol decimals} state{totalAssets totalAssetsUsd} } pageInfo{count countTotal} } }',
'schema':'query { __type(name:"VaultHistoricalState"){fields{name description}} }',
'state_schema':'query { __type(name:"VaultState"){fields{name description}} }'
}
for name,q in qs.items():
 r=requests.post('https://api.morpho.org/graphql',json={'query':q},timeout=50);o={'request':{'query':q},'status':r.status_code,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':r.json()};(O/(name+'.json')).write_text(json.dumps(o,indent=2));print(name,str(o['response'])[:3500],flush=True)
