from chain_access import *
from pathlib import Path
for f in sorted((A/'raw').glob('yearn_137_????-??-??.json')):
 z=json.loads(f.read_text());h=z['header'];chain=137;b=h['block'];asset=z['USDC'];positive=[p for p in z['allocations'] if p['current_debt']>0];ms=sorted({p['strategy'] for p in positive});vs=[v['address'] for v in z['vaults']];calls=[(asset,sel('balanceOf(address)')+word(int(m,16))) for m in ms+vs];cash=batch(chain,b,calls);cashmap={m:x[0] for m,x in zip(ms+vs,cash)}
 shares=batch(chain,b,[(p['strategy'],sel('balanceOf(address)')+word(int(p['vault'],16))) for p in positive]);calls=[]
 for p,x in zip(positive,shares):calls += [(p['strategy'],sel('convertToAssets(uint256)')+word(x[0])),(p['strategy'],sel('maxWithdraw(address)')+word(int(p['vault'],16)))]
 rz=batch(chain,b,calls)
 for i,p in enumerate(positive):p['claim_micro']=rz[2*i][0];p['maxWithdraw_micro']=rz[2*i+1][0];p['shares_raw']=str(shares[i][0]);p['cash_micro']=cashmap[p['strategy']]
 mapped=[];unsupported=[]
 for m in ms:
  d=z['strategy_interfaces'][m];total=d['totalAssets()'][0];record={'strategy':m,'totalAssets':total,'idle_cash':cashmap[m],'all_reported_assets_held_as_USDC':total==cashmap[m]};mapped.append(record)
  if total!=cashmap[m]:unsupported.append(m)
 out={'header':h,'asset':asset,'vaults':[{**v,'token_cash_micro':cashmap[v['address']]} for v in z['vaults']],'positions':positive,'strategy_cash_checks':mapped,'unsupported_strategies':unsupported};(A/'raw'/('yearn_cash_'+f.name.removeprefix('yearn_'))).write_text(json.dumps(out,indent=2));print(f.name,'positive',len(positive),'unsupported',unsupported,flush=True)
