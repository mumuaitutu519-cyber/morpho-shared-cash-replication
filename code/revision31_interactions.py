from pathlib import Path
import pandas as pd,numpy as np,json,hashlib
from scipy.stats import t as tdist
from statsmodels.stats.multitest import multipletests
R=Path(__file__).resolve().parents[1];O=R/'reports/revision31';S='0x2917956eff0b5eaf030abdb4ef4296df775009ca';E='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c'
cache=O/'hourly_inputs.csv'
if not cache.exists():
 m=pd.read_parquet(R/'reports/revision29/market_cash_sequence.parquet').sort_values(['block','log_index']);v=pd.read_parquet(R/'reports/revision5/vault_economic_events.parquet');v=v[v.type.isin(['Deposit','Withdraw'])].copy();v['hour']=pd.to_datetime(v.timestamp,unit='s',utc=True).dt.floor('h');v['group']=np.where(v.onBehalf.eq(S),'treasury_',np.where(v.onBehalf.eq(E),'ethena_','others_'))+v.type
 idx=pd.date_range('2025-01-16','2025-11-30 23:00',freq='h',tz='UTC');d=v.groupby(['hour','group']).assets_raw.sum().unstack(fill_value=0).reindex(idx,fill_value=0)/1e12
 for k in ['treasury_Deposit','treasury_Withdraw','ethena_Deposit','ethena_Withdraw','others_Deposit','others_Withdraw']:
  if k not in d:d[k]=0.
 stamps=np.array([int(x.timestamp()) for x in idx],dtype=np.int64);ix=np.searchsorted(m.timestamp.to_numpy(),stamps,side='left')-1;d['opening_cash']=np.where(ix>=0,m.cash_after_raw.to_numpy()[np.maximum(ix,0)],int(m.cash_before_raw.iloc[0]))/1e12
 m['hour']=pd.to_datetime(m.timestamp,unit='s',utc=True).dt.floor('h');flows=m.groupby(['hour','type']).assets_raw.sum().unstack(fill_value=0).reindex(idx,fill_value=0)/1e12;d['borrow']=flows.Borrow;d['repay']=flows.Repay+flows.Liquidation
 assert d.opening_cash.nunique()>100
 d['other_W']=d.others_Withdraw+d.ethena_Withdraw;d['other_D']=d.others_Deposit+d.ethena_Deposit;d['net']=d.treasury_Deposit-d.treasury_Withdraw
 for h in [1,6]:
  for y,src in [('deposit','treasury_Deposit'),('net','net')]:d[f'{y}_{h}h']=sum(d[src].shift(-j) for j in range(1,h+1))
 d.index.name='hour';d.to_csv(cache)
else:d=pd.read_csv(cache,parse_dates=['hour']).set_index('hour')
g=d.dropna().copy();assert len(d)==319*24 and len(g)==len(d)-6;raw=-np.log1p(g.opening_cash);g['tightness']=(raw-raw.mean())/raw.std();g['interaction']=g.other_W*g.tightness
names=['other_W','tightness','interaction','other_D','borrow','repay','treasury_Deposit','treasury_Withdraw'];results=[];foc=[];diag=[];models=[];marg=[]
def absorb(a,day,hour):
 for it in range(1000):
  prev=a.copy()
  for ids in [day,hour]:
   n=np.bincount(ids);means=np.column_stack([np.bincount(ids,weights=a[:,k])/n for k in range(a.shape[1])]);a-=means[ids]
  if np.max(abs(a-prev))<1e-10:return a,it+1
 raise AssertionError('absorption failed')
def fit(z,ys,bw=24,extra=False):
 cols=names+(['ethena_Withdraw'] if extra else []);day,_=pd.factorize(z.index.date);hour=z.index.hour.to_numpy();present=np.unique(hour);hour=np.searchsorted(present,hour);Y=z[ys].to_numpy();A,it=absorb(np.column_stack([z[cols].to_numpy(),Y]),day,hour);X=A[:,:len(cols)];Y=A[:,len(cols):];assert np.linalg.matrix_rank(X)==len(cols);bread=np.linalg.inv(X.T@X);B=bread@X.T@Y;n=len(z);k=len(cols)+len(np.unique(day))+len(present)-1;df=n-k;ans=[]
 # Insert omitted calendar hours as zero scores so HAC lags remain clock-time lags.
 clock=((z.index-z.index[0]).total_seconds()/3600).astype(int);T=int(clock[-1])+1
 for j,y in enumerate(ys):
  b=B[:,j];u=Y[:,j]-X@b;score=np.zeros((T,len(cols)));score[clock]=X*u[:,None];meat=score.T@score
  for lag in range(1,min(bw,T-1)+1):
   cross=score[lag:].T@score[:-lag];meat+=(1-lag/(bw+1))*(cross+cross.T)
  cov=bread@meat@bread*n/df;se=np.sqrt(np.diag(cov));p=2*tdist.sf(abs(b/se),df);ans.append((b,se,p,cov,cols,df,1-u@u/(Y[:,j]@Y[:,j])))
 return ans,it
ys=['deposit_1h','net_1h','deposit_6h','net_6h']
for bw in [24,168]:
 fits,it=fit(g,ys,bw)
 for y,(b,se,p,cov,cols,df,r2) in zip(ys,fits):
  model=f'{y}_HAC{bw}';models.append({'model':model,'n':len(g),'df':df,'within_r2':r2,'iterations':it,'outcome_mean':float(g[y].mean())})
  for k,v,s,prob in zip(cols,b,se,p):results.append({'model':model,'term':k,'coefficient':v,'se':s,'p':prob,'n':len(g)})
  if bw==24:
   foc.append({'model':model,'p':p[2]});pd.DataFrame(cov,index=cols,columns=cols).to_csv(O/f'{model}_cov.csv')
   for label,q in [('q25',g.tightness.quantile(.25)),('q75',g.tightness.quantile(.75))]:
    c=np.zeros(len(cols));c[0]=1;c[2]=q;v=c@b;s=np.sqrt(c@cov@c);marg.append({'model':model,'tightness':label,'z':q,'slope':v,'se':s,'p':2*tdist.sf(abs(v/s),df)})
# Fixed sensitivity checks, executed regardless of primary results.
for kind in ['exclude_oct4_5','exclude_ethena']+[f'exclude_month_{i}' for i in range(1,12)]:
 z=g.copy();extra=kind=='exclude_ethena'
 if extra:z['other_W']=z.others_Withdraw;z['interaction']=z.other_W*z.tightness
 elif kind=='exclude_oct4_5':
  bad=pd.DatetimeIndex(['2025-10-04','2025-10-05']).date;keep=np.ones(len(z),dtype=bool)
  for h in range(7):keep&=~np.isin((z.index+pd.Timedelta(hours=h)).date,bad)
  z=z[keep]
 else:
  mon=int(kind.rsplit('_',1)[1]);keep=np.ones(len(z),dtype=bool)
  for h in range(7):keep&=(z.index+pd.Timedelta(hours=h)).month!=mon
  z=z[keep]
 fits,_=fit(z,ys[:2],24,extra)
 for y,(b,se,p,cov,cols,df,r2) in zip(ys[:2],fits):diag.append({'diagnostic':kind,'outcome':y,'interaction':b[2],'se':se[2],'p':p[2],'withdrawal_slope_at_mean_tightness':b[0],'withdrawal_slope_p':p[0],'n':len(z)})
f=pd.DataFrame(foc);f['holm4']=multipletests(f.p,method='holm')[1];old=pd.read_csv(R/'reports/revision28/search_family32.csv');f['holm36']=multipletests(np.r_[old.p,f.p],method='holm')[1][-4:]
pd.DataFrame(results).to_csv(O/'all_coefficients.csv',index=False);f.to_csv(O/'focal_tests.csv',index=False);pd.DataFrame(diag).to_csv(O/'influence_checks.csv',index=False);pd.DataFrame(marg).to_csv(O/'marginal_slopes.csv',index=False);(O/'models.json').write_text(json.dumps(models,indent=2));g.to_csv(O/'analysis_sample.csv')
# Explicit dummy check on the full sample (early two-week subsample is rank deficient).
z=g;day=pd.get_dummies(z.index.date,dtype=float).to_numpy();hr=pd.get_dummies(z.index.hour,dtype=float).to_numpy();X=np.column_stack([z[names],day,hr]);bb=np.linalg.lstsq(X,z.deposit_1h,rcond=None)[0][:len(names)];ff,_=fit(z,['deposit_1h']);gap=float(max(abs(bb-ff[0][0])));assert gap<1e-7,gap
summ={'sample_hours':len(g),'calendar_days':len(set(g.index.date)),'zero_other_withdrawal_hours':int(g.other_W.eq(0).sum()),'opening_cash_quartiles_million':g.opening_cash.quantile([.25,.5,.75]).to_dict(),'withdrawal_quartiles_million':g.other_W.quantile([.25,.5,.75,.99]).to_dict(),'other_withdrawals_total_million':g.other_W.sum(),'explicit_dummy_coefficient_gap':gap,'all_main_designs_identical':True,'main_focal_tests':4,'prior_recorded_tests':len(old)};(O/'validation.json').write_text(json.dumps(summ,indent=2));print(f.to_string(index=False));print(pd.DataFrame(results).query("term=='interaction'").to_string(index=False));print(pd.DataFrame(diag).to_string(index=False));print(json.dumps(summ,indent=2))
