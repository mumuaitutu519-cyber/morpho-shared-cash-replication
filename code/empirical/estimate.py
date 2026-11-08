"""Prespecified real-state regressions; no target coefficient calibration."""
from pathlib import Path
import json,itertools
import numpy as np,pandas as pd
from scipy import stats,sparse
import statsmodels.api as sm
R=Path(__file__).resolve().parents[2];O=R/'outputs/empirical'
results=[];meta=[];designchecks=[]
def groups(x):return pd.factorize(x,sort=True)[0]
def projector(g):
 n=len(g);ng=int(g.max())+1;B=sparse.csr_matrix((np.ones(n),(g,np.arange(n))),shape=(ng,n));cnt=np.bincount(g);return B,cnt

def demean(A,gs):
 A=np.asarray(A,dtype=float).copy();one=A.ndim==1
 if one:A=A[:,None]
 prs=[projector(g) for g in gs]
 for it in range(150):
  gap=0
  for g,(B,c) in zip(gs,prs):
   av=(B@A)/c[:,None];gap=max(gap,float(np.max(np.abs(av))));A-=av[g]
  if gap<1e-10:break
 assert gap<1e-8,(gap,it)
 return A[:,0] if one else A

def covariance(X,e,gs,rank):
 n,k=X.shape;bread=np.linalg.inv(X.T@X);scores=X*e[:,None];common=(n-1)/(n-rank);meats=[]
 for g in [gs[0],gs[1],groups(list(zip(*gs)))]:
  B,c=projector(g);s=B@scores;G=len(c);meats.append(G/(G-1)*(s.T@s))
 return bread@(common*(meats[0]+meats[1]-meats[2]))@bread

def wild_p(X,y,g,gs,j,rank):
 n,k=X.shape;Xr=np.delete(X,j,axis=1);br=np.linalg.lstsq(Xr,y,rcond=None)[0];er=y-Xr@br;fit=y-er
 G=int(g.max())+1;signs=np.array(list(itertools.product([-1.,1.],repeat=G))).T
 ys=demean(fit[:,None]+er[:,None]*signs[g],gs);bread=np.linalg.inv(X.T@X);bs=bread@X.T@ys;es=ys-X@bs
 # One-way studentized WCR test; same covariance is used for the observed statistic.
 a=X@bread[:,j];B,c=projector(g);cluster=B@(a[:,None]*es);fac=G/(G-1)*(n-1)/(n-rank);ses=np.sqrt(fac*np.sum(cluster**2,axis=0));ts=np.divide(bs[j],ses,out=np.zeros_like(ses),where=ses>0)
 b=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@b;cl=B@(a*e);se=np.sqrt(fac*np.sum(cl**2));
 if se<1e-14:return None
 obs=b[j]/se
 return float(np.mean(np.abs(ts)>=abs(obs)-1e-10))

def fit_fe(name,df,yname,xnames,entity='vault',boot=()):
 z=df.replace([np.inf,-np.inf],np.nan).dropna(subset=[yname]+xnames+[entity,'date']).copy();z=z.sort_values([entity,'date']);gs=[groups(z[entity]),groups(z.date)];X0=z[xnames].to_numpy(float);y0=z[yname].to_numpy(float);XY=demean(np.column_stack([y0,X0]),gs);y=XY[:,0];X=XY[:,1:]
 keep=np.sqrt(np.sum(X*X,axis=0))>1e-9;absorbed=[s for s,b in zip(xnames,keep) if not b];xnames=[s for s,b in zip(xnames,keep) if b];X=X[:,keep];X0=X0[:,keep]
 assert np.linalg.matrix_rank(X)==X.shape[1],name
 b=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@b;n=len(y);rank=X.shape[1]+len(set(gs[0]))+len(set(gs[1]))-1;cov=covariance(X,e,gs,rank);diag=np.diag(cov);se=np.sqrt(np.where(diag>=0,diag,np.nan));dfree=min(len(set(gs[0])),len(set(gs[1])))-1;pv=2*stats.t.sf(np.abs(b/se),dfree)
 # Residuals agree with full fixed-effect fitted values, so y0-e is the in-sample score.
 score=y0-e;binary=set(np.unique(y0))<={0.,100.};auc=None
 if binary and 0<(y0>0).sum()<n:
  n1=(y0>0).sum();n0=n-n1;auc=float((stats.rankdata(score)[y0>0].sum()-n1*(n1+1)/2)/(n1*n0))
 for j,t in enumerate(xnames):
  wp=wild_p(X,y,gs[0],gs,j,rank) if t in boot else None
  results.append({'model':name,'term':t,'coef':float(b[j]),'se':float(se[j]) if np.isfinite(se[j]) else None,'p':float(pv[j]) if np.isfinite(pv[j]) else None,'wild_p':wp,'N':n})
 info={'model':name,'N':n,'entities':len(set(gs[0])),'dates':len(set(gs[1])),'first':z.date.min(),'last':z.date.max(),'within_R2':float(1-e@e/(y@y)) if y@y>0 else None,'outcome_mean':float(y0.mean()),'auc':auc,'absorbed':absorbed,'covariance_diagonal_nonpositive':[xnames[j] for j,x in enumerate(diag) if x<=0],'clusters':[entity,'date'],'rank_with_fe':rank,'excluded_rows':len(df)-n};meta.append(info);designchecks.append({'model':name,'X_rank':int(np.linalg.matrix_rank(X)),'columns':len(xnames),'max_group_mean_residual':max(float(np.max(np.abs((projector(g)[0]@e)/projector(g)[1]))) for g in gs)})
 return z,X,y,b,e

def save():
 pd.DataFrame(results).to_csv(O/'regressions.csv',index=False);(O/'models.json').write_text(json.dumps(meta,indent=2));(O/'design_checks.json').write_text(json.dumps(designchecks,indent=2))

if __name__=='__main__':
 p=pd.read_parquet(O/'vault_panel.parquet');p=p[~p.date.str.startswith('snapshot')].sort_values(['vault','date']).copy();assert p.date.nunique()==440
 for f in [5,10,25]:
  p['Y'+str(f)]=(p.capacity*100 < p.assets*f).astype(float)*100;p['leadY'+str(f)]=p.groupby('vault')['Y'+str(f)].shift(-1)
 p['log_W']=np.log(p.capacity.where(p.capacity>0)/1e6);p['log_cash']=np.log(p.own_cash.where(p.own_cash>0));p['dlog_W']=p.groupby('vault').log_W.diff();p['dlog_cash']=p.groupby('vault').log_cash.diff()
 for col in ['D','log_assets']:p['lag_'+col]=p.groupby('vault')[col].shift(1)
 p['interaction']=p.dlog_cash*p.lag_D
 a=p[p.date.ge('2025-01-16')].copy();a.to_parquet(O/'estimation_panel.parquet',index=False)
 # II A: daily levels, lag predictors. Year-month and weekday effects.
 d=pd.read_csv(O/'daily.csv');d=d[~d.date.str.startswith('snapshot')].sort_values('date');d['log_total_assets']=np.log(d.assets)
 for col in ['cash_hhi','log_total_assets','utilization10']:d['L_'+col]=d[col].shift(1)
 d=d[d.date.ge('2025-01-16')].copy();terms=['L_cash_hhi','L_log_total_assets','L_utilization10'];dates=pd.to_datetime(d.date);F=pd.get_dummies(pd.DataFrame({'month':dates.dt.strftime('%Y-%m'),'weekday':dates.dt.dayofweek.astype(str)}),drop_first=True,dtype=float);X=sm.add_constant(pd.concat([d[terms].reset_index(drop=True),F.reset_index(drop=True)],axis=1));m=sm.OLS(d.duplication.to_numpy(),X).fit(cov_type='HAC',cov_kwds={'maxlags':7,'use_correction':True},use_t=True)
 for t in terms:results.append({'model':'II_A','term':t,'coef':float(m.params[t]),'se':float(m.bse[t]),'p':float(m.pvalues[t]),'wild_p':None,'N':int(m.nobs)})
 meta.append({'model':'II_A','N':int(m.nobs),'R2':float(m.rsquared),'first':d.date.min(),'last':d.date.max(),'covariance':'HAC7','outcome_mean':float(d.duplication.mean())})
 fit_fe('II_B',a,'D',['shared_exposure','log_assets','active_markets'],boot=['shared_exposure'])
 # III: predictor dates start Jan 16; outcomes must exist on the immediately following day.
 for f in [5,10,25]:
  y='leadY'+str(f)
  fit_fe('III_A_'+str(f),a,y,['D10','log_assets','utilization10'],boot=['D10'])
  fit_fe('III_B_coverage_'+str(f),a,y,['coverage10','log_assets','utilization10'],boot=['coverage10'])
  fit_fe('III_B_both_'+str(f),a,y,['D10','coverage10','log_assets','utilization10'],boot=['D10','coverage10'])
 # Diagnostics: additional own cash level, leave-focal-out network rate, FWL residualized exposure, nonheld-market placebo.
 a['log_own_cash']=np.log(a.own_cash.where(a.own_cash>0))
 fit_fe('III_C_own',a,'leadY25',['D10','log_assets','utilization10','log_own_cash'],boot=['D10'])
 fit_fe('III_C_peer',a,'leadY25',['peerD10','log_assets','utilization10'],boot=['peerD10'])
 z,X,y,b,e=fit_fe('D_residualization',a,'D10',['log_assets','utilization10'])
 a['residual_D10']=np.nan;a.loc[z.index,'residual_D10']=e
 fit_fe('III_C_residual',a,'leadY25',['residual_D10','log_assets','utilization10'],boot=['residual_D10'])
 fit_fe('III_C_placebo',a,'leadY25',['placebo10','log_assets','utilization10'],boot=['placebo10'])
 fit_fe('IV_A',a,'dlog_W',['dlog_cash','interaction','lag_D','lag_log_assets'],boot=['interaction'])
 save();print('Vault regressions complete',flush=True)
 # Pair panel: exact 30-day window, 30 valid daily changes; no earlier returns are manufactured.
 pos=pd.read_parquet(O/'positions.parquet');pos=pos[~pos.date.str.startswith('snapshot')];P=pos.pivot_table(index=['date','vault'],columns='market',values='position',aggfunc='sum',fill_value=0);ms=pos.groupby(['date','market'])[['market_supply','market_borrow']].first();vs=sorted(a.vault.unique());parts=[]
 for u,v in itertools.combinations(vs,2):
  U=a[a.vault==u].set_index('date');V=a[a.vault==v].set_index('date');dates=U.index.intersection(V.index);du=U.loc[dates,'dlog_W'];dv=V.loc[dates,'dlog_W'];co=du.rolling(30,min_periods=30).corr(dv);valid=du.notna().astype(int).rolling(30,min_periods=30).sum().eq(30)&dv.notna().astype(int).rolling(30,min_periods=30).sum().eq(30);co=co.where(valid & (co.abs()<1-1e-12));fisher=np.arctanh(co)
  for day in dates:
   pu=P.loc[(day,u)];pv=P.loc[(day,v)];shared=(pu>0)&(pv>0);weights=pu+pv;den=weights.sum();exp=weights[shared].sum()/den if den else np.nan;am=ms.loc[day].reindex(P.columns);util=(weights[shared]*(am.market_borrow/am.market_supply)[shared]).sum()/weights[shared].sum() if weights[shared].sum()>0 else np.nan
   au=U.loc[day,'assets'];av=V.loc[day,'assets'];parts.append({'pair':u+'_'+v,'date':day,'fisher_z':fisher.loc[day],'correlation':co.loc[day],'overlap':exp,'size_similarity':min(au,av)/max(au,av) if max(au,av)>0 else np.nan,'shared_utilization':util,'valid_window':bool(valid.loc[day])})
 pairs=pd.DataFrame(parts);pairs.to_parquet(O/'pair_panel.parquet',index=False);fit_fe('IV_B',pairs,'fisher_z',['overlap','size_similarity','shared_utilization'],entity='pair');save()
 # Descriptives on the same primary historical panel; both full-state and lead-outcome samples are explicit.
 a[['D','coverage10','log_assets','utilization10','capacity','assets','Y5','Y10','Y25']].describe(percentiles=[.25,.5,.75]).T.to_csv(O/'descriptives.csv');print(json.dumps(meta,indent=2),flush=True)
