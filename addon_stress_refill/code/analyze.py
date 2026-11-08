from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from numba import njit
from preflight import A,R,O

W={'W1':('2025-10-09','2025-10-17'),'W2':('2025-11-03','2025-11-21')}
def calendar(d):
    d=d.copy();ts=pd.to_datetime(d.date);d['weekday']=ts.dt.dayofweek;d['month']=ts.dt.strftime('%Y-%m')
    for name,(start,end) in W.items():d[name]=d.date.between(start,end).astype(int)
    return d

def a1(write_base=True):
    d=pd.read_csv(O/'daily.csv');q=pd.read_csv(O/'joint_requests.csv');q=q[q.f.eq(25)]
    d=d.merge(q[['date','all_pass','excluded','gap','request']],on='date',validate='one_to_one')
    e=pd.read_csv(R/'real_consequences/outputs/A1_clean_events.csv')
    assert len(e)==252
    strict=pd.read_csv(O/'A4_base_strict_events.csv') if (O/'A4_base_strict_events.csv').exists() else e
    d['Errors']=d.date.map(strict[strict.is_primary.eq(1)].groupby('date').size()).fillna(0).astype(int)
    d['Errors_all']=d.date.map(strict.groupby('date').size()).fillna(0).astype(int)
    d['Errors_table11']=d.date.map(e[e.is_primary.eq(1)].groupby('date').size()).fillna(0).astype(int)
    d=calendar(d);d['excluded']=d.excluded.astype(int);d.to_csv(O/'A1_daily_panel.csv',index=False)
    rows=[];models=[]
    for outcome in ['Dup','JA','Util','excluded','Errors']:
        for label,extra in [('weekday',''),('year_month',' + C(month)')]:
            fit=smf.ols(f'{outcome} ~ W1 + W2 + C(weekday)'+extra,d).fit(cov_type='HAC',cov_kwds={'maxlags':7,'use_correction':True},use_t=True)
            for term in ['W1','W2']:rows.append(dict(outcome=outcome,spec=label,term=term,coef=fit.params[term],se=fit.bse[term],t=fit.tvalues[term],p=fit.pvalues[term]))
            models.append(dict(outcome=outcome,spec=label,N=int(fit.nobs),R2=fit.rsquared,rank=int(fit.model.rank),columns=fit.model.exog.shape[1],covariance='Newey-West 7 days'))
    pd.DataFrame(rows).to_csv(O/'A1_regressions.csv',index=False);pd.DataFrame(models).to_csv(O/'A1_models.csv',index=False)
    desc=[];errors=[];periods=[]
    for name,(start,end) in W.items():
        cs=(pd.Timestamp(start)-pd.Timedelta(days=30)).strftime('%Y-%m-%d');ce=(pd.Timestamp(start)-pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        other='W2' if name=='W1' else 'W1'
        for label,lo,hi,control in [(name,start,end,False),(name+'_control',cs,ce,True)]:
            mask=d.date.between(lo,hi)&((d[other].eq(0)) if control else True);g=d[mask];dates=set(g.date);periods.append(dict(period=label,start=lo,end=hi,days=len(g),exclude_other_window=control))
            bad=g[g.excluded.eq(1)]
            desc.append(dict(period=label,days=len(g),Dup=g.Dup.median(),JA=g.JA.median(),Util=g.Util.median(),excluded_median=g.excluded.median(),Errors_median=g.Errors.median(),Errors_total=int(g.Errors.sum()),individual_all_pass_days=int(g.all_pass.sum()),excluded_days=int(g.excluded.sum()),median_gap_request=(bad.gap/bad.request).median()))
            for scope,x in [('Table11',e[e.date.isin(dates)]),('strict_claim',e[e.date.isin(dates)&e.requested_USDC.le(e.claim_convert_USDC)])]:
                resolved=x[~x.unresolved]
                errors.append(dict(chain='Base',period=label,filter=scope,events=len(x),holders=x.owner.nunique(),request_median=x.requested_USDC.median(),completed_share=len(resolved)/len(x) if len(x) else np.nan,wait_median_hours=resolved.wait_hours.median()))
    pd.DataFrame(periods).to_csv(O/'periods.csv',index=False);pd.DataFrame(desc).to_csv(O/'A1_descriptives.csv',index=False)
    if write_base:pd.DataFrame(errors).to_csv(O/'A4_base.csv',index=False)
    print('A1 done',flush=True)

@njit(cache=True)
def pay(cash,pos,queue,lengths,remaining,order):
    paid=0
    for v in order:
        if remaining[v]==0:continue
        for rank in range(lengths[v]):
            m=queue[v,rank];take=min(remaining[v],pos[v,m],cash[m])
            if take>0:remaining[v]-=take;pos[v,m]-=take;cash[m]-=take;paid+=take
            if remaining[v]==0:break
    return paid

@njit(cache=True)
def replay(cash0,pos0,queue,lengths,requests,order,events,timestamps,start_time):
    cash=cash0.copy();pos=pos0.copy();remaining=requests.copy();total=requests.sum()
    initial=pay(cash,pos,queue,lengths,remaining,order);incoming=np.zeros(3,np.int64);clipped=0
    if remaining.sum()==0:return 0.,False,1.,initial,incoming,clipped
    for j in range(len(events)):
        m,kind,amount,own=events[j]
        if own:continue
        if kind<=2:
            cash[m]+=amount;incoming[kind]+=amount
            pay(cash,pos,queue,lengths,remaining,order)
            if remaining.sum()==0:return (timestamps[j]-start_time)/3600.,False,1.,initial,incoming,clipped
        else:
            take=min(amount,cash[m]);cash[m]-=take;clipped+=amount-take
        assert cash[m]>=0
    return 168.,True,(total-remaining.sum())/total,initial,incoming,clipped

def b1():
    p=pd.read_parquet(O/'positions.parquet');v=pd.read_parquet(O/'vault_states.parquet');m=pd.read_parquet(O/'market_states.parquet')
    d=pd.read_parquet(R/'additional_evidence/panel_evidence/raw/market_operations.parquet')
    if (O/'tail_operations.parquet').exists():
        assert (O/'tail_cash_reconciliation.csv').exists(),'Tail reconciliation must pass before use'
        assert pd.read_csv(O/'tail_cash_reconciliation.csv').gap.abs().max()<=1
        d=pd.concat([d,pd.read_parquet(O/'tail_operations.parquet')],ignore_index=True)
    d=d.sort_values(['block','log_index']);assert not d.duplicated(['tx','log_index']).any()
    assert d.owner.str.lower().eq(d.owner).all(),'Normalize owner addresses before own-operation removal'
    markets=sorted(set(d.market)|set(p.market));market_map={k:i for i,k in enumerate(markets)};vaults=sorted(v.vault.unique());vmap={k:i for i,k in enumerate(vaults)}
    kindmap={'Supply':0,'Repay':1,'Liquidation':2,'Borrow':3,'Withdraw':4}
    ev=np.column_stack([d.market.map(market_map),d.kind.map(kindmap),d.assets_micro,d.owner.isin(vaults).astype(int)]).astype(np.int64)
    blocks=d.block.to_numpy();times=d.timestamp.to_numpy();last_block=int(d.block.max());rows=[]
    coverage_end=last_block
    if (O/'tail_coverage.json').exists():coverage_end=json.loads((O/'tail_coverage.json').read_text())['end']
    full=pd.read_parquet(O/'full_daily_market_cash.parquet');assert full.gap.abs().max()<=1
    for count,(day,g) in enumerate(p[p.date.between('2025-01-16','2026-03-30')].groupby('date')):
        vg=v[v.date.eq(day)].set_index('vault').reindex(vaults);block=int(vg.block.iloc[0]);start=int(vg.timestamp.iloc[0]);endblock=block+7*43200
        cash=np.zeros(len(markets),np.int64)
        for z in m[m.date.eq(day)].itertuples():cash[market_map[z.market]]=int(z.cash)
        for z in full[full.date.eq(day)].itertuples():cash[market_map[z.market]]=int(z.cash)
        positions=np.zeros((10,len(markets)),np.int64);queue=np.full((10,32),-1,np.int64);lengths=np.zeros(10,np.int64)
        for z in g.itertuples():
            vi=vmap[z.vault];mi=market_map[z.market];positions[vi,mi]=int(z.position);queue[vi,z.rank]=mi;lengths[vi]=max(lengths[vi],z.rank+1)
        assets=vg.assets.to_numpy(np.int64);desc=np.argsort(-assets,kind='stable');asc=np.argsort(assets,kind='stable')
        lo=np.searchsorted(blocks,block,side='right');hi=np.searchsorted(blocks,endblock,side='right')
        for ordername,order in [('large_first',desc),('small_first',asc)]:
            for f in [5,10,25]:
                req=assets*f//100;tau,censored,fraction,initial,incoming,clipped=replay(cash,positions,queue,lengths,req,order,ev[lo:hi],times[lo:hi],start)
                valid=(not censored) or endblock<=coverage_end
                rows.append(dict(date=day,f=f,order=ordername,tau=tau if valid else np.nan,censored=censored if valid else None,paid_fraction=fraction if valid else np.nan,initial_paid_micro=initial,request_micro=int(req.sum()),supply_inflow_micro=int(incoming[0]),repay_inflow_micro=int(incoming[1]),liquidation_inflow_micro=int(incoming[2]),clipped_outflow_micro=clipped,horizon_complete=endblock<=coverage_end,valid_result=valid))
        if count%50==0:print('B1',count+1,439,flush=True)
    q=pd.DataFrame(rows);q.to_csv(O/'B1_daily_replay.csv',index=False)
    reference=pd.read_csv(O/'joint_requests.csv');primary=q[q.order.eq('large_first')].merge(reference[['date','f','all_pass','excluded']],on=['date','f']);primary['reference_zero']=primary.all_pass&~primary.excluded;primary['tau_zero']=primary.initial_paid_micro.eq(primary.request_micro);primary['mismatch']=primary.reference_zero.ne(primary.tau_zero);primary.to_csv(O/'B3_daily_checks.csv',index=False)
    check=primary.groupby('f').agg(dates=('date','size'),tau_zero=('tau_zero','sum'),reference_zero=('reference_zero','sum'),mismatch=('mismatch','sum'),valid_results=('valid_result','sum'));check.to_csv(O/'B3_summary.csv')
    if not q.valid_result.all():
        print('B1 incomplete future coverage; summary and regressions withheld',flush=True);return
    desc=[];sources=[];observed_sources=[]
    for (order,f),g in q.groupby(['order','f']):
        g=g.copy();g.censored=g.censored.astype(bool)
        desc.append(dict(order=order,f=f,days=len(g),zero=int(g.tau.eq(0).sum()),median=g.tau.median(),p75=g.tau.quantile(.75),p90=g.tau.quantile(.9),within1=g.tau.le(1).mean(),within6=g.tau.le(6).mean(),within24=g.tau.le(24).mean(),censored=int(g.censored.sum()),paid_fraction_7d=g.paid_fraction.median()))
        resolved=g[~g.censored];s=resolved[['supply_inflow_micro','repay_inflow_micro','liquidation_inflow_micro']].sum();total=int(s.sum())
        for k,a in s.items():sources.append(dict(order=order,f=f,source=k,amount_micro=int(a),share=a/total if total else np.nan,completed_dates=len(resolved)))
        all_s=g[['supply_inflow_micro','repay_inflow_micro','liquidation_inflow_micro']].sum();all_total=int(all_s.sum())
        for k,a in all_s.items():observed_sources.append(dict(order=order,f=f,source=k,amount_micro=int(a),share=a/all_total if all_total else np.nan,dates=len(g),censored_dates=int(g.censored.sum())))
    pd.DataFrame(desc).to_csv(O/'B1_descriptives.csv',index=False);pd.DataFrame(sources).to_csv(O/'B2_sources.csv',index=False);pd.DataFrame(observed_sources).to_csv(O/'B2_sources_observed.csv',index=False)
    daily=calendar(pd.read_csv(O/'daily.csv'));b=q[q.f.eq(25)&q.order.eq('large_first')].merge(daily,on='date',validate='one_to_one');b['log_tau']=np.log1p(b.tau);b['log_assets']=np.log(b.assets/1e6);b.to_csv(O/'B_regression_data.csv',index=False)
    rows=[]
    for name,extra in [('baseline',''),('windows',' + W1 + W2')]:
        model=smf.ols('log_tau ~ Dup + Util + log_assets + C(month) + C(weekday)'+extra,b).fit(cov_type='HAC',cov_kwds={'maxlags':7,'use_correction':True},use_t=True)
        for term in ['Dup','Util','log_assets']+(['W1','W2'] if extra else []):rows.append(dict(spec=name,term=term,coef=model.params[term],se=model.bse[term],t=model.tvalues[term],p=model.pvalues[term],N=int(model.nobs),R2=model.rsquared))
    # Cox on observed hours with ties at zero handled as a common epsilon.
    from lifelines import CoxPHFitter
    x=pd.concat([b[['Dup','Util','log_assets']],pd.get_dummies(b[['month','weekday']].astype(str),drop_first=True,dtype=float)],axis=1)
    x['duration']=np.maximum(b.tau,1e-6);x['event']=~b.censored.astype(bool)
    cox=CoxPHFitter();cox.fit(x,duration_col='duration',event_col='event',robust=True)
    cox.summary.to_csv(O/'B_cox_all_terms.csv')
    for term in ['Dup','Util','log_assets']:
        z=cox.summary.loc[term];rows.append(dict(spec='Cox',term=term,coef=z['coef'],se=z['se(coef)'],t=z['z'],p=z['p'],N=len(b),R2=np.nan))
    pd.DataFrame(rows).to_csv(O/'B_regressions.csv',index=False)
    print('B done',flush=True)

if __name__=='__main__':
    assert json.loads((O/'gate_results.json').read_text())['reference_gate']
    a1();b1()
