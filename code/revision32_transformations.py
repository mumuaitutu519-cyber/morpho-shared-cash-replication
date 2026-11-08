from pathlib import Path
import pandas as pd,numpy as np,json,ast
from scipy.stats import t as tdist
from statsmodels.stats.multitest import multipletests
R=Path(__file__).resolve().parents[1];O=R/'reports/revision32';O.mkdir(exist_ok=True)
# Reuse only the tested estimation functions; do not execute R31's analysis as an import side effect.
tree=ast.parse((R/'code/revision31_interactions.py').read_text());functions=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]);exec(compile(functions,'R31_estimator','exec'))
names=['other_W','tightness','interaction','other_D','borrow','repay','treasury_Deposit','treasury_Withdraw'];ys=['deposit_1h','net_1h','deposit_6h','net_6h'];base=pd.read_csv(R/'reports/revision31/analysis_sample.csv',parse_dates=['hour']).set_index('hour');raw=-np.log1p(base.opening_cash);mu=raw.mean();sd=raw.std();records=[];focal=[];changes=[];diagnostics=[]
flowcols=['other_W','other_D','borrow','repay','treasury_Deposit','treasury_Withdraw','others_Withdraw','ethena_Withdraw']+ys
for variant,tail in [('winsor005',.005),('winsor01',.01),('asinh_million',None)]:
 g=base.copy()
 for col in flowcols+(['opening_cash'] if tail is not None else []):
  if tail is not None:
   lo,hi=base[col].quantile([tail,1-tail]);g[col]=base[col].clip(lo,hi)
   changes.append({'variant':variant,'variable':col,'lower':lo,'upper':hi,'changed_hours':int(g[col].ne(base[col]).sum()),'absolute_displacement':float(abs(g[col]-base[col]).sum()),'original_absolute_total':float(abs(base[col]).sum()),'above_cap_original_total':float(base.loc[base[col]>hi,col].sum())})
  else:g[col]=np.arcsinh(base[col])
 g['tightness']=(-np.log1p(g.opening_cash)-mu)/sd;g['interaction']=g.other_W*g.tightness;g.to_csv(O/f'{variant}_sample.csv')
 for bw in [24,168]:
  fits,it=fit(g,ys,bw)
  for y,(b,se,p,cov,cols,df,r2) in zip(ys,fits):
   model=f'{variant}_{y}_HAC{bw}'
   for term,c,s,prob in zip(cols,b,se,p):records.append({'variant':variant,'outcome':y,'model':model,'term':term,'coefficient':c,'se':s,'p':prob,'n':len(g),'bandwidth':bw})
   if bw==24:focal.append({'variant':variant,'outcome':y,'model':model,'coefficient':b[2],'se':se[2],'p':p[2]});pd.DataFrame(cov,index=cols,columns=cols).to_csv(O/f'{variant}_{y}_cov.csv')
 for kind in ['exclude_oct4_5','exclude_october','exclude_ethena']:
  z=g.copy();extra=kind=='exclude_ethena'
  if extra:z['other_W']=z.others_Withdraw;z['interaction']=z.other_W*z.tightness
  else:
   keep=np.ones(len(z),dtype=bool)
   for h in range(7):
    when=z.index+pd.Timedelta(hours=h)
    keep&=~np.isin(when.date,pd.DatetimeIndex(['2025-10-04','2025-10-05']).date) if kind=='exclude_oct4_5' else when.month!=10
   z=z[keep]
  if extra and z.ethena_Withdraw.nunique()==1:
   for y in ys[:2]:diagnostics.append({'variant':variant,'diagnostic':kind,'outcome':y,'coefficient':np.nan,'se':np.nan,'p':np.nan,'n':len(z),'status':'not_estimable: winsorization makes Ethena control constant'})
   continue
  fits,_=fit(z,ys[:2],24,extra)
  for y,(b,se,p,cov,cols,df,r2) in zip(ys[:2],fits):diagnostics.append({'variant':variant,'diagnostic':kind,'outcome':y,'coefficient':b[2],'se':se[2],'p':p[2],'n':len(z)})
f=pd.DataFrame(focal);f['holm12']=multipletests(f.p,method='holm')[1];old=pd.read_csv(R/'reports/revision31/focal_tests.csv');old32=pd.read_csv(R/'reports/revision28/search_family32.csv');f['holm16']=multipletests(np.r_[old.p,f.p],method='holm')[1][-12:];f['holm48']=multipletests(np.r_[old32.p,old.p,f.p],method='holm')[1][-12:]
f.to_csv(O/'focal_results.csv',index=False);pd.DataFrame(records).to_csv(O/'all_coefficients.csv',index=False);pd.DataFrame(changes).to_csv(O/'winsor_impact.csv',index=False);pd.DataFrame(diagnostics).to_csv(O/'diagnostics.csv',index=False)
# Re-estimate untouched inputs using the same helper and ensure exact reproduction of the baseline.
fits,_=fit(base,ys,24);r31=pd.read_csv(R/'reports/revision31/all_coefficients.csv');gap=0
for y,(b,se,p,*_) in zip(ys,fits):
 q=r31[r31.model.eq(y+'_HAC24')].set_index('term').loc[names];gap=max(gap,float(np.max(abs(q[['coefficient','se','p']].to_numpy()-np.column_stack([b,se,p])))))
assert gap<1e-10
(O/'VALIDATION.json').write_text(json.dumps({'n':len(base),'new_variants':3,'new_focal_tests':len(f),'baseline_max_gap':gap,'no_rows_dropped_by_transform':True,'interaction_rebuilt_after_transform':True,'transformed_units':'million USDC; asinh coefficients are not dollar slopes'},indent=2))
print(f.to_string(index=False));print(pd.DataFrame(diagnostics).to_string(index=False));print(pd.DataFrame(changes).query("variable=='other_W'").to_string(index=False))
