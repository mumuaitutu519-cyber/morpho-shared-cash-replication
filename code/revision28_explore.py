"""Bounded R28 exploration with complete search ledger and joint error control."""
from pathlib import Path
import json,numpy as np,pandas as pd,statsmodels.api as sm
from scipy.stats import t
from statsmodels.stats.multitest import multipletests
R=Path(__file__).resolve().parents[1];O=R/'reports/revision28';O.mkdir(exist_ok=True)
v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v.date=pd.to_datetime(v.date)
d=pd.read_csv(R/'reports/revision27/estimation_daily_inputs.csv',parse_dates=['date']).set_index('date')
s=v[v.spark].set_index('date');d['deposits']=s.deposit_usdc/1e6;d['withdrawals']=s.withdraw_usdc/1e6;d['net']=d.deposits-d.withdrawals
for y in ['deposits','withdrawals','net']:d[y+'_rate']=100*d[y]*1e6/s.prior_claim_usdc
cols=['utilization','premium','eth_return_pp','eth_volatility_pp','spark_lag','log_assets']
cal=pd.get_dummies(pd.DataFrame({'month':d.index.month.astype(str),'weekday':d.index.dayofweek.astype(str)},index=d.index),drop_first=True,dtype=float)
X=sm.add_constant(pd.concat([d[cols],cal],axis=1));out=[];models=[];fits={}
def record(name,names,b,se,df,n,info,focal):
 for k,coef,err in zip(names,b,se):
  stat=coef/err;p=2*t.sf(abs(stat),df);out.append(dict(model=name,term=k,coefficient=float(coef),se=float(err),t=float(stat),p=float(p),n=n,focal=k in focal))
 models.append(dict(model=name,n=n,**info))
for y in ['deposits','withdrawals','net','deposits_rate','withdrawals_rate','net_rate']:
 g=d.loc['2025-01-16':];xx=X.loc[g.index];f=sm.OLS(g[y],xx).fit();fits[y]=f
 for bw in [7,14]:
  ff=f.get_robustcov_results(cov_type='HAC',maxlags=bw,use_correction=True,use_t=True);name=y+'_HAC'+str(bw);record(name,xx.columns,ff.params,ff.bse,ff.df_resid,len(g),{'r2':f.rsquared,'mean':g[y].mean(),'sd':g[y].std(),'bandwidth':bw},['utilization','premium'] if bw==7 else []);pd.DataFrame(ff.cov_params(),index=xx.columns,columns=xx.columns).to_csv(O/(name+'_cov.csv'))
identity=float(np.max(np.abs(fits['deposits'].params-fits['withdrawals'].params-fits['net'].params)));assert identity<1e-9
for h in [3,7]:
 y=sum(d.net.shift(-i) for i in range(h));g=d.loc['2025-01-16':].index;g=g[y.loc[g].notna()];f=sm.OLS(y.loc[g],X.loc[g]).fit()
 for bw in [7,14]:
  ff=f.get_robustcov_results(cov_type='HAC',maxlags=bw,use_correction=True,use_t=True);name=f'cum{h}_HAC{bw}';record(name,X.columns,ff.params,ff.bse,ff.df_resid,len(g),{'r2':f.rsquared,'mean':float(y.loc[g].mean()),'sd':float(y.loc[g].std()),'bandwidth':bw,'horizon':h},['utilization','premium'] if bw==7 else []);pd.DataFrame(ff.cov_params(),index=X.columns,columns=X.columns).to_csv(O/(name+'_cov.csv'))
# Leave-one-calendar-month-out stability of the full daily net-flow model.
loo=[]
for month in range(1,12):
 g=d.loc['2025-01-16':].index;g=g[g.month!=month];xx=X.loc[g];xx=xx.loc[:,xx.abs().sum().gt(0)];f=sm.OLS(d.loc[g,'net'],xx).fit().get_robustcov_results(cov_type='HAC',maxlags=7,use_correction=True,use_t=True);j=list(xx.columns).index('utilization');loo.append({'excluded_month':month,'coefficient':float(f.params[j]),'se':float(f.bse[j]),'p':float(f.pvalues[j]),'n':len(g)})
pd.DataFrame(loo).to_csv(O/'leave_month_out.csv',index=False);print('daily models complete',flush=True)
# Two-way FE heterogeneity, with all contemporaneous daily common shocks absorbed.
g=v[~v.spark & v.date.ge('2025-01-16') & v.prior_claim_usdc.ge(1)].copy();n0=len(g)
while True:
 keep=g.groupby('owner').owner.transform('size').gt(1)&g.groupby('date').date.transform('size').gt(1)
 if keep.all():break
 g=g[keep].copy()
g=g.merge(d[['utilization','premium','eth_return_pp','eth_volatility_pp']],left_on='date',right_index=True,validate='many_to_one');g['log_claim']=np.log(g.prior_claim_usdc);g['centered_size']=g.log_claim-np.log(1000)
names=['log_claim']
for k in ['utilization','premium','eth_return_pp','eth_volatility_pp']:g[k+'_size']=g[k]*g.centered_size;names.append(k+'_size')
ids,owners=pd.factorize(g.owner,sort=True);days,dates=pd.factorize(g.date,sort=True);G=len(owners);H=len(dates);N=len(g)
def subtract(a,idx,K):
 sums=np.column_stack([np.bincount(idx,weights=a[:,j],minlength=K) for j in range(a.shape[1])]);return a-sums[idx]/np.bincount(idx,minlength=K)[idx,None]
def absorb(a,i,j,I,J):
 z=a.copy()
 for it in range(2000):
  prev=z.copy();z=subtract(subtract(z,i,I),j,J)
  if np.max(np.abs(z-prev))<1e-10:return z,it+1
 raise AssertionError('FE did not converge')
# Bipartite connected-component count determines FE rank.
parent=np.arange(G+H)
def root(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
for i,j in zip(ids,days):
 a,b=root(i),root(G+j)
 if a!=b:parent[a]=b
components=len({root(i) for i in range(G+H)});fullk=G+H-components+len(names)
raw=np.column_stack([g[names].to_numpy(),100*g.withdraw_any.to_numpy(),100*g.deposit_any.to_numpy()]);w,it=absorb(raw,ids,days,G,H);xx=w[:,:len(names)];assert np.linalg.matrix_rank(xx)==len(names);bread=np.linalg.inv(xx.T@xx)
def meat(score,idx,K):
 z=np.column_stack([np.bincount(idx,weights=score[:,j],minlength=K) for j in range(score.shape[1])]);return z.T@z
for j,y in enumerate(['withdraw','deposit']):
 yy=w[:,len(names)+j];b=bread@(xx.T@yy);res=yy-xx@b;sc=xx*res[:,None];cov=bread@((G/(G-1)*meat(sc,ids,G)+H/(H-1)*meat(sc,days,H)-N/(N-1)*(sc.T@sc))*(N-1)/(N-fullk))@bread
 assert (np.diag(cov)>0).all();name='sizeFE_'+y;record(name,names,b,np.sqrt(np.diag(cov)),min(G,H)-1,N,{'owners':G,'dates':H,'components':components,'absorbed_parameters':fullk,'iterations':it,'singletons_removed':n0-N,'within_r2':1-res@res/(yy@yy),'negative_cov_eigenvalues':int((np.linalg.eigvalsh(cov)<-1e-10).sum()),'mean':float(100*g[y+'_any'].mean())},['utilization_size','premium_size']);pd.DataFrame(cov,index=names,columns=names).to_csv(O/(name+'_cov.csv'))
# Explicit-dummy check on 20 deterministic owners, including date effects.
z=g[g.owner.isin(owners[:20])].copy();ii,oo=pd.factorize(z.owner);jj,dd=pd.factorize(z.date);zr=np.column_stack([z[names],100*z.withdraw_any]);zw,_=absorb(zr,ii,jj,len(oo),len(dd));bw=np.linalg.lstsq(zw[:,:len(names)],zw[:,-1],rcond=None)[0];dummy=pd.concat([pd.get_dummies(z.owner,dtype=float),pd.get_dummies(z.date,dtype=float)],axis=1);be=np.linalg.lstsq(np.column_stack([z[names],dummy]),100*z.withdraw_any,rcond=None)[0][:len(names)];gap=float(np.max(np.abs(bw-be)));assert gap<1e-6,gap
r=pd.DataFrame(out);sel=r.focal;assert sel.sum()==20
r.loc[sel,'holm20']=multipletests(r.loc[sel,'p'],method='holm')[1];r.loc[sel,'bh20']=multipletests(r.loc[sel,'p'],method='fdr_bh')[1]
old=pd.read_csv(R/'reports/revision27/regression_results.csv');old=old[old.model.isin(['other_flow_HAC7','withdraw_any_cutoff1','deposit_any_cutoff1'])&old.term.isin(['premium','utilization'])];assert len(old)==6
allp=np.r_[r.loc[sel,'p'],old.p];r.loc[sel,'holm26']=multipletests(allp,method='holm')[1][:20];r.loc[sel,'bh26']=multipletests(allp,method='fdr_bh')[1][:20]
r['stars']=np.where(r.p<.01,'***',np.where(r.p<.05,'**',np.where(r.p<.1,'*','')));r.to_csv(O/'all_regressions.csv',index=False);r[sel].to_csv(O/'focal_results.csv',index=False);pd.concat([r[sel][['model','term','p']],old[['model','term','p']]]).to_csv(O/'search_family26.csv',index=False);(O/'models.json').write_text(json.dumps(models,indent=2));d.to_csv(O/'daily_analysis.csv');(O/'validation.json').write_text(json.dumps({'flow_identity_max_gap':identity,'two_way_FE_dummy_gap':gap,'FE_iterations':it,'extension_tests':20,'combined_tests':26,'design':'exploratory, retained inputs, no causal identification'},indent=2));print(r[sel][['model','term','coefficient','p','holm26','bh26']].to_string(index=False))
