from chain_access import *
from collect_morpho import CONFIG
for chain,(M,asset,fac) in CONFIG.items():
 try:
  h=block_at(chain,1790726400);logs=rpc(chain,'eth_getLogs',[{'address':fac,'fromBlock':'0x0','toBlock':hex(h['block']),'topics':[signature('CreateMetaMorpho(address,address,address,uint256,address,string,string,bytes32)'),None,None,'0x'+word(int(asset,16))]}]);vs=sorted({addr(int(x['topics'][1],16)) for x in logs});z=json.loads((A/'raw'/f'morpho_discovery_{chain}.json').read_text())['response']['data']['vaults'];api=sorted(x['address'].lower() for x in z['items'] if x['asset']['address'].lower()==asset.lower() and x['creationTimestamp']<1790726400);out={'chain':chain,'factory':fac,'header':h,'logs':logs,'factory_vaults':vs,'api_vaults':api,'missing_from_api':sorted(set(vs)-set(api)),'not_in_factory_logs':sorted(set(api)-set(vs))};(A/'raw'/f'morpho_factory_audit_{chain}.json').write_text(json.dumps(out,indent=2));print(chain,len(vs),len(api),out['missing_from_api'],out['not_in_factory_logs'],flush=True)
 except Exception as e:print(chain,str(e),flush=True)
