from chain_access import *
import pandas as pd
b=block_at(1,1790726400)['block'];fac='0x59709B029B140C853FE28d277f83C3a65e308aF4';n=batch(1,b,[(fac,sel('getVaultListLength()'))])[0][0];vs=[addr(x[0]) for x in batch(1,b,[(fac,sel('vaultList(uint256)')+word(i)) for i in range(n)])];fields=['asset()','totalAssets()','withdrawQueueLength()'];z=batch(1,b,[(v,sel(f)) for v in vs for f in fields]);out=[]
for i,v in enumerate(vs):out.append(dict(vault=v,asset=addr(z[i*3][0]),assets=z[i*3+1][0],queue_length=z[i*3+2][0]))
(A/'raw/euler_discovery.json').write_text(json.dumps(out,indent=2));print('euler',pd.DataFrame(out).to_string(index=False),flush=True)
for c in [42161,137]:
 z=json.loads((A/'raw'/f'morpho_discovery_{c}.json').read_text())['response']['data']['vaults'];print('morpho counts',c,z['pageInfo'],pd.Series([v['asset']['symbol'] for v in z['items']]).value_counts().to_dict(),flush=True)
# Factory deployments filtered by indexed USDC. Archive endpoints may permit whole-range logs.
yfac=['0x310aC28ACF5E514abDbFF9Ab25e21f1bfe22bcAC','0x770D0d1Fb036483Ed4AbB6d53c1C88fb277D812F','0x5577EdcB8A856582297CdBbB07055E6a6E38eb5f','0x444045c5C13C246e117eD36437303cac8E250aB0','0xE9E8C89c8Fc7E8b8F23425688eb68987231178e5']
try:
 z=rpc(1,'eth_getLogs',[{'address':yfac,'fromBlock':hex(17000000),'toBlock':hex(b),'topics':[signature('NewVault(address,address)'),None,'0x'+word(int('0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',16))]}]);(A/'raw/yearn_deployment_logs.json').write_text(json.dumps(z,indent=2));print('yearn logs',len(z),flush=True)
except Exception as e:print('yearn log error',str(e),flush=True)
