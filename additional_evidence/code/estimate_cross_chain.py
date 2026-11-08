"""Same-state native-USDC Morpho vault exposure across four chains; requested models only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats
A=Path(__file__).resolve().parents[1];R=A.parent;C=A/'cross_chain';O=C/'outputs';O.mkdir(parents=True,exist_ok=True)
(R/'outputs').mkdir(exist_ok=True)
sys.path.insert(0,str(R/'code/empirical'));from build_panel import build
from estimate import groups,demean,projector
DATES=['2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31','2026-09-29']
CHAINS=[1,8453,42161,137];rows=[];descs=[];audit=[];provenance=[];allpositions=[]
for chain in CHAINS:
 for day in DATES:
  f=(C/'raw' if chain in [1,8453] else A/'raw')/f'morpho_{chain}_{day}.json'
  assert f.exists(),str(f)
  z=json.loads(f.read_text());pp,vv=build(z);p=pd.DataFrame(pp);v=pd.DataFrame(vv);assert v.asset_reconciliation_gap.eq(0).all();assert not p.duplicated(['vault','market']).any();allpositions.append(p.assign(chain=chain,date=day))
  mt=p.groupby('market').agg(P=('position','sum'),cash=('cash','first'),supply=('market_supply','first'),borrow=('market_borrow','first'));assert p.groupby('market').cash.nunique().max()==1
  J=sum(min(int(a),int(b)) for a,b in zip(mt.P,mt.cash));assert all(p.cash==p.market_cash),'global token cap binds; inspect before choosing definition'
  obs=[]
  for vr in v.itertuples():
   if int(vr.assets)<=0:continue
   own=p[(p.vault==vr.vault)&(p.position>0)].copy();S=sum(min(int(x),int(c)) for x,c in zip(own.position,own.cash));J_without=J
   for x in own.itertuples():
    P=int(mt.loc[x.market,'P']);M=int(mt.loc[x.market,'cash']);J_without-=min(P,M)-min(P-int(x.position),M)
   marginal=J-J_without;D=(S-marginal)/S if S else np.nan;Ptot=sum(int(x) for x in own.position);shared=sum(int(x.position) for x in own.itertuples() if int(mt.loc[x.market,'P'])>int(x.position))
   util=sum(int(x.position)*int(x.market_borrow)/int(x.market_supply) for x in own.itertuples())/Ptot*10 if Ptot else np.nan
   r=dict(chain=chain,date=day,block=z['block'],block_hash=z['block_hash'],vault=vr.vault,name=vr.name,entity=str(chain)+':'+vr.vault,chain_state=str(chain)+':'+day,assets_micro=int(vr.assets),S_micro=S,J_chain_micro=J,J_without_vault_micro=J_without,marginal_cash_micro=marginal,D=D,shared_market_share=shared/Ptot if Ptot else np.nan,active_markets=len(own),log_assets=np.log(int(vr.assets)/1e6),utilization10=util,max_market_share=max(own.position)/Ptot if Ptot else np.nan,position_micro=Ptot,zero_S=S==0)
   assert 0<=marginal<=S and (S==0 or 0<=D<=1);obs.append(r)
  dd=pd.DataFrame(obs);good=dd[~dd.zero_S];rows+=obs;descs.append(dict(chain=chain,date=day,block=z['block'],block_hash=z['block_hash'],deployed_vaults=len(v),positive_assets_vaults=len(dd),zero_S_excluded=int(dd.zero_S.sum()),vaults=len(good),D_mean=good.D.mean(),D_median=good.D.median(),shared_market_share_mean=good.shared_market_share.mean()))
  audit.append(dict(chain=chain,date=day,source=str(f.relative_to(R)),asset_reconciliations=len(v),same_token_cap_nonbinding=True,positive_assets=len(dd),S_zero=int(dd.zero_S.sum()),census_comparison=z.get('census_comparison')));provenance.append({'file':str(f.relative_to(R)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
panel=pd.DataFrame(rows).sort_values(['entity','date']).reset_index(drop=True);assert not panel.duplicated(['entity','date']).any();panel.to_csv(O/'vault_state_panel.csv',index=False,float_format='%.17g');pd.concat(allpositions,ignore_index=True).to_parquet(O/'position_panel.parquet',index=False);pd.DataFrame(descs).to_csv(O/'descriptives.csv',index=False,float_format='%.17g');(O/'data_audit.json').write_text(json.dumps(audit,indent=2));(C/'input_manifest.json').write_text(json.dumps(provenance,indent=2))
added=json.loads((C/'raw/morpho_8453_2026-09-29.json').read_text())['census_comparison']['added_positive']
panel[(panel.chain==8453)&(panel.date=='2026-09-29')&panel.vault.isin(added)].to_csv(O/'census_additions.csv',index=False,float_format='%.17g')
terms=['shared_market_share','active_markets','log_assets','utilization10','max_market_share'];eligible=panel[~panel.zero_S].copy();assert eligible[['D']+terms].notna().all().all();res=[];meta=[];design=[]
def add(spec,name,b,se,p):res.append(dict(model='cross_chain_exposure',spec=spec,variable=name,coefficient=float(b),standard_error=float(se),t_statistic=float(b/se),p_value=float(p)))
# A: identical design with chain-cluster CR1 and HC1 inference.
z=eligible[eligible.date=='2026-09-29'].reset_index(drop=True);F=pd.get_dummies(z.chain.astype(str),drop_first=True,dtype=float);X=sm.add_constant(pd.concat([z[terms],F],axis=1));rank=np.linalg.matrix_rank(X);assert rank==X.shape[1]
for label,cov,kw in [('a_chain_cluster','cluster',{'groups':z.chain,'use_correction':True,'df_correction':True}),('a_HC1','HC1',{})]:
 m=sm.OLS(z.D,X).fit(cov_type=cov,cov_kwds=kw,use_t=True)
 for t in terms:add(label,t,m.params[t],m.bse[t],m.pvalues[t])
 meta.append(dict(model='cross_chain_exposure',spec=label,Obs=len(z),vaults=z.entity.nunique(),clusters=z.chain.nunique() if cov=='cluster' else np.nan,cluster_unit='chain' if cov=='cluster' else 'HC1 heteroskedasticity robust',FE='chain',R2=m.rsquared,within_R2=np.nan,df_p=z.chain.nunique()-1 if cov=='cluster' else m.df_resid,design_rank=int(rank),singleton_vaults=np.nan))
# Rank for crossed FE is entity count + state count - number of connected components.
def fe_components(g1,g2):
 a=int(max(g1))+1;b=int(max(g2))+1;parent=list(range(a+b))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for i,j in zip(g1,g2):
  ri,rj=root(int(i)),root(a+int(j));parent[ri]=rj
 return len({root(i) for i in range(a+b)})
for label,cols in [('b_chain_state_FE',['chain_state']),('c_vault_chain_state_FE',['entity','chain_state'])]:
 z=eligible.sort_values(['entity','date']).reset_index(drop=True);gs=[groups(z[k]) for k in cols];xy=demean(z[['D']+terms].to_numpy(float),gs);y=xy[:,0];X=xy[:,1:];assert np.linalg.matrix_rank(X)==len(terms),label
 components=fe_components(*gs) if len(gs)==2 else None;fe_rank=(len(set(gs[0])) if len(gs)==1 else sum(len(set(g)) for g in gs)-components);rank=len(terms)+fe_rank;n=len(z);g=groups(z.entity);G=len(set(g));bread=np.linalg.inv(X.T@X);b=bread@X.T@y;e=y-X@b;B,_=projector(g);scores=B@(X*e[:,None]);cov=bread@(scores.T@scores)@bread * G/(G-1)*(n-1)/(n-rank);se=np.sqrt(np.diag(cov));pv=2*stats.t.sf(abs(b/se),G-1)
 for j,t in enumerate(terms):add(label,t,b[j],se[j],pv[j])
 meta.append(dict(model='cross_chain_exposure',spec=label,Obs=n,vaults=G,clusters=G,cluster_unit='chain+vault address',FE=' + '.join(cols),R2=np.nan,within_R2=1-e@e/(y@y),df_p=G-1,design_rank=rank,FE_components=components,singleton_vaults=int(z.groupby('entity').size().eq(1).sum())))
 design.append(dict(spec=label,rank_X=int(np.linalg.matrix_rank(X)),FE_rank=fe_rank,FE_components=components,max_FE_residual_mean=max(float(np.abs((projector(gg)[0]@e)/projector(gg)[1]).max()) for gg in gs)))
pd.DataFrame(res).to_csv(O/'cross_chain_regressions.csv',index=False,float_format='%.17g');pd.DataFrame(meta).to_csv(O/'cross_chain_models.csv',index=False,float_format='%.17g');(O/'design_checks.json').write_text(json.dumps(design,indent=2));print(pd.DataFrame(meta).to_string(index=False));print(pd.DataFrame(res).to_string(index=False))
# Mechanism a-d are the frozen completed results. E is the explicitly requested formula-deviation regression.
rr=pd.read_csv(A/'outputs/mechanism.csv').drop(columns=['wild_cluster_p']);mm=pd.read_csv(A/'outputs/model_metadata.csv');mm=mm[mm.model=='mechanism'].copy();p=pd.read_csv(A/'outputs/mechanism_observations.csv');p['opening_gap_million']=[max(int(q)-int(w),0)/1e12 for q,w in zip(p.claim_micro_before,p.capacity_micro_before)];p['formula_error_million']=[(int(after)-int(before)-min(int(d),max(int(q)-int(before),0)))/1e12 for after,before,d,q in zip(p.capacity_micro,p.capacity_micro_before,p.deposit_micro,p.claim_micro_before)];g=groups(p.tx);m=sm.OLS(p.formula_error_million,sm.add_constant(p.opening_gap_million)).fit(cov_type='cluster',cov_kwds={'groups':g,'use_correction':True,'df_correction':True},use_t=True)
extra=[]
for t,name in [('const','intercept'),('opening_gap_million','opening_gap')]:extra.append(dict(model='mechanism',spec='e_formula_error',variable=name,coefficient=m.params[t],standard_error=m.bse[t],t_statistic=m.tvalues[t],p_value=m.pvalues[t]))
rr=pd.concat([rr,pd.DataFrame(extra)],ignore_index=True);rr.to_csv(O/'mechanism_regressions.csv',index=False,float_format='%.17g');me=dict(model='mechanism',spec='e_formula_error',Obs=len(p),R2=m.rsquared,clusters_entity=p.tx.nunique(),df_p=p.tx.nunique()-1,FE='none',covariance='transaction cluster CR1',slope_equals_one_p=np.nan,intercept_equals_zero_p=m.pvalues['const'],first=p.date.min(),last=p.date.max());mm=pd.concat([mm,pd.DataFrame([me])],ignore_index=True);mm.to_csv(O/'mechanism_models.csv',index=False,float_format='%.17g');p[['tx','owner','date','opening_gap_million','formula_error_million']].to_csv(O/'mechanism_e_data.csv',index=False,float_format='%.17g')
# Paper-facing wide table: coefficients followed by parenthesized t statistics, never SEs.
specs=['a_pooled','b_transaction_FE','c_constrained','d_constrained_from_2025_04_23','e_formula_error'];table=[]
for term,label in [('min_deposit_opening_gap','min(deposit, opening gap)'),('opening_gap','Opening gap'),('intercept','Intercept')]:
 values={};ts={}
 for col,spec in zip('abcde',specs):
  z=rr[(rr.spec==spec)&(rr.variable==term)]
  if z.empty:values[col]='';ts[col]=''
  else:
   r=z.iloc[0];stars='***' if r.p_value<.01 else '**' if r.p_value<.05 else '*' if r.p_value<.1 else '';values[col]=f'{r.coefficient:.6f}'+stars;ts[col]=f'({r.t_statistic:.2f})'
 table.append({'row':label,**values});table.append({'row':label+' t statistic',**ts})
for key,label in [('slope_equals_one_p','p(slope = 1)'),('Obs','Observations'),('clusters_entity','Transaction clusters'),('R2','R-squared'),('FE','Fixed effects')]:
 vals={}
 for col,spec in zip('abcde',specs):
  v=mm[mm.spec==spec].iloc[0][key]
  vals[col]='' if pd.isna(v) else str(int(v)) if key in ['Obs','clusters_entity'] else f'{float(v):.9f}' if key=='R2' else f'{float(v):.6f}' if key=='slope_equals_one_p' else v
 table.append({'row':label,**vals})
pd.DataFrame(table).to_csv(O/'mechanism_paper_table.csv',index=False)
(C/'mechanism_table_notes.txt').write_text('Amounts are in million USDC. Columns a-d use the change in withdrawal capacity. Column e uses that change minus min(deposit, opening gap), with opening gap as the regressor and an intercept. Parentheses contain t statistics based on transaction-clustered standard errors. Column b includes transaction fixed effects. Columns c and d use the same 17 constrained observations, all dated after April 23, 2025. A common intercept in column b is absorbed. *, ** and *** denote p<0.10, p<0.05 and p<0.01. The slope-equals-one test refers to the min(deposit, opening gap) coefficient and is not applicable to column e.\n')
print('mechanism_e',json.dumps(extra),flush=True)
