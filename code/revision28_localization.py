"""Post-discovery stability checks specified in SENSITIVITY_AMENDMENT.md."""
from pathlib import Path
import pandas as pd,numpy as np,json
from scipy.stats import t
R=Path(__file__).resolve().parents[1];O=R/'reports/revision28';v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v.date=pd.to_datetime(v.date);d=pd.read_csv(R/'reports/revision27/estimation_daily_inputs.csv',parse_dates=['date']).set_index('date');v=v[~v.spark & v.date.ge('2025-01-16') & v.prior_claim_usdc.ge(1)].merge(d[['utilization','premium','eth_return_pp','eth_volatility_pp']],left_on='date',right_index=True);v['log_low']=np.minimum(np.log(v.prior_claim_usdc),np.log(100));v['log_high']=np.maximum(np.log(v.prior_claim_usdc)-np.log(100),0);names=['log_low','log_high']
for k in ['utilization','premium','eth_return_pp','eth_volatility_pp']:
 for segment in ['low','high']:v[k+'_'+segment]=v[k]*v['log_'+segment];names.append(k+'_'+segment)
def sub(a,ids,G):
 sums=np.column_stack([np.bincount(ids,weights=a[:,j],minlength=G) for j in range(a.shape[1])]);return a-sums[ids]/np.bincount(ids,minlength=G)[ids,None]
def meat(a,ids,G):
 sums=np.column_stack([np.bincount(ids,weights=a[:,j],minlength=G) for j in range(a.shape[1])]);return sums.T@sums
rows=[]
for tag in ['piecewise100']:
 g=v.copy()
 if tag=='exclude_ethena':g=g[g.owner.ne('0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c')]
 elif tag=='cutoff100':g=g[g.prior_claim_usdc.ge(100)]
 elif tag.startswith('exclude_month_'):g=g[g.date.dt.month.ne(int(tag.split('_')[-1]))]
 while True:
  keep=g.groupby('owner').owner.transform('size').gt(1)&g.groupby('date').date.transform('size').gt(1)
  if keep.all():break
  g=g[keep].copy()
 ids,owners=pd.factorize(g.owner);days,dates=pd.factorize(g.date);G=len(owners);H=len(dates);N=len(g);a=np.column_stack([g[names],100*g.deposit_any]);z=a.copy()
 for it in range(2000):
  prev=z.copy();z=sub(sub(z,ids,G),days,H)
  if np.max(abs(prev-z))<1e-10:break
 else:raise AssertionError('nonconvergence')
 # Verify all dates belong to one component via connected owner-date adjacency.
 connected={0}
 while True:
  seen=np.unique(ids[np.isin(days,list(connected))]);more=set(days[np.isin(ids,seen)])
  if more==connected:break
  connected=more
 assert len(connected)==H
 xx=z[:,:len(names)];yy=z[:,-1];assert np.linalg.matrix_rank(xx)==len(names);bread=np.linalg.inv(xx.T@xx);b=bread@(xx.T@yy);res=yy-xx@b;sc=xx*res[:,None];fullk=G+H-1+len(names);cov=bread@((G/(G-1)*meat(sc,ids,G)+H/(H-1)*meat(sc,days,H)-N/(N-1)*(sc.T@sc))*(N-1)/(N-fullk))@bread;assert (np.diag(cov)>0).all()
 for key in ['premium_low','premium_high','utilization_low','utilization_high','premium_difference','utilization_difference']:
  c=np.zeros(len(names))
  if key.endswith('difference'):
   k=key.split('_')[0];c[names.index(k+'_low')]=1;c[names.index(k+'_high')]=-1
  else:c[names.index(key)]=1
  coef=c@b;se=np.sqrt(c@cov@c);rows.append(dict(model=tag,term=key,coefficient=coef,se=se,t=coef/se,p=2*t.sf(abs(coef/se),min(G,H)-1),n=N,owners=G,dates=H,iterations=it+1,within_r2=1-res@res/(yy@yy)))
 pd.DataFrame(cov,index=names,columns=names).to_csv(O/'piecewise_cov.csv')
 pd.DataFrame({'term':names,'coefficient':b,'se':np.sqrt(np.diag(cov))}).to_csv(O/'piecewise_all_coefficients.csv',index=False)
pd.DataFrame(rows).to_csv(O/'piecewise_results.csv',index=False)
from statsmodels.stats.multitest import multipletests
old=pd.read_csv(O/'search_family26.csv');allresults=pd.concat([old,pd.DataFrame(rows)],ignore_index=True);allresults['holm32']=multipletests(allresults.p,method='holm')[1];allresults['bh32']=multipletests(allresults.p,method='fdr_bh')[1];assert len(allresults)==32;allresults.to_csv(O/'search_family32.csv',index=False);print(allresults.tail(6).to_string(index=False))
