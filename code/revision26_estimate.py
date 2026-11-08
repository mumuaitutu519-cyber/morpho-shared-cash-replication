"""Predeclared flow and incumbent-action equations; auditable coefficients and nulls."""
from pathlib import Path
import pandas as pd,numpy as np,json
import statsmodels.api as sm
from scipy.stats import t
from statsmodels.stats.multitest import multipletests
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26'
v=pd.read_parquet(O/'owner_day_panel.parquet');v['date']=pd.to_datetime(v.date)
d=pd.read_csv(O/'daily_conditions.csv',parse_dates=['date']).set_index('date')
e=pd.read_parquet(R/'data/processed/regression_daily_panel.parquet');e['date']=pd.to_datetime(e.date);e=e.set_index('date').sort_index();assert e.index.is_unique
market=pd.DataFrame({'eth_return_pp':100*e.eth_log_return.shift(),'eth_volatility_pp':100*e.eth_log_return.rolling(30).std().shift()})
d=d.join(market);d['premium']=d.native_yield_premium_pp.shift();d['utilization']=100*d.market_utilization.shift();d['log_assets']=np.log(d.direct_assets_raw.shift()/1e6)
flows=v.groupby(['date','spark'])[['deposit_usdc','withdraw_usdc']].sum().unstack('spark').fillna(0)
for flag,name in [(False,'other'),(True,'spark')]:d[name+'_net']=(flows[('deposit_usdc',flag)]-flows[('withdraw_usdc',flag)])/1e6;d[name+'_lag']=d[name+'_net'].shift()
common=['premium','utilization','eth_return_pp','eth_volatility_pp']
def calendar(dates):
 return pd.get_dummies(pd.DataFrame({'month':dates.dt.month.astype(str),'weekday':dates.dt.dayofweek.astype(str)},index=dates.index),drop_first=True,dtype=float)
results=[];meta=[]
def record(label,names,b,se,df,n,extra):
 for j,k in enumerate(names):
  stat=b[j]/se[j];p=2*t.sf(abs(stat),df);results.append({'model':label,'term':k,'coefficient':b[j],'se':se[j],'t':stat,'p':p,'stars':'***' if p<.01 else '**' if p<.05 else '*' if p<.1 else '', 'n':n,'df':df})
 meta.append({'model':label,'n':n,**extra})
for name in ['other','spark']:
 g=d.loc['2025-01-16':'2025-11-30'].copy();cols=common+[name+'_lag','log_assets'];assert g[cols+[name+'_net']].notna().all().all();X=sm.add_constant(pd.concat([g[cols],calendar(pd.Series(g.index,index=g.index))],axis=1));fit=sm.OLS(g[name+'_net'],X).fit()
 for lag in [7,14]:
  f=fit.get_robustcov_results(cov_type='HAC',maxlags=lag,use_correction=True,use_t=True);pd.DataFrame(f.cov_params(),index=X.columns,columns=X.columns).to_csv(O/(name+'_flow_HAC'+str(lag)+'_covariance.csv'));record(name+'_flow_HAC'+str(lag),X.columns,f.params,f.bse,f.df_resid,len(g),{'r2':fit.rsquared,'covariance':'HAC '+str(lag)})
d.to_csv(O/'estimation_daily_inputs.csv',index_label='date')
v=v.merge(d[common],left_on='date',right_index=True,validate='many_to_one');v['log_claim']=np.log(v.prior_claim_usdc.where(v.prior_claim_usdc>0))
def demean(a,ids,G):
 sums=np.zeros((G,a.shape[1]));np.add.at(sums,ids,a);count=np.bincount(ids,minlength=G);return a-sums[ids]/count[ids,None]
def meat(scores,ids):
 G=ids.max()+1;s=np.zeros((G,scores.shape[1]));np.add.at(s,ids,scores);return s.T@s,G
for threshold in [1,0,100]:
 g=v[~v.spark & v.date.ge('2025-01-16') & (v.prior_claim_usdc.ge(threshold) if threshold else v.prior_claim_usdc.gt(0))].copy();before=len(g);counts=g.groupby('owner').size();g=g[g.owner.isin(counts[counts>1].index)].copy();assert g[common+['log_claim','age_days']].notna().all().all()
 ids,owners=pd.factorize(g.owner,sort=True);days,dates=pd.factorize(g.date,sort=True);G=len(owners);N=len(g);X=pd.concat([g[common+['log_claim','age_days']].astype(float),calendar(g.date)],axis=1);names=X.columns.tolist();xx=demean(X.to_numpy(),ids,G);K=xx.shape[1];assert np.linalg.matrix_rank(xx)==K;bread=np.linalg.inv(xx.T@xx);fullk=G+K
 for outcome in ['withdraw_any','deposit_any']:
  yy=demean(g[[outcome]].to_numpy(dtype=float),ids,G).ravel();b=bread@(xx.T@yy);res=yy-xx@b;scores=xx*res[:,None];mo,go=meat(scores,ids);md,gd=meat(scores,days);mi=scores.T@scores
  cov=bread@((go/(go-1)*mo+gd/(gd-1)*md-N/(N-1)*mi)*(N-1)/(N-fullk))@bread;diag=np.diag(cov);assert (diag>0).all(),diag;se=np.sqrt(diag)
  pd.DataFrame(cov,index=names,columns=names).to_csv(O/(outcome+'_cutoff'+str(threshold)+'_covariance.csv'));record(outcome+'_cutoff'+str(threshold),names,b,se,min(G,len(dates))-1,N,{'owners':G,'dates':len(dates),'singleton_rows_removed':before-N,'full_parameter_count':fullk,'within_r2':1-res@res/(yy@yy),'negative_covariance_eigenvalues':int((np.linalg.eigvalsh(cov)<-1e-12).sum()),'zero_within_outcome_owners':int(g.groupby('owner')[outcome].nunique().eq(1).sum())})
 # Independent coefficient check against explicit owner dummies on first 20 multi-day owners.
 if threshold==1:
  z=g[g.owner.isin(owners[:20])];zx=pd.concat([z[common+['log_claim','age_days']].astype(float),calendar(z.date)],axis=1);zi,zo=pd.factorize(z.owner);zw=demean(zx.to_numpy(),zi,len(zo));zy=demean(z[['withdraw_any']].to_numpy(dtype=float),zi,len(zo)).ravel();bw=np.linalg.lstsq(zw,zy,rcond=None)[0];dummy=pd.get_dummies(z.owner,dtype=float);explicit=np.linalg.lstsq(np.column_stack([zx.to_numpy(),dummy.to_numpy()]),z.withdraw_any.to_numpy(),rcond=None)[0][:zx.shape[1]];gap=float(np.max(abs(bw-explicit)));assert gap<1e-7,gap;(O/'within_ols_validation.json').write_text(json.dumps({'deterministic_owners':len(zo),'rows':len(z),'max_coefficient_difference':gap},indent=2))
 print('completed cutoff',threshold,'rows',N,flush=True)
a=pd.DataFrame(results);mask=a.model.isin(['other_flow_HAC7','spark_flow_HAC7','withdraw_any_cutoff1','deposit_any_cutoff1']) & a.term.isin(['premium','utilization']);assert mask.sum()==8;a.loc[mask,'holm_p']=multipletests(a.loc[mask,'p'],method='holm')[1];a.to_csv(O/'regression_results.csv',index=False);(O/'regression_models.json').write_text(json.dumps(meta,indent=2));print(a[mask].to_string(index=False))
