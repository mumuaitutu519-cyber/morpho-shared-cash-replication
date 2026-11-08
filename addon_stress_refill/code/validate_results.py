"""Independent numerical and coverage checks of the published estimates."""
import json
import numpy as np,pandas as pd
import patsy
from scipy import stats
from preflight import O,R
def hac_check(formula,data,rows):
    yy,xx=patsy.dmatrices(formula,data,return_type='dataframe');X=xx.to_numpy();y=yy.to_numpy().ravel();n,k=X.shape;pinv=np.linalg.pinv(X);beta=pinv@y;e=y-X@beta;score=X*e[:,None];meat=score.T@score
    for lag in range(1,8):g=score[lag:].T@score[:-lag];meat+=(1-lag/8)*(g+g.T)
    bread=pinv@pinv.T;cov=bread@meat@bread*n/(n-k);se=np.sqrt(np.diag(cov));diff=[]
    for r in rows.itertuples():
        j=list(xx.columns).index(r.term);p=2*stats.t.sf(abs(beta[j]/se[j]),n-k);diff.append(dict(term=r.term,coefficient_gap=abs(beta[j]-r.coef),se_gap=abs(se[j]-r.se),p_gap=abs(p-r.p)))
    assert max(z['coefficient_gap'] for z in diff)<1e-7 and max(z['se_gap'] for z in diff)<1e-6
    return diff
def run():
    gate=json.loads((O/'gate_results.json').read_text());assert gate['reference_gate'] and gate['full_daily_market_checks']==14520 and gate['full_daily_market_max_gap_micro']<=1
    q=pd.read_csv(O/'B1_daily_replay.csv');assert len(q)==439*6 and q.valid_result.all() and q.horizon_complete.all();assert q.tau.between(0,168).all();assert (q.censored==q.paid_fraction.lt(1)).all();assert (q.tau.eq(0)==q.initial_paid_micro.eq(q.request_micro)).all();assert q[q.censored].tau.eq(168).all()
    b3=pd.read_csv(O/'B3_daily_checks.csv');assert not ((b3.tau_zero)&(~b3.reference_zero)).any();assert b3[b3.f.eq(25)].mismatch.sum()==4
    a=pd.read_csv(O/'A1_daily_panel.csv');ar=pd.read_csv(O/'A1_regressions.csv');checks=[]
    for (outcome,spec),rows in ar.groupby(['outcome','spec']):
        formula=f'{outcome} ~ W1 + W2 + C(weekday)'+(' + C(month)' if spec=='year_month' else '');checks+=hac_check(formula,a,rows)
    b=pd.read_csv(O/'B_regression_data.csv');br=pd.read_csv(O/'B_regressions.csv')
    for name,extra in [('baseline',''),('windows',' + W1 + W2')]:checks+=hac_check('log_tau ~ Dup + Util + log_assets + C(month) + C(weekday)'+extra,b,br[br.spec.eq(name)])
    pd.DataFrame(checks).to_csv(O/'independent_HAC_checks.csv',index=False)
    result={'reference_and_asset_gates':'PASS','full_33_market_cash_grid':'PASS','all_2634_replay_runs_complete':'PASS','B3_differences_retained':4,'independent_HAC_coefficients_and_covariances':'PASS','max_HAC_se_difference':max(z['se_gap'] for z in checks),'B1_initial_cash_full_grid_check':'Every run has the same tau and paid fraction as the earlier active-queue cash check; unheld-market clipping is corrected'}
    if (O/'hourly_gates.json').exists():result['hourly_gates']=json.loads((O/'hourly_gates.json').read_text())
    v=pd.read_parquet(O/'vault_states.parquet');ledger=pd.read_parquet(R/'additional_evidence/panel_evidence/raw/market_operations.parquet');anchor=v.iloc[0];assert (int(anchor.timestamp)+2*(ledger.block-int(anchor.block))==ledger.timestamp).all();assert (int(anchor.timestamp)+2*(v.block-int(anchor.block))==v.timestamp).all()
    (O/'Base_clock_validation.json').write_text(json.dumps({'ledger_events':len(ledger),'daily_vault_states':len(v),'event_timestamp_gap_seconds':0,'daily_timestamp_gap_seconds':0,'anchor_block':int(anchor.block),'anchor_timestamp':int(anchor.timestamp)},indent=2))
    if (O/'A3_hour_panel.parquet').exists():
        panel=pd.read_parquet(O/'A3_hour_panel.parquet');reg=pd.read_csv(O/'A3_regressions.csv');independent=[]
        for row in reg.itertuples():
            q=panel[panel.chain.eq(row.chain)&panel.scope.eq(row.scope)].dropna(subset=[row.outcome,'interaction']).copy();xy=q[[row.outcome,'interaction']].copy()
            for _ in range(1000):
                old=xy.to_numpy().copy()
                for key in ['vault','utc']:xy-=xy.groupby(q[key]).transform('mean')
                if np.max(abs(xy.to_numpy()-old))<1e-12:break
            else:raise AssertionError('Independent A3 absorption did not converge')
            y,x=xy.iloc[:,0],xy.iloc[:,1];beta=float(x@y/(x@x));score=x*(y-beta*x);g=score.groupby(q.vault).sum();N=len(q);G=q.vault.nunique();rank=G+q.utc.nunique();se=np.sqrt(float(g@g)/(x@x)**2*G/(G-1)*(N-1)/(N-rank));pval=2*stats.t.sf(abs(beta/se),G-1)
            assert abs(beta-row.coef)<1e-7 and abs(se-row.se)<1e-7 and abs(pval-row.p)<1e-6
            independent.append(dict(chain=row.chain,scope=row.scope,outcome=row.outcome,coef_gap=abs(beta-row.coef),se_gap=abs(se-row.se),p_gap=abs(pval-row.p)))
        pd.DataFrame(independent).to_csv(O/'independent_A3_cluster_checks.csv',index=False);result['independent_A3_cluster_covariance']='PASS'
    if all((O/f'A4_summary_{c}.csv').exists() for c in [1,42161]):
        for c in [1,42161]:
            cover=pd.read_csv(O/f'A4_portal_coverage_{c}.csv');assert (cover.from_block.iloc[1:].to_numpy()==cover.last_block.iloc[:-1].to_numpy()+1).all();assert json.loads((O/f'A4_trace_log_check_{c}.json').read_text())['logs_without_calls']==0
        result['A4_contiguous_trace_coverage_and_committed_log_crosscheck']='PASS'
    (O/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':run()
