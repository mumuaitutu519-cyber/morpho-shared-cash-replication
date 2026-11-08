from chain_access import *
STRATEGY='0xd811a47cfd17355f47ac49be02c4744a926dd16b'
for f in sorted((A/'raw').glob('yearn_cash_137_????-??-??.json')):
 z=json.loads(f.read_text());bad=z['unsupported_strategies'];assert all(m==STRATEGY for m in bad)
 if not bad:continue
 h=z['header'];b=h['block'];chain=137;s=STRATEGY;v=addr(batch(chain,b,[(s,sel('vault()'))])[0][0]);data=batch(chain,b,[(v,sel('getData()'))])[0];liquidity=addr(data[0]);asset=z['asset'];cash=batch(chain,b,[(asset,sel('balanceOf(address)')+word(int(liquidity,16)))])[0][0];shares=batch(chain,b,[(v,sel('balanceOf(address)')+word(int(s,16)))])[0][0];claim=batch(chain,b,[(v,sel('convertToAssets(uint256)')+word(shares))])[0][0]
 owncash=[r['idle_cash'] for r in z['strategy_cash_checks'] if r['strategy']==s][0];pos=[p for p in z['positions'] if p['strategy']==s];out={'header':h,'strategy':s,'fToken':v,'liquidity':liquidity,'asset':asset,'liquidity_cash_micro':cash,'fToken_shares':str(shares),'strategy_fToken_claim_micro':claim,'strategy_idle_micro':owncash,'parent_positions':pos};(A/'raw'/('fluid_mapping_'+f.name.removeprefix('yearn_cash_'))).write_text(json.dumps(out,indent=2));print(f.name,cash,claim,owncash,[(p['current_debt'],p['claim_micro']) for p in pos],flush=True)
