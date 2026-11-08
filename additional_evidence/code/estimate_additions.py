"""Three requested exercises using observed frozen inputs. Run offline after fetch_spark_lag.py."""
from pathlib import Path
import sys,json,sqlite3,itertools,hashlib
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats
A=Path(__file__).resolve().parents[1];R=A.parent;O=A/'outputs';O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'code/empirical'));from estimate import groups,demean,covariance,projector
rows=[];meta=[];checks=[]
def emit(model,spec,var,b,se,p,wp=np.nan):
 rows.append(dict(model=model,spec=spec,variable=var,coefficient=b,standard_error=se,t_statistic=b/se if se>0 else np.nan,p_value=p,wild_cluster_p=wp))
def save():
 z=pd.DataFrame(rows);z.to_csv(O/'regressions.csv',index=False,float_format='%.12g')
 for m in z.model.unique():z[z.model==m].to_csv(O/f'{m}.csv',index=False,float_format='%.12g')
 pd.DataFrame(meta).to_csv(O/'model_metadata.csv',index=False,float_format='%.12g');(O/'estimation_checks.json').write_text(json.dumps(checks,indent=2))
# 1. Exact archived cohort; amounts converted from integer micro-USDC to million USDC.
p=pd.read_csv(R/'enrichment/outputs/peer_event_panel.csv',dtype={'shares_raw':str,'shares_raw_before':str});assert len(p)==495 and p.tx.nunique()==93
p['gap_micro']=[max(int(a)-int(w),0) for a,w in zip(p.claim_micro_before,p.capacity_micro_before)]
p['formula_million']=[min(int(d),int(g))/1e12 for d,g in zip(p.deposit_micro,p.gap_micro)]
p['delta_million']=[(int(a)-int(b))/1e12 for a,b in zip(p.capacity_micro,p.capacity_micro_before)]
assert (p.gap_micro>0).sum()==17
p.to_csv(O/'mechanism_observations.csv',index=False)
p.loc[p.gap_micro>0,['formula_million','delta_million']].to_csv(O/'mechanism_scatter.csv',index=False,float_format='%.12g')
for spec in ['a_pooled','b_transaction_FE','c_constrained','d_constrained_from_2025_04_23']:
 z=p.copy()
 if spec.startswith(('c_','d_')):z=z[z.gap_micro>0]
 if spec.startswith('d_'):z=z[z.date>='2025-04-23']
 g=groups(z.tx);G=len(set(g));n=len(z);y=z.delta_million.to_numpy();x=z.formula_million.to_numpy()
 if spec.startswith('b_'):
  xy=demean(np.column_stack([y,x]),[g]);yd=xy[:,0];xd=xy[:,1,None];b=np.linalg.lstsq(xd,yd,rcond=None)[0];e=yd-xd@b;rank=G+1
  sc=projector(g)[0]@(xd*e[:,None]);cov=np.linalg.inv(xd.T@xd)@(sc.T@sc)*G/(G-1)*(n-1)/(n-rank)@np.linalg.inv(xd.T@xd)
  se=float(np.sqrt(cov[0,0]));slope=float(b[0]);pv=float(2*stats.t.sf(abs(slope/se),G-1));p1=float(2*stats.t.sf(abs((slope-1)/se),G-1));p0=np.nan
  emit('mechanism',spec,'min_deposit_opening_gap',slope,se,pv);r2=1-e@e/((y-y.mean())@(y-y.mean()));wr2=1-e@e/(yd@yd)
 else:
  X=sm.add_constant(x);m=sm.OLS(y,X).fit(cov_type='cluster',cov_kwds={'groups':g,'use_correction':True,'df_correction':True},use_t=True)
  for j,var in enumerate(['intercept','min_deposit_opening_gap']):emit('mechanism',spec,var,float(m.params[j]),float(m.bse[j]),float(m.pvalues[j]))
  p1=float(2*stats.t.sf(abs((m.params[1]-1)/m.bse[1]),G-1));p0=float(m.pvalues[0]);r2=m.rsquared;wr2=np.nan
 meta.append(dict(model='mechanism',spec=spec,Obs=n,R2=r2,within_R2=wr2,clusters_entity=G,clusters_date=np.nan,df_p=G-1,FE='transaction' if spec.startswith('b_') else 'none',covariance='transaction cluster CR1',slope_equals_one_p=p1,intercept_equals_zero_p=p0,first=z.date.min(),last=z.date.max()))
checks.append(dict(check='mechanism_cohort',N=len(p),transactions=p.tx.nunique(),constrained=int((p.gap_micro>0).sum()),pre_Apr23_constrained=int(((p.gap_micro>0)&(p.date<'2025-04-23')).sum())))
save();print('mechanism complete',flush=True)
# 2. Committed Spark ERC4626 net flows, not underlying market reallocations.
spark='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
flowfile=A/'raw/spark_committed_flows.csv.gz'
if flowfile.exists():f=pd.read_csv(flowfile,dtype={'assets_raw':str})
else:
 con=sqlite3.connect(f'file:{R}/real_consequences/raw/events.sqlite?mode=ro',uri=True)
 f=pd.read_sql_query("select date,event,assets_raw from logs where vault=? and event in ('Deposit','Withdraw')",con,params=[spark])
assert len(f)>0
f['net_micro']=[int(a)*(1 if ev=='Deposit' else -1) for a,ev in zip(f.assets_raw,f.event)]
flow=f.groupby('date').net_micro.sum().to_dict();lagpath=A/'raw/spark_jan15';cover=json.loads((lagpath/'coverage.json').read_text());assert cover['complete']
lagnet=0;laglogs=0
for page in cover['pages']:
 for line in (lagpath/page['file']).read_text().splitlines():
  r=json.loads(line)
  for l in r.get('logs',[]):
   assert pd.Timestamp(r['header']['timestamp'],unit='s',tz='UTC').strftime('%Y-%m-%d')=='2025-01-15'
   dep=l['topics'][0]=='0xdcbc1c05240f31ff3ad067ef1ee35ce4997762752e3a095284754544f4c709d7';amount=int(l['data'][2:66],16);lagnet+=amount*(1 if dep else -1);laglogs+=1
flow['2025-01-15']=lagnet
pd.DataFrame([dict(date=k,spark_net_flow_micro=v) for k,v in sorted(flow.items())]).to_csv(O/'spark_daily_flow.csv',index=False)
d=pd.read_csv(R/'outputs/empirical/daily.csv');d=d[d.date.between('2025-01-15','2026-03-30')].sort_values('date').copy();assert len(d)==440
# Missing log dates are observed zero only because the committed-log archive covers every block.
d['spark_net_flow_usdc']=d.date.map(flow).fillna(0)/1e6;d['spark_flow_share']=d.spark_net_flow_usdc/d.assets;d['log_assets']=np.log(d.assets)
terms=['L_utilization10','L_cash_hhi','L_log_assets','L_spark_flow_share']
for k in ['utilization10','cash_hhi','log_assets','spark_flow_share']:d['L_'+k]=d[k].shift(1)
j=pd.read_csv(R/'joint_review/outputs/joint_request_daily.csv');j=j[j.request_pct==25].set_index('date');d['joint_exclusion25']=d.date.map(j.joint_budget_excluded).astype(float)
d['gap25']=1-d.J/(.25*d.assets);d['gap10']=1-d.J/(.10*d.assets);d['J_assets']=d.J/d.assets;d=d[d.date>='2025-01-16'].reset_index(drop=True);assert len(d)==439 and d[terms].notna().all().all()
d.to_csv(O/'daily_estimation_data.csv',index=False)
dt=pd.to_datetime(d.date);F=pd.get_dummies(pd.DataFrame({'month':dt.dt.strftime('%Y-%m'),'weekday':dt.dt.dayofweek.astype(str)}),drop_first=True,dtype=float);X=sm.add_constant(pd.concat([d[terms],F],axis=1));assert np.linalg.matrix_rank(X)==X.shape[1]
for spec in ['gap25','joint_exclusion25','J_assets','gap10']:
 m=sm.OLS(d[spec],X).fit(cov_type='HAC',cov_kwds={'maxlags':7,'use_correction':True},use_t=True)
 for t in terms:emit('joint_budget',spec,t,float(m.params[t]),float(m.bse[t]),float(m.pvalues[t]))
 meta.append(dict(model='joint_budget',spec=spec,Obs=int(m.nobs),R2=m.rsquared,df_p=m.df_resid,FE='year-month + weekday',covariance='HAC7 finite-sample correction',first=d.date.min(),last=d.date.max()))
checks.append(dict(check='daily_sample',N=len(d),Jan15_log_count=laglogs,Jan15_net_micro=lagnet,joint_excluded_days=int(d.joint_exclusion25.sum()),flow_denominator='ten-vault total assets',gap_outcomes='signed; no truncation'))
save();print('daily complete',flush=True)
# 3. Positive holdings only; per-market cash counted once in J.
p=pd.read_parquet(R/'outputs/empirical/positions.parquet');p=p[p.date.between('2025-01-16','2026-03-30') & p.position.gt(0)].copy();p['single']=np.minimum(p.position,p.market_cash)
assert not p.duplicated(['date','vault','market']).any()
for col in ['market_cash','market_supply','market_borrow']:assert p.groupby(['date','market'])[col].nunique().max()==1
m=p.groupby(['date','market']).agg(vault_count=('vault','nunique'),position=('position','sum'),largest_position=('position','max'),cash=('market_cash','first'),supply=('market_supply','first'),borrow=('market_borrow','first'),S=('single','sum')).reset_index();m['J']=np.minimum(m.cash,m.position);m['duplication']=(m.S-m.J)/m.S.where(m.S>0);m['utilization10']=10*m.borrow/m.supply.where(m.supply>0);m['log_cash']=np.log((m.cash/1e6).where(m.cash>0));m['largest_position_supply']=m.largest_position/m.supply.where(m.supply>0)
m.to_parquet(O/'market_daily_data.parquet',index=False)
# Restricted wild cluster bootstrap-t: market Rademacher weights; FE reabsorbed each draw.
# Exact enumeration for <=12 clusters, 9999 seeded draws otherwise. One-way studentization matches manuscript helper.
def wild(X,y,gs,j,rank):
 g=gs[0];G=int(max(g))+1;n=len(y);B,_=projector(g);bread=np.linalg.inv(X.T@X);a=X@bread[:,j];fac=G/(G-1)*(n-1)/(n-rank)
 b=bread@X.T@y;e=y-X@b;se=np.sqrt(fac*np.sum((B@(a*e))**2));obs=b[j]/se
 Xr=np.delete(X,j,axis=1);er=y-Xr@np.linalg.lstsq(Xr,y,rcond=None)[0];fit=y-er
 exact=G<=12;seed=20261002
 signs=np.array(list(itertools.product([-1.,1.],repeat=G))).T if exact else np.random.default_rng(seed).choice([-1.,1.],size=(G,9999))
 exceed=0
 for start in range(0,signs.shape[1],256):
  ys=demean(fit[:,None]+er[:,None]*signs[g,start:start+256],gs);bs=bread@X.T@ys;es=ys-X@bs;ses=np.sqrt(fac*np.sum((B@(a[:,None]*es))**2,axis=0));ts=bs[j]/ses;exceed+=np.sum(np.abs(ts)>=abs(obs)-1e-10)
 return float(exceed/signs.shape[1] if exact else (exceed+1)/(signs.shape[1]+1)),signs.shape[1],('exact' if exact else f'Monte Carlo seed {seed}')
terms=['vault_count','utilization10','log_cash','largest_position_supply']
for cutoff in [2,3]:
 src=m[m.vault_count>=cutoff].copy();z=src.replace([np.inf,-np.inf],np.nan).dropna(subset=['duplication']+terms).sort_values(['market','date']);gs=[groups(z.market),groups(z.date)];G=len(set(gs[0]));T=len(set(gs[1]));xy=demean(z[['duplication']+terms].to_numpy(float),gs);y=xy[:,0];X=xy[:,1:];assert np.linalg.matrix_rank(X)==4
 b=np.linalg.lstsq(X,y,rcond=None)[0];e=y-X@b;rank=4+G+T-1;cv=covariance(X,e,gs,rank);diag=np.diag(cv);se=np.sqrt(np.where(diag>=0,diag,np.nan));pv=2*stats.t.sf(abs(b/se),min(G,T)-1)
 for k,t in enumerate(terms):
  wp,draws,method=wild(X,y,gs,k,rank);emit('market_duplication',f'at_least_{cutoff}_vaults',t,float(b[k]),float(se[k]),float(pv[k]),wp)
 meta.append(dict(model='market_duplication',spec=f'at_least_{cutoff}_vaults',Obs=len(z),within_R2=1-e@e/(y@y),clusters_entity=G,clusters_date=T,df_p=min(G,T)-1,FE='market + date',covariance='two-way cluster CR1',wild_draws=draws,wild_method=method,excluded_rows=len(src)-len(z),first=z.date.min(),last=z.date.max()))
 checks.append(dict(check=f'market_sample_{cutoff}',eligible=len(src),used=len(z),zero_cash=int(src.cash.eq(0).sum()),negative_covariance_diagonal=[terms[i] for i,v in enumerate(diag) if v<0],max_FE_residual_mean=max(float(np.abs((projector(g)[0]@e)/projector(g)[1]).max()) for g in gs)))
 z.to_csv(O/f'market_estimation_at_least_{cutoff}.csv',index=False);save();print(f'market {cutoff} complete',flush=True)
print(pd.DataFrame(meta).to_string(index=False),flush=True)
