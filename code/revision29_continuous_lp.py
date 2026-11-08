from pathlib import Path
import pandas as pd,numpy as np,json
from scipy.optimize import linprog
from scipy.sparse import diags,vstack
O=Path(__file__).resolve().parents[1]/'reports/revision29';m=pd.read_parquet(O/'market_cash_sequence.parquet');ix=m.cash_delta_raw.lt(0).to_numpy();o=m.loc[ix];n=len(o);F=np.cumsum(np.where(m.tagged_supply,m.assets_raw,0))[ix];f=np.diff(np.r_[0,F]);a=o.assets_raw.to_numpy(dtype=np.int64);cap=o.cash_after_raw.to_numpy(dtype=np.int64);t=o.target_union.to_numpy(dtype=int);D=diags([np.ones(n),-np.ones(n-1)],[0,-1],format='csr');c=np.r_[t[1:],0]-t
fit=linprog(c,A_ub=vstack([D,-D],format='csr'),b_ub=np.r_[f,a-f]/1e6,bounds=np.column_stack([np.zeros(n),cap/1e6]),method='highs',options={'time_limit':90});r={'success':fit.success,'message':fit.message,'scope':'Continuous study-period gross first-use; opening cash alternative; targets borrow and withdrawals outside Spark vault. Not causal additional payments.'}
if fit.success:
 z=np.rint(fit.x*1e6).astype(np.int64);q=f+np.r_[0,z[:-1]]-z;assert ((q>=0)&(q<=a)&(z>=0)&(z<=cap)).all();value=int(q[t.astype(bool)].sum())/1e6;r.update(lower_usdc=value,objective_gap_usdc=abs(value-(fit.fun+float(t@f)/1e6)),integer_witness_feasible=True);o[['timestamp','tx','log_index']].assign(attributed_micro=q).to_parquet(O/'continuous_lp_lower_witness.parquet',index=False)
(O/'continuous_lp_summary.json').write_text(json.dumps(r,indent=2));print(r)
