"""Offline revision-stage accounting comparisons; no network or regressions."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict
import csv, hashlib, json, statistics
import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/revision21'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x): (OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def cs(n,rows):
    pd.DataFrame(rows).to_csv(OUT/n,index=False)
def read(n):return pd.read_csv(ROOT/n,dtype=str)
def qstat(xs):
    a=np.array([float(x) for x in xs]);return {k:float(np.quantile(a,q)) for k,q in [('min',0),('p25',.25),('median',.5),('p75',.75),('p90',.9),('p95',.95),('max',1)]}
def main():
    OUT.mkdir(exist_ok=True)
    paths=['reports/revision6/withdrawal_capacity.csv','reports/revision5/vault_economic_events.parquet',
      'reports/revision6/domain_6_operations.csv','reports/revision6/domain_6_matches.csv',
      'reports/revision6/domain_6_first_disposition_manifest.json','reports/revision6/domain_6_market_links.csv',
      'reports/revision18/funded_positions.csv','reports/revision18/weekly_comparison.csv',
      'reports/revision17/quarter_withdrawal_execution.csv','reports/revision21/ANALYSIS_PLAN.md',
      'reports/revision5/market_liquidity_validation.csv']
    save('input_manifest.json',{p:{'sha256':sha(ROOT/p),'bytes':(ROOT/p).stat().st_size} for p in paths})
    states=read(paths[0]).set_index('date');assert len(states)==320
    ds=states.loc['2025-01-16':'2025-11-30'];assert len(ds)==319
    ev=pd.read_parquet(ROOT/paths[1]);assert len(ev)==145957 and not ev.duplicated(['tx','log_index']).any()
    own=ev[ev.onBehalf.eq(PROXY)&ev.type.isin(['Deposit','Withdraw'])].copy()
    ops=read(paths[2]);mt=read(paths[3]);manifest=json.loads((ROOT/paths[4]).read_text())
    assert len(manifest['items'])==704 and len(mt)==3235
    tx_time={t:int(g.destination_timestamp.iloc[0]) for t,g in mt.groupby('destination_tx')}
    assert all(g.destination_timestamp.nunique()==1 for _,g in mt.groupby('destination_tx'))
    od=ops[ops.operation.str.endswith('deposit') & ops.validated_native_transfer.eq('True')].copy()
    od['timestamp']=od.destination_tx.map(tx_time)
    od['date']=pd.to_datetime(od.timestamp,unit='s',utc=True).dt.strftime('%Y-%m-%d')
    assert len(od)==231
    vd=od[od.operation.eq('Vault deposit')];assert len(vd)==94
    ix=own.set_index(['tx','log_index'])
    cohort=[]
    for row in vd.itertuples():
        a=ix.loc[(row.destination_tx,int(row.operation_log))]
        assert a.type=='Deposit' and int(a.assets_raw)==int(row.amount_micro_usdc)
        assert int(a.shares_raw)==int(row.share_base_units) and a.timestamp==row.timestamp
        cohort.append({'tx':row.destination_tx,'log_index':int(row.operation_log),'date':row.date,
            'assets_micro':str(int(row.amount_micro_usdc)),'shares_raw':str(int(row.share_base_units))})
    cs('cohort_vault_event_join.csv',cohort)
    cohortkeys={(x['tx'],x['log_index']) for x in cohort}
    summary={'cohort':{},'stock':{}}
    for name,d in [('all_facilities',od),('psm',od[od.operation.eq('PSM deposit')]),('vault',vd)]:
        bounds=manifest['summary'] if name=='all_facilities' else manifest['summary']['operation_bounds'][name]
        summary['cohort'][name]={'events':len(d),'transactions':d.destination_tx.nunique(),
          'assets_micro':str(sum(map(int,d.amount_micro_usdc))),
          'lower_micro':bounds['lower_micro'],'upper_micro':bounds['upper_micro'],
          'first_date':d.date.min(),'last_date':d.date.max(),
          'in_state_window_events':int(d.date.between('2025-01-16','2025-11-30').sum()),
          'shares_raw':str(sum(map(int,d.share_base_units))) if name=='vault' else None}
    flows=[]
    for date,st in ds.iterrows():
        previous=(pd.Timestamp(date)-pd.Timedelta(days=1)).strftime('%Y-%m-%d');op=states.loc[previous]
        day=ev[ev.date.eq(date)];dep=day[day.type.eq('Deposit')&day.onBehalf.eq(PROXY)]
        wd=day[day.type.eq('Withdraw')&day.onBehalf.eq(PROXY)];tr=day[day.type.eq('Transfer')]
        mint=sum(map(int,dep.shares_raw));burn=sum(map(int,wd.shares_raw))
        tin=sum(map(int,tr.loc[tr.to.eq(PROXY),'shares_raw']));tout=sum(map(int,tr.loc[tr['from'].eq(PROXY),'shares_raw']))
        delta=int(st.treasury_shares)-int(op.treasury_shares)
        residual=delta-mint+burn-tin+tout
        flows.append({'date':date,'opening_shares_raw':str(op.treasury_shares),
            'deposit_micro':str(sum(map(int,dep.assets_raw))),'withdraw_micro':str(sum(map(int,wd.assets_raw))),
            'minted_shares_raw':str(mint),'burned_shares_raw':str(burn),'transfer_in_raw':str(tin),'transfer_out_raw':str(tout),
            'unexplained_share_change_raw':str(residual),'closing_shares_raw':str(st.treasury_shares),
            'prior_claim_micro':str(op.claim_micro),'closing_claim_micro':str(st.claim_micro),
            'successful_withdraw_events':len(wd),'successful_withdraw_transactions':wd.tx.nunique()})
    cs('daily_flow_stock_reconciliation.csv',flows)
    for key in ['deposit_micro','withdraw_micro','minted_shares_raw','burned_shares_raw','transfer_in_raw','transfer_out_raw','unexplained_share_change_raw']:
        summary['stock'][key]=str(sum(int(x[key]) for x in flows))
    st=summary['stock'];st.update({'opening_shares_raw':states.loc['2025-01-15','treasury_shares'],
       'ending_shares_raw':states.loc['2025-11-30','treasury_shares'],
       'opening_claim_micro':states.loc['2025-01-15','claim_micro'],'ending_claim_micro':states.loc['2025-11-30','claim_micro'],
       'residual_nonzero_days':sum(int(x['unexplained_share_change_raw'])!=0 for x in flows),
       'residual_negative_days':sum(int(x['unexplained_share_change_raw'])<0 for x in flows),
       'source_attributed_ending_stock':None})
    assert int(st['ending_shares_raw'])==int(st['opening_shares_raw'])+int(st['minted_shares_raw'])-int(st['burned_shares_raw'])+int(st['transfer_in_raw'])-int(st['transfer_out_raw'])+int(st['unexplained_share_change_raw'])
    sampleown=own[own.date.between('2025-01-16','2025-11-30')]
    st['deposit_events']=int(sampleown.type.eq('Deposit').sum());st['withdraw_events']=int(sampleown.type.eq('Withdraw').sum())
    st['cohort_share_mints_fraction_of_all_mints']=sum(int(x['shares_raw']) for x in cohort)/int(st['minted_shares_raw'])
    st['cohort_asset_deposit_fraction']=int(summary['cohort']['vault']['assets_micro'])/int(st['deposit_micro'])
    st['valuation_and_omitted_event_residual_micro']=str(int(st['ending_claim_micro'])-int(st['opening_claim_micro'])-int(st['deposit_micro'])+int(st['withdraw_micro']))
    save('flow_stock_summary.json',summary)

    scenarios=[];perday=[]
    old=read(paths[8]).set_index('date')
    for pct in [5,10,25,50,100]:
        flags=[]
        for date,r in ds.iterrows():
            requested=int(r.claim_micro)*pct//100;flag=requested>int(r.max_withdraw_micro);flags.append(flag)
            if pct==25:assert flag==(old.loc[date,'status']=='liquidity_revert'),old.loc[date,'status']
            perday.append({'date':date,'request_pct':pct,'request_micro':str(requested),'capacity_micro':r.max_withdraw_micro,'capacity_exceeded':flag,'execution_checked':pct==25})
        scenarios.append({'request_pct':pct,'days':319,'capacity_exceeded_days':sum(flags),'fraction':sum(flags)/319,'execution_checked':pct==25})
    cs('withdrawal_scenarios.csv',scenarios);cs('withdrawal_scenarios_daily.csv',perday)
    success=[]
    for (date,tx),g in sampleown[sampleown.type.eq('Withdraw')].groupby(['date','tx']):
        prev=(pd.Timestamp(date)-pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        amount=sum(map(int,g.assets_raw));claim=int(states.loc[prev,'claim_micro']);assert claim>0
        success.append({'date':date,'tx':tx,'amount_micro':str(amount),'prior_close_claim_micro':str(claim),'amount_to_prior_claim':amount/claim,'events':len(g)})
    cs('successful_withdrawal_transactions.csv',success)
    daily=[int(x['withdraw_micro'])/int(x['prior_claim_micro']) for x in flows]
    txratios=[x['amount_to_prior_claim'] for x in success]
    withsum={'transactions':len(success),'events':sum(x['events'] for x in success),'zero_withdrawal_days':sum(x==0 for x in daily),
       'all_days':319,'transaction_amount_million':qstat([int(x['amount_micro'])/1e12 for x in success]),
       'transaction_ratio_pct':qstat([100*x for x in txratios]),'daily_ratio_pct':qstat([100*x for x in daily]),
       'threshold_exceedances':[{'pct':p,'transactions':sum(100*int(x['amount_micro'])>p*int(x['prior_close_claim_micro']) for x in success),'days':sum(100*int(x['withdraw_micro'])>p*int(x['prior_claim_micro']) for x in flows)} for p in [5,10,25,50,100]],
       'denominator':'Prior daily close owner claim; successful events only; neither pre-transaction claim nor latent demand'}
    save('successful_withdrawal_summary.json',withsum)

    # Exact symmetric (Shapley) decomposition of a ratio at observed endpoints.
    mindate=min(ds.index,key=lambda d:Fraction(int(ds.loc[d,'max_withdraw_micro']),int(ds.loc[d,'claim_micro'])))
    a,b=ds.loc[mindate],ds.iloc[-1];w0,w1=int(a.max_withdraw_micro),int(b.max_withdraw_micro);c0,c1=int(a.claim_micro),int(b.claim_micro)
    cw=Fraction(w1-w0,2)*(Fraction(1,c0)+Fraction(1,c1));cc=Fraction(w0+w1,2)*(Fraction(1,c1)-Fraction(1,c0))
    assert cw+cc==Fraction(w1,c1)-Fraction(w0,c0)
    decomp={'start_date':mindate,'end_date':ds.index[-1],'W0_micro':str(w0),'W1_micro':str(w1),'C0_micro':str(c0),'C1_micro':str(c1),
        'coverage_start_pct':100*w0/c0,'coverage_end_pct':100*w1/c1,'capacity_contribution_pp':float(100*cw),'claim_contribution_pp':float(100*cc)}
    for label,g in [('first30',ds.iloc[:30]),('last30',ds.iloc[-30:])]:
        decomp[label]={'median_capacity_million':statistics.median(int(x)/1e12 for x in g.max_withdraw_micro),
           'median_claim_million':statistics.median(int(x)/1e12 for x in g.claim_micro),
           'median_ratio_pct':statistics.median(int(r.max_withdraw_micro)/int(r.claim_micro)*100 for r in g.itertuples())}
    cashseries=read(paths[10]).set_index('timestamp')
    common0=int(cashseries.loc[a.boundary_timestamp,'reconstructed_liquidity_raw'])
    common1=int(cashseries.loc[b.boundary_timestamp,'reconstructed_liquidity_raw'])
    assert common0==w0
    decomp.update({'common_market_cash_start_micro':str(common0),'common_market_cash_end_micro':str(common1),
       'common_market_cash_change_micro':str(common1-common0),
       'capacity_beyond_common_cash_end_micro':str(w1-common1),
       'capacity_change_share_accounted_by_common_cash':(common1-common0)/(w1-w0),
       'daily_capped_common_cash_exact_capacity_dates':sum(min(int(r.claim_micro),int(cashseries.loc[r.boundary_timestamp,'reconstructed_liquidity_raw']))==int(r.max_withdraw_micro) for r in ds.itertuples())})
    save('capacity_decomposition.json',decomp)

    pos=read(paths[6]);weekly=read(paths[7]).set_index(['vault','date']);joint=[];alloc=[];sizes=[];lperror=0
    for date,g in pos.groupby('date',sort=True):
        separate=sum(min(int(r.position_micro),int(r.market_cash_micro)) for r in g.itertuples())
        jointcash=0;cashmap={};allocmap=defaultdict(Fraction)
        for market,h in g.groupby('market'):
            assert h.market_cash_micro.nunique()==h.market_supply_micro.nunique()==h.market_borrow_micro.nunique()==1
            cash=int(h.market_cash_micro.iloc[0]);P=sum(map(int,h.position_micro));S=int(h.market_supply_micro.iloc[0]);assert P<=S
            usable=min(P,cash);jointcash+=usable;cashmap[market]=cash
            for r in h.itertuples():
                x=Fraction(int(r.position_micro)*usable,P);allocmap[r.vault]+=x
                alloc.append({'date':date,'vault':r.vault,'market':market,'position_micro':r.position_micro,
                    'pro_rata_allocated_micro':float(x),'allocation_numerator':str(x.numerator),'allocation_denominator':str(x.denominator)})
        assert sum(allocmap.values(),Fraction(0))==jointcash and separate>=jointcash
        # Separate linear allocation program checks the closed-form joint upper bound.
        rows=list(g.itertuples());A=np.array([[int(r.market==m) for r in rows] for m in cashmap],dtype=float)
        fit=linprog(-np.ones(len(rows)),A_ub=A,b_ub=np.array(list(cashmap.values()))/1e12,
           bounds=[(0,int(r.position_micro)/1e12) for r in rows],method='highs')
        assert fit.success;err=abs(-fit.fun-jointcash/1e12);lperror=max(lperror,err);assert err<1e-7
        out={'date':date,'individually_counted_micro':str(separate),'joint_cash_upper_micro':str(jointcash),
          'duplicate_cash_micro':str(separate-jointcash),'duplicate_fraction_of_separate':(separate-jointcash)/separate,
          'separate_over_joint':separate/jointcash,'markets':g.market.nunique()}
        for v in ['spark','moonwell','gauntlet']:
            z=weekly.loc[(v,date)];out[v+'_pro_rata_cash_to_assets_pct']=float(allocmap[v]/int(z.total_assets_micro)*100)
        joint.append(out)
        focal=g[g.vault.eq('spark')];C=int(states.loc[date,'claim_micro'])
        for scale in [Fraction(1,10),Fraction(1,4),Fraction(1,2),Fraction(1)]:
            K=sum((min(scale*int(r.position_micro),int(r.market_cash_micro)) for r in focal.itertuples()),Fraction(0))
            frac=min(Fraction(1),K/(scale*C))
            sizes.append({'date':date,'position_scale':float(scale),'coverage_fraction':float(frac),'quarter_shortfall':frac<Fraction(1,4)})
    cs('shared_cash_weekly.csv',joint);cs('shared_cash_allocation.csv',alloc);cs('fixed_portfolio_size_scenarios.csv',sizes)
    shared={'weekly_dates':46,'duplicate_positive_dates':sum(int(r['duplicate_cash_micro'])>0 for r in joint),
       'separate_million':qstat([int(r['individually_counted_micro'])/1e12 for r in joint]),
       'joint_million':qstat([int(r['joint_cash_upper_micro'])/1e12 for r in joint]),
       'duplicate_million':qstat([int(r['duplicate_cash_micro'])/1e12 for r in joint]),
       'duplicate_pct':qstat([r['duplicate_fraction_of_separate']*100 for r in joint]),
       'lp_max_error_million':lperror,
       'pro_rata_cash_assets_median_pct':{v:statistics.median(x[v+'_pro_rata_cash_to_assets_pct'] for x in joint) for v in ['spark','moonwell','gauntlet']},
       'size_scenarios':[{'scale':s,'median_coverage_pct':statistics.median(x['coverage_fraction']*100 for x in sizes if x['position_scale']==s),
          'quarter_shortfall_dates':sum(x['quarter_shortfall'] for x in sizes if x['position_scale']==s)} for s in [.1,.25,.5,1]],
       'scope':'Selected three vault portfolios, static cash-only allocation upper bound before outside withdrawals; not joint contract execution'}
    for d in sorted({r['date'] for r in sizes}):
        ordered=[x['coverage_fraction'] for x in sizes if x['date']==d];assert ordered==sorted(ordered,reverse=True)
    save('shared_cash_summary.json',shared)
    # Pedagogical amounts are whole USDC, not empirical observations.
    events=[('arrival',60),('other',10),('other_out',30),('deposit',50),('arrival',20),('deposit',20)]
    states_ex={(0,0,() )};cash=20
    for kind,amount in events:
        if kind=='arrival':cash+=amount;states_ex={(f+amount,d,q) for f,d,q in states_ex}
        elif kind=='other':cash+=amount
        else:
            nxt=set()
            for f,d,q in states_ex:
                for take in range(max(0,amount-(cash-f)),min(f,amount)+1):
                    nxt.add((f-take,d+take*(kind=='deposit'),q+(take,)))
            cash-=amount;states_ex=nxt
        assert states_ex and cash>=0
    lo=min(d for _,d,_ in states_ex);hi=max(d for _,d,_ in states_ex);assert (lo,hi)==(40,70)
    save('funding_example.json',{'type':'Artificial numerical explanation; not observations','opening':20,'events':events,'deposit_total':70,'lower':lo,'upper':hi,
       'lower_witness':min(q for _,d,q in states_ex if d==lo),'upper_witness':min(q for _,d,q in states_ex if d==hi),'feasible_terminal_allocations':len(states_ex)})
    save('validation.json',{'status':'PASS','exact_vault_cohort_joins':94,'daily_reconciliations_with_explicit_residual':319,
       'scenario_monotonicity':True,'quarter_capacity_rule_matches_all_archived_execution':True,'joint_cash_lp_dates':46,
       'lp_max_error_million':lperror,'integer_funding_example_endpoints':[40,70],'regressions_reestimated':False,
       'raw_share_ledger_complete':False,'source_attributed_ending_claim_identified':False})
    print(json.dumps({'flow_stock':summary,'withdrawals':withsum,'scenarios':scenarios,'decomposition':decomp,'shared_cash':shared},indent=2))
if __name__=='__main__':main()
