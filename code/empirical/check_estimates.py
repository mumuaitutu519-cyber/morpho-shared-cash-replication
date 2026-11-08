from pathlib import Path
import json
import pandas as pd,numpy as np,statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
R=Path(__file__).resolve().parents[2];O=R/'outputs/empirical';p=pd.read_parquet(O/'estimation_panel.parquet');xs=['D10','coverage10','log_assets','utilization10'];z=p.dropna(subset=['leadY25']+xs).sort_values(['vault','date']);F=pd.get_dummies(z[['vault','date']],drop_first=True,dtype=float);X=sm.add_constant(pd.concat([z[xs],F],axis=1));m=sm.OLS(z.leadY25,X).fit();cov=cov_cluster_2groups(m,pd.factorize(z.vault)[0],pd.factorize(z.date)[0])[0];r=pd.read_csv(O/'regressions.csv');r=r[r.model=='III_B_both_25'].set_index('term');gaps={t:{'coef':float(m.params[t]-r.loc[t,'coef']),'se':float(np.sqrt(cov[X.columns.get_loc(t),X.columns.get_loc(t)])-r.loc[t,'se'])} for t in xs};assert max(abs(x) for a in gaps.values() for x in a.values())<1e-8
# Independently calculate every rolling correlation using centered window dot products.
a=p.pivot(index='date',columns='vault',values='dlog_W').sort_index();pair=pd.read_parquet(O/'pair_panel.parquet');stable=[];diffs=[]
for row in pair.itertuples():
 i=a.index.get_loc(row.date);u,v=row.pair.split('_');rho=np.nan
 if i>=29:
  x=a[u].iloc[i-29:i+1].to_numpy();y=a[v].iloc[i-29:i+1].to_numpy()
  if np.isfinite(x).all() and np.isfinite(y).all():
   x=x-x.mean();y=y-y.mean();den=np.sqrt((x@x)*(y@y))
   if den>0:
    t=float((x@y)/den)
    if abs(t)<1-1e-12:rho=t
 stable.append(rho)
 if np.isfinite(rho) and pd.notna(row.correlation):diffs.append(abs(rho-row.correlation))
valid=np.isfinite(stable);before=pair.correlation.notna().to_numpy();rep={'dummy_OLS_two_way_cluster_comparison':gaps,'rolling_valid_before':int(before.sum()),'rolling_valid_centered':int(valid.sum()),'rolling_validity_disagreements':int((valid!=before).sum()),'rolling_max_difference':max(diffs) if diffs else None}
assert rep['rolling_validity_disagreements']==0 and rep['rolling_max_difference']<1e-7
(O/'independent_estimate_checks.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
