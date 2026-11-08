"""Post-discovery stability checks specified in SENSITIVITY_AMENDMENT.md."""
from pathlib import Path
import pandas as pd,numpy as np,json
from scipy.stats import t
R=Path(__file__).resolve().parents[1];O=R/'reports/revision28';v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v.date=pd.to_datetime(v.date);d=pd.read_csv(R/'reports/revision27/estimation_daily_inputs.csv',parse_dates=['date']).set_index('date');v=v[~v.spark & v.date.ge('2025-01-16') & v.prior_claim_usdc.ge(1)].merge(d[['utilization','premium','eth_return_pp','eth_volatility_pp']],left_on='date',right_index=True);v['log_claim']=np.log(v.prior_claim_usdc);names=['log_claim']
for k in ['utilization','premium','eth_return_pp','eth_volatility_pp']:v[k+'_size']=v[k]*(v.log_claim-np.log(1000));names.append(k+'_size')
def sub(a,ids,G):
 sums=np.column_stack([np.bincount(ids,weights=a[:,j],minlength=G) for j in range(a.shape[1])]);return a-sums[ids]/np.bincount(ids,minlength=G)[ids,None]
def meat(a,ids,G):
 sums=np.column_stack([np.bincount(ids,weights=a[:,j],minlength=G) for j in range(a.shape[1])]);return sums.T@sums
rows=[]
for tag in ['exclude_ethena','cutoff100']+[f'exclude_month_{m}' for m in range(1,12)]:
 g=v.copy()
 if tag=='exclude_ethena':g=g[g.owner.ne('0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c')]
 elif tag=='cutoff100':g=g[g.prior_claim_usdc.ge(100)]
 else:g=g[g.date.dt.month.ne(int(tag.split('_')[-1]))]
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
 for key in ['premium_size','utilization_size']:
  j=names.index(key);se=np.sqrt(cov[j,j]);rows.append(dict(spec=tag,term=key,coefficient=b[j],se=se,p=2*t.sf(abs(b[j]/se),min(G,H)-1),n=N,owners=G,dates=H,iterations=it+1))
 print(tag,rows[-2],flush=True)
pd.DataFrame(rows).to_csv(O/'size_sensitivity.csv',index=False)
