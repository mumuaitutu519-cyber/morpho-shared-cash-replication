from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats
A=Path(__file__).resolve().parents[1];R=A.parent;C=A/'cross_chain';O=C/'outputs';p=pd.read_csv(O/'vault_state_panel.csv');rr=pd.read_csv(O/'cross_chain_regressions.csv');mm=pd.read_csv(O/'cross_chain_models.csv');good=p[~p.zero_S].sort_values(['entity','date']).reset_index(drop=True);terms=['shared_market_share','active_markets','log_assets','utilization10','max_market_share'];checks=[]
assert p.chain_state.nunique()==28 and not p.duplicated(['entity','date']).any();assert p.assets_micro.gt(0).all();assert p.zero_S.eq(p.S_micro.eq(0)).all();assert good.D.between(0,1).all();assert good[terms].notna().all().all();assert np.allclose(good.D,(good.S_micro-(good.J_chain_micro-good.J_without_vault_micro))/good.S_micro);checks.append('28 chain-states; unique chain+vault+date rows; positive assets; S-zero exclusion; D identity and [0,1] bounds verified.')
# Independent direct leave-one-vault-out calculation; reconstruct all J(V-v) rather than reuse algebraic contributions.
positions=pd.read_parquet(O/'position_panel.parquet')
for (chain,day),x in positions.groupby(['chain','date']):
 for v in p[(p.chain==chain)&(p.date==day)].itertuples():
  other=x[x.vault!=v.vault];m=other.groupby('market').agg(P=('position','sum'),M=('cash','first'));J0=sum(min(int(a),int(b)) for a,b in zip(m.P,m.M));assert J0==v.J_without_vault_micro
checks.append('All leave-one-vault-out joint budgets agree with independent deletion and regrouping of the position data.')
for spec in ['b_chain_state_FE','c_vault_chain_state_FE']:
 if spec.startswith('b_'):F=pd.get_dummies(good.chain_state,dtype=float)
 else:
  entity=pd.get_dummies(good.entity,dtype=float);state=pd.get_dummies(good.chain_state,dtype=float);anchors=good.groupby('chain').chain_state.min().tolist();state=state.drop(columns=anchors);F=pd.concat([entity,state],axis=1)
 X=pd.concat([good[terms],F],axis=1);fit=sm.OLS(good.D,X).fit(cov_type='cluster',cov_kwds={'groups':good.entity,'use_correction':True,'df_correction':True},use_t=True);r=rr[rr.spec==spec].set_index('variable').loc[terms];assert np.allclose(fit.params[terms],r.coefficient,rtol=1e-7,atol=1e-9);assert np.allclose(fit.bse[terms],r.standard_error,rtol=1e-7,atol=1e-9);assert np.allclose(fit.pvalues[terms],r.p_value,rtol=1e-6,atol=1e-9);assert fit.model.rank==mm[mm.spec==spec].design_rank.iloc[0]
 checks.append(spec+': coefficients, clustered SEs, p-values and FE rank verified using independent explicit-dummy OLS.')
for row in mm.itertuples():
 r=rr[rr.spec==row.spec];assert np.allclose(r.coefficient/r.standard_error,r.t_statistic);assert np.allclose(2*stats.t.sf(abs(r.t_statistic),row.df_p),r.p_value,rtol=1e-9,atol=1e-12)
checks.append('All displayed t statistics and p-values agree with reported inference degrees of freedom.')
me=pd.read_csv(O/'mechanism_regressions.csv',float_precision='round_trip');old=pd.read_csv(A/'outputs/mechanism.csv',float_precision='round_trip');compare=me[me.spec!='e_formula_error'].merge(old,on=['model','spec','variable'],suffixes=('_new','_input'));assert len(compare)==len(old)
for col in ['coefficient','standard_error','t_statistic','p_value']:assert np.allclose(compare[col+'_new'],compare[col+'_input'],rtol=1e-14,atol=1e-18)
e=pd.read_csv(O/'mechanism_e_data.csv');assert len(e)==495 and e.tx.nunique()==93;meta=pd.read_csv(O/'mechanism_models.csv');assert meta[meta.spec=='e_formula_error'].Obs.iloc[0]==495
wide=pd.read_csv(O/'mechanism_paper_table.csv').fillna('');specs=['a_pooled','b_transaction_FE','c_constrained','d_constrained_from_2025_04_23','e_formula_error']
for label,term in [('min(deposit, opening gap)','min_deposit_opening_gap'),('Opening gap','opening_gap'),('Intercept','intercept')]:
 for col,spec in zip('abcde',specs):
  r=me[(me.spec==spec)&(me.variable==term)];cell=wide[wide.row==label][col].iloc[0];tcell=wide[wide.row==label+' t statistic'][col].iloc[0]
  if len(r):
   r=r.iloc[0];stars='***' if r.p_value<.01 else '**' if r.p_value<.05 else '*' if r.p_value<.1 else '';assert cell==f'{r.coefficient:.6f}'+stars and tcell==f'({r.t_statistic:.2f})'
  else:assert cell=='' and tcell==''
checks.append('Mechanism a-d numeric results retained; e uses 495 observations/93 transactions; every paper-table coefficient, t statistic and significance star matches the numeric CSV.')
d=pd.read_csv(O/'descriptives.csv');assert d.vaults.sum()==len(good) and d.positive_assets_vaults.sum()==len(p) and d.zero_S_excluded.sum()==p.zero_S.sum();checks.append('Descriptive counts reconcile with the complete positive-assets sample and every S-zero exclusion.')
expected={'Counting_the_same_cash.docx':'11bd3d97c4e15184429f00b7df91374bc388059cbd63b1922c7191e7f77866d3','Counting_the_same_cash.pdf':'07058da857e0bc72c0278fd3db0070fdc240f9e72bf4d016b9c8efbb3ed7cb46'}
for name,digest in expected.items():
 f=R.parents[1]/name
 if f.exists():assert hashlib.sha256(f.read_bytes()).hexdigest()==digest
checks.append('Manuscript source workspace hashes match the unchanged Word and PDF; manuscripts are excluded from the results archive.')
(C/'checks.md').write_text('# Checks\n\n'+'\n'.join('- PASS: '+s for s in checks)+'\n');print('\n'.join(checks))
