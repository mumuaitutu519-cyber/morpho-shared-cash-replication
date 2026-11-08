from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).parent));from collect_shared import call
O=Path('reports/revision39_pilot');sel=json.loads((O/'selected_vaults.json').read_text());q='query{'
for i,v in enumerate(sel):
 q+=f'v{i}:vaultByAddress(address:"{v["address"]}",chainId:8453)'+'{address name liquidity{underlying usd} state{blockNumber timestamp totalAssets allocation{supplyAssets market{marketId state{supplyAssets borrowAssets liquidityAssets}}}}}'
q+='}'
r=call('public_live_liquidity',q);print(str(r)[:600])
