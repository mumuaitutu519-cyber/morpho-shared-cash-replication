from panel_evidence_stats import *
import warnings
p=pd.read_parquet(O/'daily_prediction_data.parquet');p['month']=p.date.str[:7];base=['D','utilization10','log_assets','Flow','shared_exposure'];issues=[]
for pct in [25,10]:
 y=f'next_refused{pct}';lag=f'refused{pct}'
 for spec,terms in [('LPM_lag',base+[lag]),('LPM_no_lag',base)]:
  fit(f'task3_{pct}',spec,p,y,terms,['vault','month'],['vault'],wild=True);save('task3');print(pct,spec,'complete',flush=True)
 # Dummy-FE logit: eliminate vaults with a constant outcome; explicitly report changes.
 z=p.dropna(subset=[y]+base+[lag]).copy();constant=z.groupby('vault')[y].nunique();drop=constant[constant<2].index;z=z[~z.vault.isin(drop)].copy()
 terms=base+[lag];F=pd.get_dummies(z[['vault','month']],drop_first=True,dtype=float);X=sm.add_constant(pd.concat([z[terms],F],axis=1));notes=[]
 try:
  with warnings.catch_warnings(record=True) as ws:
   warnings.simplefilter('always');m=sm.Logit(z[y],X).fit(disp=False,maxiter=500,cov_type='cluster',cov_kwds={'groups':groups(z.vault),'use_correction':True});notes=[str(w.message) for w in ws]
  converged=bool(m.mle_retvals['converged']);rank=int(np.linalg.matrix_rank(X));assert converged and rank==X.shape[1] and np.isfinite(m.bse).all(),(converged,rank,X.shape[1])
  for t in terms:ROWS.append(dict(model=f'task3_{pct}',spec='FE_logit',variable=t,coefficient=m.params[t],standard_error=m.bse[t],t_statistic=m.params[t]/m.bse[t],p_value=m.pvalues[t],covariance='cluster:vault asymptotic z',wild_cluster_p=logit_wclr(X,z[y],groups(z.vault),list(X.columns).index(t),m.params[t]/m.bse[t])))
  META.append(dict(model=f'task3_{pct}',spec='FE_logit',Obs=len(z),eligible=len(p),dropped=len(p)-len(z),FE='vault + month',clusters=f'vault:{z.vault.nunique()}',df_p=np.inf,pseudo_R2=m.prsquared,outcome_mean=z[y].mean(),constant_outcome_vaults=';'.join(drop),converged=converged,wild_draws=9999,wild_method='restricted WCLR-C'))
 except Exception as e:issues.append(dict(task=f'task3_{pct}',spec='FE_logit',error=str(e),warnings=notes,N=len(z),constant_outcome_vaults=list(drop)))
 save('task3');print(pct,'logit done',flush=True)
(P/'task3_status.json').write_text(json.dumps(issues,indent=2));save('task3')
(O/'task3_notes.txt').write_text('Outcomes are next closing-state refusal indicators at 25% and 10% of next-state total assets, in fractions. Current-state D and Shared are fractions, utilization is per 10 percentage points, Size is log USDC assets, Flow is committed ERC4626 net inflow in million USDC during the current UTC day. LPM includes vault and year-month fixed effects. CR1 vault-cluster t statistics use G-1 degrees of freedom. Restricted wild bootstrap-t uses Rademacher weights, 9,999 draws, seed 20261003; p=(exceedances+1)/10000. Logit uses the same FE and controls, vault-cluster normal-reference z statistics and McFadden pseudo R-squared. Logit wild p-values use restricted WCLR-C linearized bootstrap with 9,999 Rademacher draws (MacKinnon, Nielsen and Webb, 2024, equations 26-30,37-38; https://arxiv.org/html/2406.00650v1). Constant-outcome vaults are removed only in logit. *, **, *** denote 10%, 5%, 1%. Outcome means and exact sample counts appear in task3_models.csv. Cross-chain estimation is performed by estimate_cross_state_prediction.py using its archived same-day flow ledger.\n')
