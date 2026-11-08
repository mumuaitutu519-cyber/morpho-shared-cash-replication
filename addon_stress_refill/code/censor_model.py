"""Cox with calendar strata, retaining all dates and exposing the separated fit."""
import warnings,json
import numpy as np,pandas as pd
from scipy import stats
from lifelines import CoxPHFitter
from preflight import O
def run():
    b=pd.read_csv(O/'B_regression_data.csv');x=pd.concat([b[['Dup','Util','log_assets','month']],pd.get_dummies(b.weekday.astype(str),prefix='weekday',drop_first=True,dtype=float)],axis=1);x['duration']=np.maximum(b.tau,1e-6);x['event']=~b.censored.astype(bool)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always');model=CoxPHFitter();model.fit(x,duration_col='duration',event_col='event',strata=['month'],robust=True)
    msgs=[str(w.message) for w in caught];model.summary.to_csv(O/'B_cox_stratified_all_terms.csv')
    # Exact Efron individual score contributions, including tied completions at t=0.
    terms=list(model.params_.index);X=x[terms].to_numpy();beta=model.params_.to_numpy();scores=np.zeros_like(X);hessian=np.zeros((len(terms),len(terms)))
    for month,ids in x.groupby('month').groups.items():
        ids=np.array(list(ids));times=x.loc[ids,'duration'].to_numpy();event=x.loc[ids,'event'].to_numpy();XX=X[ids];phi=np.exp(XX@beta)
        for t in np.unique(times[event]):
            deaths=(times==t)&event;risk=times>=t;count=int(deaths.sum());Rsum=phi[risk].sum();Esum=phi[deaths].sum();scores[ids[deaths]]+=XX[deaths]
            for tie in range(count):
                fraction=tie/count;denom=Rsum-fraction*Esum;weights=phi*(risk.astype(float)-fraction*deaths.astype(float))/denom;mean=(weights[:,None]*XX).sum(axis=0)
                scores[ids[deaths]]-=mean/count
                scores[ids]-=weights[:,None]*(XX-mean)
                centered=XX-mean;hessian+=centered.T@(centered*weights[:,None])
    assert np.max(abs(scores.sum(axis=0)))<1e-3,('Cox score equations not solved',scores.sum(axis=0))
    bread_gap=float(abs(np.linalg.inv(hessian)-model.variance_matrix_.to_numpy()).max())
    assert bread_gap<1e-5,('Independent Efron Hessian differs',bread_gap)
    B=scores@model.variance_matrix_.to_numpy();cov=B.T@B
    for lag in range(1,8):
        cross=B[lag:].T@B[:-lag];cov+=(1-lag/8)*(cross+cross.T)
    se=np.sqrt(np.diag(cov));rows=[]
    for term in ['Dup','Util','log_assets']:
        i=terms.index(term);coef=float(model.params_[term]);z=coef/se[i];rows.append(dict(spec='Cox_month_strata',term=term,coef=coef,se=se[i],t=z,p=2*stats.norm.sf(abs(z)),N=len(b),R2=np.nan))
    pd.DataFrame(rows).to_csv(O/'B_cox_stratified.csv',index=False);pd.DataFrame(cov,index=terms,columns=terms).to_csv(O/'B_cox_stratified_HAC7_covariance.csv');pd.DataFrame(scores,columns=terms).to_csv(O/'B_cox_Efron_scores.csv',index=False);(O/'B_cox_diagnostics.json').write_text(json.dumps({'month_dummy_fit':'calendar separation: September 2025 has 30 right-censored dates and no completed request; original fit retained as diagnostic, no accepted inference','stratified_fit_warnings':msgs,'calendar_strata':b.month.nunique(),'dates':len(b),'Sep2025_dates':int(b.month.eq('2025-09').sum()),'covariance':'HAC7 of exact Efron score contributions in chronological date order','max_score_equation_residual':float(abs(scores.sum(axis=0)).max()),'independent_Hessian_inverse_max_difference':bread_gap,'zero_times_hours':1e-6},indent=2));print(pd.DataFrame(rows).to_string(index=False),flush=True);print('warnings',msgs,flush=True)
    all_=pd.read_csv(O/'B_regressions.csv');all_=all_[~all_.spec.eq('Cox_month_strata')].copy();all_['accepted_inference']=~all_.spec.eq('Cox');all_['status']=np.where(all_.spec.eq('Cox'),'calendar separation; diagnostic only','validated')
    extra=pd.DataFrame(rows);extra['accepted_inference']=True;extra['status']='validated; year-month strata; exact Efron HAC7';pd.concat([all_,extra],ignore_index=True).to_csv(O/'B_regressions.csv',index=False)
if __name__=='__main__':run()
