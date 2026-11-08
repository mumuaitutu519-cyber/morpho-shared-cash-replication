"""Reusable requested inference, explicit FE ranks and recorded sample exclusions."""
from pathlib import Path
import sys,json,itertools
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats,sparse
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';O=P/'outputs'
sys.path.insert(0,str(R/'code/empirical'));from estimate import groups,demean,projector,covariance
ROWS=[];META=[];TESTS=[]
def ferank(z,fe):
 if not fe:return 1
 # Bipartite FE connected components avoid overcounting disconnected chains.
 if len(fe)==1:return z[fe[0]].nunique()
 assert len(fe)==2
 u=groups(z[fe[0]]);v=groups(z[fe[1]]);nu=max(u)+1;nv=max(v)+1
 G=sparse.coo_matrix((np.ones(2*len(z)),(np.r_[u,nu+v],np.r_[nu+v,u])),shape=(nu+nv,nu+nv)).tocsr()
 nc=sparse.csgraph.connected_components(G,directed=False,return_labels=False)
 return nu+nv-nc
def emit(model,spec,variables,b,cov,df,covname,wild=None):
 diag=np.diag(cov);se=np.sqrt(np.where(diag>=0,diag,np.nan));t=b/se;p=2*stats.t.sf(abs(t),df)
 for j,var in enumerate(variables):ROWS.append(dict(model=model,spec=spec,variable=var,coefficient=b[j],standard_error=se[j],t_statistic=t[j],p_value=p[j],covariance=covname,wild_cluster_p=np.nan if wild is None else wild[j]))
def wild9999(X,y,gs,g,j,rank):
 n=len(y);G=max(g)+1;B,_=projector(g);bread=np.linalg.inv(X.T@X);a=X@bread[:,j];fac=G/(G-1)*(n-1)/(n-rank)
 b=bread@X.T@y;e=y-X@b;obs=b[j]/np.sqrt(fac*np.sum((B@(a*e))**2))
 Xr=np.delete(X,j,axis=1);er=y-Xr@np.linalg.lstsq(Xr,y,rcond=None)[0];fit=y-er;signs=np.random.default_rng(20261003).choice([-1.,1.],size=(G,9999));nex=0
 for k in range(0,9999,256):
  raw=fit[:,None]+er[:,None]*signs[g,k:k+256];ys=demean(raw,gs) if gs else raw;bb=bread@X.T@ys;ee=ys-X@bb;ses=np.sqrt(fac*np.sum((B@(a[:,None]*ee))**2,axis=0));nex+=np.sum(abs(bb[j]/ses)>=abs(obs)-1e-10)
 return (nex+1)/10000

def fit(model,spec,data,yname,terms,fe,clusters,dk=False,wild=False,test_equal=None):
 z=data.replace([np.inf,-np.inf],np.nan).dropna(subset=[yname]+terms+fe+clusters).copy();n=len(z);gs=[groups(z[f]) for f in fe]
 xy=z[[yname]+terms].to_numpy(float);prescale=np.maximum(np.sqrt(np.mean(xy*xy,axis=0)),1.) if np.max(np.abs(xy))>1e8 else np.ones(xy.shape[1]);xy=xy/prescale;xy=demean(xy,gs) if gs else xy-np.mean(xy,axis=0);y=xy[:,0];X=xy[:,1:];keep=np.linalg.norm(X,axis=0)>1e-9;absorbed=[t for t,k in zip(terms,keep) if not k];terms=[t for t,k in zip(terms,keep) if k];X=X[:,keep];scale=np.sqrt(np.mean(X*X,axis=0));X=X/scale;conversion=prescale[0]/prescale[1:][keep]/scale;assert np.linalg.matrix_rank(X)==len(terms),(model,spec,terms)
 rank=ferank(z,fe)+len(terms);b=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@b;bread=np.linalg.inv(X.T@X);cg=[groups(z[c]) for c in clusters];df=min(max(g)+1 for g in cg)-1
 if len(cg)==2:cv=covariance(X,e,cg,rank)
 else:
  g=cg[0];G=max(g)+1;sc=projector(g)[0]@(X*e[:,None]);cv=bread@(sc.T@sc)@bread*G/(G-1)*(n-1)/(n-rank)
 wp=[wild9999(X,y,gs,cg[0],j,rank) for j in range(len(terms))] if wild else None
 b=b*conversion;cv=cv*np.outer(conversion,conversion)
 emit(model,spec,terms,b,cv,df,'cluster:'+','.join(clusters),wp)
 info=dict(model=model,spec=spec,Obs=n,eligible=len(data),dropped=len(data)-n,FE=' + '.join(fe) or 'none',clusters=';'.join(f'{c}:{z[c].nunique()}' for c in clusters),df_p=df,rank=rank,within_R2=1-e@e/(y@y),outcome_mean=z[yname].mean(),absorbed=';'.join(absorbed),wild_draws=9999 if wild else 0);META.append(info)
 if test_equal:
  a=np.zeros(len(terms));a[terms.index(test_equal[0])]=1;a[terms.index(test_equal[1])]=-1;se=np.sqrt(a@cv@a);TESTS.append(dict(model=model,spec=spec,test=' = '.join(test_equal),difference=float(a@b),standard_error=se,t_statistic=(a@b)/se,p_value=2*stats.t.sf(abs((a@b)/se),df),covariance='cluster'))
 if dk:
  dg=groups(z.date);sc=projector(dg)[0]@(X*e[:,None]);observed=sorted(z.date.unique());calendar=pd.date_range(min(observed),max(observed)).strftime('%Y-%m-%d');sc=pd.DataFrame(sc,index=observed).reindex(calendar,fill_value=0).to_numpy();meat=sc.T@sc
  for lag in range(1,6):cross=sc[lag:].T@sc[:-lag];meat+=(1-lag/6)*(cross+cross.T)
  dc=bread@meat@bread*n/(n-rank)*np.outer(conversion,conversion);emit(model,spec,terms,b,dc,z.date.nunique()-1,'Driscoll-Kraay5')
  if test_equal:
   se=np.sqrt(a@dc@a);TESTS.append(dict(model=model,spec=spec,test=' = '.join(test_equal),difference=float(a@b),standard_error=se,t_statistic=(a@b)/se,p_value=2*stats.t.sf(abs((a@b)/se),z.date.nunique()-1),covariance='Driscoll-Kraay5'))
 return z,X,y,b,e

def save(prefix):
 r=pd.DataFrame(ROWS);m=pd.DataFrame(META);r.to_csv(O/f'{prefix}_numeric.csv',index=False,float_format='%.15g');m.to_csv(O/f'{prefix}_models.csv',index=False,float_format='%.15g');pd.DataFrame(TESTS).to_csv(O/f'{prefix}_tests.csv',index=False,float_format='%.15g')
 columns={}
 for (model,spec),z in r.groupby(['model','spec'],sort=False):
  d={};main=z[~z.covariance.eq('Driscoll-Kraay5')]
  for x in main.itertuples():
   star='***' if x.p_value<.01 else '**' if x.p_value<.05 else '*' if x.p_value<.1 else '';d[x.variable]=(f'{x.coefficient:.3e}' if 0<abs(x.coefficient)<5e-7 else f'{x.coefficient:.6f}')+star;d[x.variable+' t']=f'({x.t_statistic:.2f})'
   if np.isfinite(x.wild_cluster_p):d[x.variable+' wild p']=f'{x.wild_cluster_p:.6f}'
  for x in z[z.covariance.eq('Driscoll-Kraay5')].itertuples():d[x.variable+' DK t']=f'({x.t_statistic:.2f})'
  mm=m[(m.model==model)&(m.spec==spec)].iloc[0]
  for f in ['date','month','weekday','chain_state','market','chain','pair']:
   d[{'pair':'Event-pair','month':'Year-month','weekday':'Weekday','chain_state':'Chain-by-state','entity':'Vault','vault':'Vault','date':'Date','market':'Market','chain':'Chain'}.get(f,f)+' FE']='Yes' if f in mm.FE.split(' + ') else 'No'
  d['Vault FE']='Yes' if any(f in mm.FE.split(' + ') for f in ['vault','entity']) else 'No'
  for key in ['Obs','clusters','within_R2','R2','pseudo_R2','outcome_mean']:
   if key in mm and pd.notna(mm[key]):d[{'Obs':'Obs.','clusters':'Clusters','within_R2':'Within R-squared','R2':'R-squared','pseudo_R2':'Pseudo R-squared','outcome_mean':'Outcome mean'}.get(key,key)]=int(mm[key]) if key=='Obs' else mm[key]
  for test in TESTS:
   if test['model']==model and test['spec']==spec:d['p('+test['test']+') '+test['covariance']]=test['p_value']
  columns[model+' / '+spec]=d
 pd.DataFrame(columns).rename_axis('row').to_csv(O/f'{prefix}_paper.csv')

def logit_wclr(X,y,g,j,observed_t):
 """Restricted WCLR-C, MacKinnon/Nielsen/Webb (2024), equations 26-30,37-38."""
 X=np.asarray(X,float);y=np.asarray(y,float);n,k=X.shape;scale=np.sqrt(np.mean(X*X,axis=0));Xs=X/scale;Xr=np.delete(Xs,j,axis=1)
 null=sm.Logit(y,Xr).fit(disp=False,maxiter=500);assert null.mle_retvals['converged'];pr=null.predict();weights=pr*(1-pr);G=max(g)+1;score=[];information=[]
 for h in range(G):
  mask=g==h;xx=Xs[mask];score.append(xx.T@(y[mask]-pr[mask]));information.append(xx.T@(weights[mask,None]*xx))
 score=np.array(score);information=np.array(information);bread=np.linalg.inv(information.sum(axis=0));signs=np.random.default_rng(20261003).choice([-1.,1.],size=(G,9999));bstar=bread@score.T@signs;direction=bread[j];factor=G/(G-1)*(n-1)/(n-k);cluster_influence=np.empty((G,9999))
 for h in range(G):cluster_influence[h]=direction@(score[h,:,None]*signs[h]-information[h]@bstar)
 se=np.sqrt(factor*np.sum(cluster_influence**2,axis=0));tstar=bstar[j]/se;return (1+np.sum(abs(tstar)>=abs(observed_t)-1e-10))/10000
