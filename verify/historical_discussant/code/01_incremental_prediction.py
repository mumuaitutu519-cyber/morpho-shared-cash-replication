"""Chronological later-outcome tests; no joint outcome duplicated as vault outcomes."""
import json,warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from settings import OUT,PE,R,ADD
from statistics_common import cluster_cov,nw_vault_cov,auc


def design(z,basis,with_d,months=None):
    x=z[[basis,'utilization10','log_assets','active_markets']].astype(float).copy()
    x=x.rename(columns={basis:'JA'})
    if with_d:x['D']=z.D
    labels=z.month.copy()
    if months is None:months=sorted(labels.unique())
    labels=labels.where(labels.isin(months),months[-1])
    for month in months[1:]:x['month_'+month]=labels.eq(month).astype(float)
    x.insert(0,'const',1.)
    return x,months


def estimate(z,yname,basis,with_d,kind,months=None):
    z=z.copy()
    if z[yname].nunique()<2:raise ValueError('Outcome is constant in this estimation sample')
    dropped=0
    if kind=='Logit':
        valid=z.groupby('month')[yname].nunique()
        keep=valid[valid.gt(1)].index
        dropped=len(z)-int(z.month.isin(keep).sum())
        z=z[z.month.isin(keep)].copy()
        if z[yname].nunique()<2:raise ValueError('No varying year-month strata for FE logit')
    X,months=design(z,basis,with_d,months)
    if np.linalg.matrix_rank(X)<X.shape[1]:raise ValueError('Regressors are collinear after the stated FE/sample filter')
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always')
        if kind=='LPM':
            fit=sm.OLS(z[yname].to_numpy(),X).fit()
            resid=z[yname].to_numpy()-np.asarray(fit.predict(X))
            score=X.to_numpy()*resid[:,None]
            bread=np.linalg.inv(X.to_numpy().T@X.to_numpy())
            ym=z[yname]-z.groupby('month')[yname].transform('mean')
            metric=1-float(resid@resid)/float(ym@ym)
        else:
            fit=sm.GLM(z[yname].to_numpy(),X,family=sm.families.Binomial()).fit(maxiter=200,tol=1e-10)
            if not fit.converged:raise ValueError('Unpenalized FE logit did not converge')
            if any('separation' in str(w.message).lower() for w in ws):raise ValueError('Unpenalized FE logit separation')
            prob=np.asarray(fit.predict(X))
            if not np.isfinite(fit.params).all():raise ValueError('Unpenalized FE logit has nonfinite parameters')
            score=X.to_numpy()*(z[yname].to_numpy()-prob)[:,None]
            bread=np.linalg.inv(X.to_numpy().T@((prob*(1-prob))[:,None]*X.to_numpy()))
            metric=1-fit.llf/fit.llnull
    return dict(z=z,X=X,fit=fit,score=score,bread=bread,months=months,metric=metric,
                constant_month_rows_dropped=dropped,warnings='; '.join(str(w.message) for w in ws))


def run():
    daily=pd.read_parquet(PE/'daily_prediction_data.parquet').sort_values(['vault','date']).reset_index(drop=True)
    replay=pd.read_csv(OUT/'package/full_replay/output/vault_replay_24h.csv')
    daily=daily.merge(replay[['date','vault','not_paid24','remaining_24h_micro']],on=['date','vault'],validate='one_to_one')
    p=pd.read_parquet(ADD/'positions.parquet')
    marginal=[]
    for date,g in p.groupby('date'):
        total=g.groupby('market').position.sum()
        for vault,x in g.groupby('vault'):
            other=x.market.map(total)-x.position
            contribution=int((np.minimum(x.position+other,x.cash)-np.minimum(other,x.cash)).sum())
            marginal.append(dict(date=date,vault=vault,marginal_micro=contribution))
    daily=daily.merge(pd.DataFrame(marginal),on=['date','vault'],validate='one_to_one')
    known=pd.read_csv(ADD/'daily.csv').set_index('date')
    daily['JA_marginal']=daily.marginal_micro/daily.assets
    daily['JA_pool']=daily.date.map(known.JA)
    difference=np.abs(daily.D-(1-daily.marginal_micro/daily.capacity))
    assert difference.dropna().max()<1e-12
    events=pd.read_csv(ADD/'A4_base_strict_events.csv')
    dates=sorted(daily.date.unique());split=dates[299]
    trainmed=daily[daily.date.le(split)].groupby('vault').marginal_micro.median()
    overallmed=daily.groupby('vault').marginal_micro.median()
    daily['month']=daily.date.str[:7]
    labelrows=[]
    for vault,g in daily.groupby('vault'):
        g=g.sort_values('date').copy()
        eventtimes=np.sort(events.loc[events.vault.eq(vault),'timestamp'].to_numpy())
        for h in [1,7,30]:
            # Future states are t+1,...,t+h. A full h-day window is mandatory.
            values=[];mins=[]
            for i,r in enumerate(g.itertuples()):
                complete=i+h<len(g)
                end=r.timestamp+h*86400
                bad=np.searchsorted(eventtimes,end,side='right')-np.searchsorted(eventtimes,r.timestamp,side='right')
                future=g.iloc[i+1:i+h+1]
                values.append((float(bad>0) if complete else np.nan,float(future.not_paid24.max()) if complete else np.nan))
                mins.append(float(future.marginal_micro.min()) if complete else np.nan)
            g[f'error_h{h}']=[v[0] for v in values]
            g[f'replay_h{h}']=[v[1] for v in values]
            g[f'min_cash_h{h}']=mins
            g[f'lowbound_h{h}']=np.where(np.isfinite(mins),np.asarray(mins)<overallmed[vault],np.nan)
            g[f'lowbound_train_h{h}']=np.where(np.isfinite(mins),np.asarray(mins)<trainmed[vault],np.nan)
        labelrows.append(g)
    panel=pd.concat(labelrows,ignore_index=True)
    panel.to_parquet(OUT/'data/incremental_prediction_panel.parquet',index=False)
    rows=[];issues=[];forecast=[]
    for basis in ['JA_marginal','JA_pool']:
        for outcome in ['error','replay','lowbound']:
            for h in [1,7,30]:
                y=f'{outcome}_h{h}'
                z=panel.replace([np.inf,-np.inf],np.nan).dropna(subset=[y,basis,'D','utilization10','log_assets','active_markets']).copy()
                for kind in ['LPM','Logit']:
                    try:
                        m0=estimate(z,y,basis,False,kind)
                        m1=estimate(z,y,basis,True,kind)
                        assert m0['z'][['date','vault']].equals(m1['z'][['date','vault']])
                        q=m1['z'];j=list(m1['X'].columns).index('D');coef=float(m1['fit'].params['D'])
                        for covariance in ['vault_date','NW_by_vault']:
                            if covariance=='vault_date':
                                cv=cluster_cov(m1['score'],m1['bread'],[q.vault,q.date],m1['X'].shape[1])
                            else:
                                cv=nw_vault_cov(m1['score'],m1['bread'],q.vault,q.date,m1['X'].shape[1],max(7,h))
                            se=np.sqrt(cv[j,j]) if cv[j,j]>0 else np.nan
                            t=coef/se;df=q.vault.nunique()-1
                            rows.append(dict(baseline=basis,outcome=outcome,h=h,model=kind,covariance=covariance,
                                coefficient_D=coef,se=se,t=t,p=2*stats.t.sf(abs(t),df),N=len(q),vaults=q.vault.nunique(),dates=q.date.nunique(),
                                R2_M0=m0['metric'],R2_M1=m1['metric'],delta_R2=m1['metric']-m0['metric'],
                                metric='within-year-month R2' if kind=='LPM' else 'McFadden pseudo R2',
                                constant_month_rows_dropped=m1['constant_month_rows_dropped'],status='PASS' if np.isfinite(se) else 'two-way covariance diagonal nonpositive; inference unavailable'))
                    except Exception as exc:issues.append(dict(baseline=basis,outcome=outcome,h=h,model=kind,stage='full_sample',reason=str(exc)))
                    # First 300 closes define the train cutoff; purge labels that extend past it.
                    try:
                        zo=z.copy()
                        if outcome=='lowbound':zo[y]=zo[f'lowbound_train_h{h}']
                        label_lag=h+(1 if outcome=='replay' else 0)
                        cutoff=(pd.Timestamp(split)-pd.Timedelta(days=label_lag)).strftime('%Y-%m-%d')
                        train=zo[zo.date.le(cutoff)].copy()
                        test=zo[zo.date.gt(split)].copy()
                        aucs=[];preds=[]
                        for include in [False,True]:
                            fit=estimate(train,y,basis,include,kind)
                            X,_=design(test,basis,include,fit['months'])
                            probability=fit['fit'].predict(X)
                            aucs.append(auc(test[y],probability));preds.append(np.asarray(probability))
                        forecast.append(dict(baseline=basis,outcome=outcome,h=h,model=kind,split_date=split,
                            last_training_feature_date=cutoff,label_lag_days=label_lag,train_N=len(train),test_N=len(test),
                            test_positive=int(test[y].sum()),AUC_M0=aucs[0],AUC_M1=aucs[1],delta_AUC=aucs[1]-aucs[0],
                            future_month_rule='carry latest estimable training month intercept for unseen year-months'))
                    except Exception as exc:issues.append(dict(baseline=basis,outcome=outcome,h=h,model=kind,stage='out_of_sample',reason=str(exc)))
                pd.DataFrame(rows).to_csv(OUT/'tables/incremental_prediction.csv',index=False)
                pd.DataFrame(forecast).to_csv(OUT/'tables/incremental_prediction_oos.csv',index=False)
                print('Prediction checkpoint',basis,outcome,h,flush=True)
    # Audit whether fixed-horizon outcomes can actually be observed in the four-chain census.
    cross=pd.read_csv(R/'additional_evidence/cross_chain/outputs/vault_state_panel.csv')
    coverage=[]
    for chain,g in cross.groupby('chain'):
        calendar=sorted(g.date.unique())
        gaps=pd.Series(pd.to_datetime(calendar)).diff().dt.days.dropna()
        coverage.append(dict(chain=int(chain),states=len(g),dates=len(calendar),min_gap_days=int(gaps.min()),max_gap_days=int(gaps.max()),
                             daily_1_7_30_minimum_outcome_observable=False,
                             reason='Seven irregular census dates, no complete daily follow-up; replay exists only for the fixed ten Base vaults; full-call history absent for the other chains'))
    pd.DataFrame(coverage).to_csv(OUT/'tables/four_chain_outcome_coverage.csv',index=False)
    (OUT/'logs/step1_status.json').write_text(json.dumps(dict(issues=issues,split_date=split,
        original_vault_dates=len(daily),replay_vault_labels=len(replay),
        D_definition='D_v = 1 - [J(V)-J(V without v)] / standalone capacity; not portfolio Dup',
        JA_primary='marginal joint cash contribution / own vault assets; independently reconstructed from positions and cash',
        JA_robustness='pool-wide joint bound / aggregate ten-vault assets',
        horizon_definition='any recorded error or any future initiated request unpaid24 over t+1 through t+h; future minimum marginal joint cash below vault full-sample median',
        out_of_sample='fixed first-300-date cutoff; h-day label purge (h+1 for replay, whose payment status requires another24h); training-only median for lowbound outcome; unseen month FE carried from latest training month',
        logit='drop constant-outcome year-month strata identically in M0 and M1; report excluded rows; no penalized fallback',
        inference='two-way CR1 vault/date, t with 9 df; NW within vault with max(7,h) calendar-day lags; no PSD repair of negative two-way variances'),indent=2))
    print('Step1 complete',len(rows),'result rows;',len(issues),'explicit fit issues',flush=True)


if __name__=='__main__':run()
