from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
R=Path(__file__).resolve().parents[1];O=R/'reports/revision35';O.mkdir(exist_ok=True)
d=pd.read_csv(R/'reports/revision25/analysis_daily.csv');e=pd.read_csv(R/'reports/revision24/deposit_post_state_audit.csv');v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');g=v[v.risk_set_incumbent & ~v.spark];assert len(g)==513949
ee=pd.DataFrame({'deposit':e.deposit_micro/1e12,'opening':e.opening_wallet_cash_micro/1e12,'shares':e.shares_raw.astype(float)/1e24,'capacity':e.post_capacity_micro/1e12,'cover':e.post_coverage*100})
panels=[('A. Matched deposits',ee,[('deposit','Deposit'),('opening','Opening wallet cash'),('shares','Shares received'),('capacity','Block-end capacity'),('cover','Block-end coverage (\\%)')]),('B. Treasury account days',d,[('claim','Claim value'),('capacity','Withdrawal capacity'),('coverage','Coverage (\\%)'),('treasury_vault_deposit','Gross deposits'),('treasury_vault_withdraw','Gross withdrawals'),('treasury_vault_net','Net deposits')]),('C. Common-market days',d,[('cash','Available cash'),('util_pct','Utilization (\\%)'),('vault_net','Vault net supply'),('net_borrow','Net borrowing'),('other_net','Other net supply')]),('D. Non-Spark owner-days',g,[('prior_claim_usdc','Opening claim'),('deposit_usdc','Daily deposits'),('withdraw_usdc','Daily withdrawals'),('deposit_any','Deposit indicator'),('withdraw_any','Withdrawal indicator'),('prior_cash_coverage','Cash coverage')])]
panels.extend([('E. Positive-flow owner-days',g[g.deposit_usdc>0],[('deposit_usdc','Positive deposits')]),('E. Positive-flow owner-days',g[g.withdraw_usdc>0],[('withdraw_usdc','Positive withdrawals')])])
rows=[]
for panel,f,cols in panels:
 for key,label in cols:
  x=f[key].astype(float);assert x.notna().all() and np.isfinite(x).all();q=x.quantile([.25,.5,.75,.99],interpolation='linear');rawusdc=x if panel.startswith(('D.','E.')) else x*1e6
  transformed=np.arcsinh(rawusdc) if x.min()<0 else np.log1p(rawusdc)
  rows.append(dict(panel=panel,variable=key,label=label,N=len(x),mean=x.mean(),sd=x.std(ddof=1),min=x.min(),p25=q.loc[.25],median=q.loc[.5],p75=q.loc[.75],max=x.max(),p99=q.loc[.99],skewness=x.skew(),zero_percent=100*x.eq(0).mean(),largest_absolute_value_share=abs(x).max()/abs(x).sum() if abs(x).sum() else 0,transformed_skewness=pd.Series(transformed).skew()))
st=pd.DataFrame(rows);st.to_csv(O/'descriptive_statistics.csv',index=False)
# Independent quantile check against sorted linear interpolation.
for panel,f,cols in panels:
 for key,label in cols:
  x=np.sort(f[key].astype(float).to_numpy());row=st[(st.panel==panel)&(st.variable==key)].iloc[0]
  for prob,col in [(.25,'p25'),(.5,'median'),(.75,'p75')]:
   h=(len(x)-1)*prob;j=int(h);expected=x[j]+(x[min(j+1,len(x)-1)]-x[j])*(h-j);assert np.isclose(expected,row[col],rtol=1e-14,atol=1e-12)
z=pd.read_csv(R/'reports/revision28/daily_analysis.csv',parse_dates=['date']).set_index('date');idx=z.loc['2025-01-16':].index;assert len(idx)==319;assert np.allclose(z.loc[idx,'spark_lag'],z.net.shift().loc[idx])
basecols=['utilization','premium','eth_return_pp','eth_volatility_pp','spark_lag','log_assets'];cal=pd.get_dummies(pd.DataFrame({'month':z.index.month.astype(str),'weekday':z.index.dayofweek.astype(str)},index=z.index),drop_first=True,dtype=float);out=[];caps=[]
for variant in ['raw','winsor1','log_signed']:
 w=z.copy()
 if variant=='winsor1':
  for k in ['deposits','withdrawals']:
   lo,hi=z.loc[idx,k].quantile([.01,.99]);w[k]=z[k].clip(lo,hi);caps.append(dict(variable=k,lower_million=lo,upper_million=hi,changed_days=int((w.loc[idx,k]!=z.loc[idx,k]).sum()),original_sum_million=z.loc[idx,k].sum(),capped_sum_million=w.loc[idx,k].sum()))
  w['net']=w.deposits-w.withdrawals;w['spark_lag']=w.net.shift()
 if variant=='log_signed':
  w['deposits']=np.log1p(z.deposits*1e6);w['withdrawals']=np.log1p(z.withdrawals*1e6);w['net']=np.arcsinh(z.net*1e6);w['spark_lag']=np.arcsinh(z.spark_lag*1e6)
 xx=sm.add_constant(pd.concat([w[basecols],cal],axis=1)).loc[idx].astype(float);assert np.linalg.matrix_rank(xx)==xx.shape[1]
 for y in ['deposits','withdrawals','net']:
  f=sm.OLS(w.loc[idx,y],xx).fit()
  for bw in [7,14]:
   ff=f.get_robustcov_results(cov_type='HAC',maxlags=bw,use_correction=True,use_t=True);name=variant+'_'+y+'_HAC'+str(bw)
   for k,b,se,p in zip(xx.columns,ff.params,ff.bse,ff.pvalues):out.append(dict(model=name,variant=variant,outcome=y,HAC=bw,term=k,coefficient=b,se=se,p=p,N=len(idx),r2=f.rsquared))
   pd.DataFrame(ff.cov_params(),index=xx.columns,columns=xx.columns).to_csv(O/(name+'_cov.csv'))
 w.loc[idx,basecols+['deposits','withdrawals','net']].to_csv(O/(variant+'_analysis.csv'))
a=pd.DataFrame(out);sel=a.HAC.eq(7)&a.term.isin(['utilization','premium'])&a.variant.ne('raw');assert sel.sum()==12;a.loc[sel,'holm12']=multipletests(a.loc[sel,'p'],method='holm')[1]
old=pd.read_csv(R/'reports/revision28/all_regressions.csv');checks=[]
for y in ['deposits','withdrawals','net']:
 n=a[(a.variant=='raw')&(a.outcome==y)&a.HAC.eq(7)].merge(old[old.model.eq(y+'_HAC7')],on='term',suffixes=('_new','_old'));gap=float(abs(n.coefficient_new-n.coefficient_old).max());assert gap<1e-9;checks.append(gap)
oldp=np.r_[pd.read_csv(R/'reports/revision28/search_family32.csv').p,pd.read_csv(R/'reports/revision31/focal_tests.csv').p,pd.read_csv(R/'reports/revision32/focal_results.csv').p];assert len(oldp)==48
a.loc[sel,'holm60']=multipletests(np.r_[oldp,a.loc[sel,'p']],method='holm')[1][-12:]
a.to_csv(O/'all_coefficients.csv',index=False);a[a.term.isin(['utilization','premium'])].to_csv(O/'focal_coefficients.csv',index=False);pd.DataFrame(caps).to_csv(O/'winsor_thresholds.csv',index=False)
# Preserve cumulative family, including earlier nonlinear localization and hourly tests.
pd.DataFrame({'p':np.r_[oldp,a.loc[sel,'p']]}).to_csv(O/'search_family60.csv',index=False)
validation={'descriptive_rows':len(st),'quantiles_independently_checked':True,'original_models_max_difference':max(checks),'observations_per_daily_model':319,'models_including_HAC_sensitivity':18,'new_focal_tests_HAC7':12,'no_observations_dropped':True,'funding_and_execution_records_unchanged':True};(O/'VALIDATION.json').write_text(json.dumps(validation,indent=2));print(st[st.variable.isin(['deposit','treasury_vault_deposit','treasury_vault_withdraw','treasury_vault_net','prior_claim_usdc'])][['variable','mean','median','p25','p75','skewness','zero_percent']].to_string(index=False));print(a[a.term.eq('utilization')&a.HAC.eq(7)][['variant','outcome','coefficient','p','holm12']].to_string(index=False))
