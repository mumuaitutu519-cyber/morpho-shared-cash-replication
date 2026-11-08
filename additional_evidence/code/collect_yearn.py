from chain_access import *
import pandas as pd
DAY=sys.argv[2] if len(sys.argv)>2 else '2026-09-29'
BOUNDARY=int((pd.Timestamp(DAY,tz='UTC')+pd.Timedelta(days=1)).timestamp())
CHAIN=int(sys.argv[1]) if len(sys.argv)>1 else 1
USDC={1:'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',42161:'0xaf88d065e77c8cc2239327c5edb3a432268e5831',137:'0x3c499c542cef5e3811e1192ce70d8cc03d5c3359'}[CHAIN]
D=json.loads((A/'raw/yearn_deployment_logs.json').read_text()) if CHAIN==1 else json.loads((A/'raw'/f'yearn_chain_probe_{CHAIN}.json').read_text())['deployment_logs'];h=block_at(CHAIN,BOUNDARY);b=h['block'];D=[x for x in D if int(x['blockNumber'],16)<=b];vs=sorted({addr(int(x['topics'][1],16)) for x in D});minimum=min(int(x['blockNumber'],16) for x in D)
# Complete deployed allocator universe, including vaults absent from public endorsed registries.
q={'address':vs,'fromBlock':hex(minimum),'toBlock':hex(b),'topics':[signature('StrategyChanged(address,uint256)')]}
# Vyper flags compile to uint256. Keep queue calls as an independent reconciliation of discovered strategies.
logs=rpc(CHAIN,'eth_getLogs',[q]);(A/'raw'/f'yearn_strategy_logs_{CHAIN}_{DAY}.json').write_text(json.dumps(logs,indent=2));keys=sorted({(x['address'].lower(),addr(int(x['topics'][1],16))) for x in logs})
zz=batch(CHAIN,b,[(v,sel(f)) for v in vs for f in ['asset()','totalAssets()','totalIdle()','totalDebt()','get_default_queue()']]);vaults=[]
for i,v in enumerate(vs):
 z=zz[5*i:5*i+5];assert z[0] and addr(z[0][0])==USDC;queue=[addr(w) for w in z[4][2:]] if z[4] else [];vaults.append({'address':v,'totalAssets':z[1][0],'totalIdle':z[2][0],'totalDebt':z[3][0],'queue':queue});keys=sorted(set(keys)|{(v,m) for m in queue})
zz=batch(CHAIN,b,[(v,sel('strategies(address)')+word(int(m,16))) for v,m in keys]);alloc=[{'vault':v,'strategy':m,'activation':x[0],'last_report':x[1],'current_debt':x[2],'max_debt':str(x[3])} for (v,m),x in zip(keys,zz) if x and x[0]>0];ms=sorted({x['strategy'] for x in alloc if x['current_debt']>0});fns=['asset()','totalAssets()','cash()','vault()','pool()','lendingPool()','aToken()','market()','MORPHO()','morpho()','name()'];zz=batch(CHAIN,b,[(m,sel(f)) for m in ms for f in fns]);interfaces={}
for i,m in enumerate(ms):interfaces[m]={f:x for f,x in zip(fns,zz[i*len(fns):(i+1)*len(fns)])}
for v in vaults:
 v['discovered_debt_sum']=sum(x['current_debt'] for x in alloc if x['vault']==v['address']);v['debt_reconciliation_gap']=v['totalDebt']-v['discovered_debt_sum']
out={'header':h,'USDC':USDC,'factory_deployments':D,'vaults':vaults,'allocations':alloc,'strategy_interfaces':interfaces};(A/'raw'/(f'yearn_{DAY}.json' if CHAIN==1 else f'yearn_{CHAIN}_{DAY}.json')).write_text(json.dumps(out,indent=2))
print('vaults',len(vaults),'positive',sum(v['totalAssets']>0 for v in vaults),'strategies',len(ms),'debtgap',sum(abs(v['debt_reconciliation_gap']) for v in vaults),flush=True)
for m,d in interfaces.items():
 print(m,{k:(addr(v[0]) if k in ['vault()','pool()','lendingPool()','aToken()','market()','MORPHO()','morpho()'] and v and v[0]<2**160 else v) for k,v in d.items() if v},flush=True)
