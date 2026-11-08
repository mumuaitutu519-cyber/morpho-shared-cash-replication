"""Exact current Table 8 samples, new inference, isolated sample and flow outcomes."""
import json,hashlib
import numpy as np
import pandas as pd
from settings import OUT,PE,RAW,ADD
from statistics_common import event_fit,markdown,cell

H=['m1','pre','event','p1','p6','p24','p72','p168']


def run():
    e=pd.read_csv(PE/'borrow_event_list.csv')
    candidates=pd.read_csv(PE/'borrow_event_candidates.csv')
    q=candidates[candidates.threshold_pass].sort_values(['timestamp','block','first_log_index'])
    meta=[]
    for r in e.itertuples():
        g=q[q.market.eq(r.market)]
        if r.event_type=='borrow':g=g[~(g.tx.eq(r.tx)&g.block.eq(r.block))]
        after=g[(g.timestamp>r.timestamp)|((g.timestamp==r.timestamp)&((g.block>r.block)|((g.block==r.block)&g.first_log_index.gt(r.first_log_index))))]
        before=g[(g.timestamp<r.timestamp)|((g.timestamp==r.timestamp)&g.block.le(r.block))]
        nxt=float(after.timestamp.min()) if len(after) else np.inf
        prv=float(before.timestamp.max()) if len(before) else -np.inf
        meta.append(dict(event_id=r.event_id,event_timestamp=int(r.timestamp),event_block=int(r.block),
                         calendar_date=pd.Timestamp(r.timestamp,unit='s',tz='UTC').strftime('%Y-%m-%d'),
                         next_qualifying_timestamp=nxt,previous_qualifying_timestamp=prv,
                         isolated168=(prv<r.timestamp-168*3600 and nxt>r.timestamp+168*3600)))
    meta=pd.DataFrame(meta)
    raw=pd.read_parquet(PE/'event_market_horizons.parquet').merge(meta,on='event_id',validate='many_to_one')
    raw.to_parquet(OUT/'data/table8_all_horizons.parquet',index=False)
    estimates=[];coverage=[];samples=[]
    for panel,y in [('A','delta_market_duplication'),('B','joint_million')]:
        for col,kind in [(1,'borrow'),(2,'borrow'),(3,'borrow'),(4,'placebo')]:
            d=raw[raw.event_type.eq(kind)].dropna(subset=[y]).copy()
            good=d.groupby('event_id').horizon.nunique()
            d=d[d.event_id.isin(good[good.eq(9)].index)].copy()
            if col==2:d=d[d.timestamp.lt(d.next_qualifying_timestamp)|d.horizon.isin(['m24','m1','pre','event'])].copy()
            ids=d[['event_id','vault_count']].drop_duplicates()
            d['count_centered']=d.vault_count-ids.vault_count.mean()
            terms=[]
            for h in H:
                d['h_'+h]=d.horizon.eq(h).astype(float);terms.append('h_'+h)
            if col==3:
                for h in H:
                    d['count_'+h]=d['h_'+h]*d.count_centered;terms.append('count_'+h)
            result=event_fit(d,y,terms)
            result['panel']=panel;result['column']=col;result['sample']='main'
            estimates.append(result)
            samples.append(d[['event_id','event_type','horizon','market','calendar_date','timestamp',y]].assign(panel=panel,column=col))
            coverage.append(dict(panel=panel,column=col,N=len(d),events=d.event_id.nunique(),market_clusters=d.market.nunique(),
                                 event_block_events=d[d.horizon.eq('event')].event_id.nunique(),
                                 p168_events=d[d.horizon.eq('p168')].event_id.nunique()))
        # Isolated definition is fixed by the manuscript: no qualifying threshold borrow +/-168h.
        d=raw[raw.event_type.eq('borrow')&raw.isolated168].dropna(subset=[y]).copy()
        good=d.groupby('event_id').horizon.nunique()
        d=d[d.event_id.isin(good[good.eq(9)].index)].copy()
        for h in H:d['h_'+h]=d.horizon.eq(h).astype(float)
        z=event_fit(d,y,['h_'+h for h in H]);z['panel']=panel;z['column']=0;z['sample']='isolated168';estimates.append(z)
    results=pd.concat(estimates,ignore_index=True)
    results.to_csv(OUT/'tables/table8_reestimated_unrounded.csv',index=False)
    pd.DataFrame(coverage).to_csv(OUT/'tables/table8_sample_coverage.csv',index=False)
    pd.concat(samples,ignore_index=True).to_parquet(OUT/'data/table8_regression_samples.parquet',index=False)
    for covariance in ['event_original','market','market_date']:
        for panel in ['A','B']:
            rows=[]
            for h in H:
                values=[]
                for col in [1,2,3,4]:
                    term=('count_' if col==3 else 'h_')+h
                    r=results[results.panel.eq(panel)&results.column.eq(col)&results['sample'].eq('main')&results.covariance.eq(covariance)&results.term.eq(term)].iloc[0]
                    values.append(cell(r.coefficient,r.t,r.p))
                rows.append([h]+values)
            frame=pd.DataFrame(rows,columns=['Horizon','(1) Borrow events','(2) Censored','(3) × Vaults','(4) Placebo'])
            (OUT/f'tables/Table8_Panel_{panel}_{covariance}.md').write_text(markdown(frame)+'\n')
    # Use full nine-state Panel B sample to match 834 manuscript events.
    b=raw[raw.event_type.eq('borrow')].dropna(subset=['joint_million'])
    complete=b.groupby('event_id').horizon.nunique()
    chosen=e[e.event_id.isin(complete[complete.eq(9)].index)].merge(meta,on='event_id',validate='one_to_one')
    assert len(chosen)==834
    isolated=chosen[chosen.isolated168]
    assert len(isolated)==80
    chosen.to_csv(OUT/'data/table8_column2_event_list.csv',index=False)
    isolated.to_csv(OUT/'data/table8_80_isolated_events.csv',index=False)
    universe=sorted(pd.read_parquet(RAW/'market_operations.parquet',columns=['market']).market.unique())
    overlap=[]
    for market in universe:
        g=chosen[chosen.market.eq(market)]
        row={'market':market,'events':len(g),'all_qualifying_borrows':int(q.market.eq(market).sum())}
        for hour in [24,72,168]:
            count=int((g.next_qualifying_timestamp-g.timestamp<=hour*3600).sum())
            row[f'next_within_{hour}h_events']=count
            row[f'next_within_{hour}h_share']=count/len(g) if len(g) else np.nan
        overlap.append(row)
    pd.DataFrame(overlap).to_csv(OUT/'tables/borrow_overlap_by_market.csv',index=False)
    # Recorded flows after the event closing block, through each observed target block.
    ledger=pd.read_parquet(RAW/'market_operations.parquet')
    if (ADD/'tail_operations.parquet').exists():ledger=pd.concat([ledger,pd.read_parquet(ADD/'tail_operations.parquet')],ignore_index=True)
    ledger=ledger.sort_values(['block','log_index'])
    samplevaults=set(pd.read_parquet(ADD/'vault_states.parquet').vault)
    marketdata={}
    for market,g in ledger.groupby('market'):
        sign=g.kind.map({'Supply':1,'Withdraw':-1}).fillna(0).to_numpy()
        amount=g.assets_micro.to_numpy(np.int64)
        series=np.column_stack([sign*amount,sign*amount*g.owner.isin(samplevaults).to_numpy(),
                                amount*g.kind.eq('Repay').to_numpy(),amount*g.kind.isin(['Repay','Liquidation']).to_numpy()]).astype(np.int64)
        marketdata[market]=(g.block.to_numpy(),np.vstack([np.zeros(4,np.int64),series.cumsum(axis=0)]))
    d=b[b.event_id.isin(chosen.event_id)].copy()
    boundary=chosen[chosen.next_qualifying_timestamp.eq(chosen.timestamp)]
    boundary.to_csv(OUT/'data/table8_same_timestamp_censor_boundary.csv',index=False)
    d=d[d.timestamp.lt(d.next_qualifying_timestamp)|d.horizon.isin(['m24','m1','pre','event'])].copy()
    flowrows=[]
    for r in d.itertuples():
        blocks,cumulative=marketdata[r.market]
        start=np.searchsorted(blocks,r.event_block,side='right')
        stop=np.searchsorted(blocks,r.block,side='right')
        values=cumulative[stop]-cumulative[start] if r.horizon.startswith('p') and r.horizon!='pre' else np.zeros(4,np.int64)
        flowrows.append(dict(event_id=r.event_id,market=r.market,calendar_date=r.calendar_date,horizon=r.horizon,
                             timestamp=r.timestamp,block=r.block,net_supply_all=values[0]/1e12,
                             net_supply_sample=values[1]/1e12,repayments=values[2]/1e12,repayments_with_liquidation=values[3]/1e12))
    flows=pd.DataFrame(flowrows)
    flow_estimates=[]
    for y in ['net_supply_all','net_supply_sample','repayments','repayments_with_liquidation']:
        for h in H:flows['h_'+h]=flows.horizon.eq(h).astype(float)
        r=event_fit(flows,y,['h_'+h for h in H]);r['outcome']=y;flow_estimates.append(r)
    flows.to_parquet(OUT/'data/postborrow_recorded_flows.parquet',index=False)
    pd.concat(flow_estimates).to_csv(OUT/'tables/postborrow_flow_estimates.csv',index=False)
    notes={'threshold':'borrow transaction > 10% preceding-block idle cash; previous qualifying-borrow cooldown 24h',
           'isolation':'no other qualifying borrow in same market within +/-168h; threshold borrows need not survive cooldown',
           'censoring':'drop post-event observations at/after next qualifying borrow; preserve pre/event states to reproduce current manuscript',
           'same_timestamp_event_boundaries':len(boundary),
           'event_baseline':'m24 omitted; outcome changes from pre-event block; event fixed effects',
           'col3':'horizon x pre-event vault count centered across complete events, with main horizon effects',
           'bootstrap':'null-imposed restricted wild cluster bootstrap-t; market Rademacher signs; 999 draws; seed 20261018; p=(1+exceedances)/1000',
           'cluster_counts':{'historical_markets':len(universe),'markets_with_qualifying_borrows':int(q.market.nunique()),'main_Table8_markets':int(chosen.market.nunique())},
           'isolated_events':len(isolated),'following_counts':{str(h):int((chosen.next_qualifying_timestamp-chosen.timestamp<=h*3600).sum()) for h in [24,72,168]},
           'postborrow_flows':'million USDC, after event block through observed horizon block; same 834-event censored sample as Panel B column2; pre/event cumulative flows zero by definition',
           'boundary':'isolation is conditional on ledger coverage; no unobserved boundary periods filled with zero'}
    (OUT/'logs/step2_status.json').write_text(json.dumps(notes,indent=2))
    print('Step2 complete:',notes['cluster_counts'],notes['following_counts'],flush=True)


if __name__=='__main__':run()
