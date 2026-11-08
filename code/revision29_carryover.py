"""Feasibility witness, not an optimality claim: no daily source reset."""
from pathlib import Path
import pandas as pd,json
R=Path(__file__).resolve().parents[1];O=R/'reports/revision29';m=pd.read_parquet(O/'market_cash_sequence.parquet');z=0;target_paid=0;attributed=[]
for d,tag,target,cap in zip(m.cash_delta_raw,m.tagged_supply,m.target_union,m.cash_after_raw):
 d=int(d);cap=int(cap)
 if d>=0:
  if tag:z+=d
  q=0
 else:
  q=max(0,z-cap) if target else min(z,-d)
  assert 0<=q<=-d
  z-=q
  if target:target_paid+=q
 assert 0<=z<=cap
 attributed.append(q)
m[['timestamp','tx','log_index','target_union']].assign(attributed_micro=attributed).to_parquet(O/'continuous_feasible_allocation.parquet',index=False)
o={'target_attributed_usdc':target_paid/1e6,'ending_tagged_cash_usdc':z/1e6,'integer_cash_feasible':True,'daily_reset':False,'interpretation':'Feasible allocation only. If target allocation equals zero it proves the nonnegative lower endpoint is zero. Otherwise this is not a tight bound. Target excludes all withdrawals by the Spark vault, including its other holders.'};(O/'continuous_feasibility.json').write_text(json.dumps(o,indent=2));print(o)
