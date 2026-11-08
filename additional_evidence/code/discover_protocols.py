"""Online discovery preceding the saved-state collectors; no current-positive-assets filter."""
from chain_access import *
TOKENS={1:'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',137:'0x3c499c542cef5e3811e1192ce70d8cc03d5c3359',42161:'0xaf88d065e77c8cc2239327c5edb3a432268e5831'}
FACTORIES=['0x310ac28acf5e514abdbff9ab25e21f1bfe22bcac','0x770d0d1fb036483ed4abb6d53c1c88fb277d812f','0x5577edcb8a856582297cdbbb07055e6a6e38eb5f','0x444045c5c13c246e117ed36437303cac8e250ab0','0xe9e8c89c8fc7e8b8f23425688eb68987231178e5']
for chain in [42161,137]:
 p=A/'raw'/f'morpho_discovery_{chain}.json'
 if not p.exists():
  q='{vaults(first:1000,where:{chainId_in:['+str(chain)+']}){items{address name asset{address symbol decimals} state{totalAssets} creationTimestamp} pageInfo{count countTotal}}}'
  url='https://api.morpho.org/graphql';req=urllib.request.Request(url,json.dumps({'query':q}).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'})
  with urllib.request.urlopen(req,timeout=40) as r:z=json.loads(r.read())
  assert 'errors' not in z and z['data']['vaults']['pageInfo']['count']==z['data']['vaults']['pageInfo']['countTotal'];p.write_text(json.dumps({'url':url,'query':q,'response':z}))
for chain,asset in TOKENS.items():
 p=A/'raw'/('yearn_deployment_logs.json' if chain==1 else f'yearn_chain_probe_{chain}.json')
 if p.exists():continue
 h=block_at(chain,1790726400);logs=rpc(chain,'eth_getLogs',[{'address':FACTORIES,'fromBlock':'0x0','toBlock':hex(h['block']),'topics':[signature('NewVault(address,address)'),None,'0x'+word(int(asset,16))]}]);p.write_text(json.dumps(logs if chain==1 else {'chain':chain,'asset':asset,'header':h,'deployment_logs':logs}))
