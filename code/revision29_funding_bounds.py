"""Sparse inventory LP: daily first uses of strictly linked treasury market receipts."""
from pathlib import Path
import pandas as pd,numpy as np,json
from scipy.optimize import linprog
from scipy.sparse import diags,vstack
R=Path(__file__).resolve().parents[1];O=R/'reports/revision29';W=O/'witnesses';W.mkdir(exist_ok=True);m=pd.read_parquet(O/'market_cash_sequence.parquet');results=[];validation=[]
for day,g in m.groupby('date',sort=True):
 idx=g.cash_delta_raw.lt(0).to_numpy();outs=g.loc[idx].copy();n=len(outs);f=np.cumsum(np.where(g.tagged_supply,g.assets_raw,0));F=f[idx];ins=np.diff(np.r_[0,F]);amount=outs.assets_raw.to_numpy(dtype=np.int64);caps=outs.cash_after_raw.to_numpy(dtype=np.int64);total=int(np.where(g.tagged_supply,g.assets_raw,0).sum());D=diags([np.ones(n),-np.ones(n-1)],[0,-1],format='csr');A=vstack([D,-D],format='csr');rhs=np.r_[ins,amount-ins]/1e6;bounds=np.column_stack([np.zeros(n),caps/1e6]);w=outs[['timestamp','block','tx','log_index','type','position_owner','assets_raw','cash_after_raw']].copy();stats={'date':day,'opening_cash_usdc':int(g.cash_before_raw.iloc[0])/1e6,'closing_cash_usdc':int(g.cash_after_raw.iloc[-1])/1e6,'tagged_supply_usdc':total/1e6,'tagged_withdrawal_usdc':int(g.loc[g.tagged_withdrawal,'assets_raw'].sum())/1e6}
 if n==0:raise AssertionError('no outflows')
 for target in ['borrow','other_withdrawal','union']:
  mask=outs['target_'+target].to_numpy(dtype=int);c=np.r_[mask[1:],0]-mask;stats[target+'_payments_usdc']=int(amount[mask.astype(bool)].sum())/1e6
  for sign,label in [(1,'lower'),(-1,'upper')]:
   if total:
    fit=linprog(sign*c,A_ub=A,b_ub=rhs,bounds=bounds,method='highs');assert fit.success,(day,target,fit.message);z=np.rint(fit.x*1e6).astype(np.int64)
   else:z=np.zeros(n,dtype=np.int64)
   q=ins+np.r_[0,z[:-1]]-z
   assert ((q>=0)&(q<=amount)&(z>=0)&(z<=caps)).all(),(day,target,label,'integer witness infeasible')
   end=int(q[mask.astype(bool)].sum());stats[target+'_'+label+'_usdc']=end/1e6;w[target+'_'+label+'_attributed_micro']=q
   if total:
    expected=sign*fit.fun+float(mask@ins)/1e6;gap=abs(expected-end/1e6);assert gap<.0001,(day,target,label,gap)
    validation.append({'date':day,'target':target,'endpoint':label,'primal_objective_gap_usdc':gap,'integer_witness_feasible':True})
  assert stats[target+'_lower_usdc']<=stats[target+'_upper_usdc']+1e-6
 results.append(stats);w.to_parquet(W/f'{day}.parquet',index=False)
 if len(results)%40==0:print('completed days',len(results),flush=True)
d=pd.DataFrame(results);d.to_csv(O/'daily_first_use_bounds.csv',index=False);pd.DataFrame(validation).to_csv(O/'LP_validation.csv',index=False);summary={'days':len(d),'tagged_supplies_usdc':d.tagged_supply_usdc.sum(),'tagged_withdrawals_usdc':d.tagged_withdrawal_usdc.sum(),'targets':{k:{'payments_usdc':d[k+'_payments_usdc'].sum(),'lower_usdc':d[k+'_lower_usdc'].sum(),'upper_usdc':d[k+'_upper_usdc'].sum(),'days_positive_lower':int(d[k+'_lower_usdc'].gt(1e-6).sum()),'max_daily_lower_usdc':d[k+'_lower_usdc'].max()} for k in ['borrow','other_withdrawal','union']},'all_integer_witnesses_feasible':True,'max_primal_objective_gap_usdc':max(x['primal_objective_gap_usdc'] for x in validation),'scope':'Gross daily first-use support of completed payments, conditional on complete retained cash ledger; day-opening cash is alternative funding, not attributed. No causal removal or unique permanent token labels.'};(O/'first_use_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
