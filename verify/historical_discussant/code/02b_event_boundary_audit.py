"""Compare manuscript's sample-bounded event filter with full future-ledger coverage."""
import json
import numpy as np
import pandas as pd
from settings import OUT,PE,RAW,ADD
from statistics_common import event_fit


def run():
    tail=pd.read_parquet(ADD/'tail_operations.parquet').sort_values(['block','log_index'])
    cash=pd.read_parquet(ADD/'full_daily_market_cash.parquet')
    cash={r.market:int(r.cash) for r in cash[cash.date.eq('2026-03-30')].itertuples()}
    # The threshold uses cash at the preceding block, not cash immediately before each log.
    extra=[]
    for block,g in tail.groupby('block',sort=True):
        opening=cash.copy()
        borrows=g[g.kind.eq('Borrow')].groupby(['market','tx'],as_index=False).agg(borrow_micro=('assets_micro','sum'),timestamp=('timestamp','first'),first_log_index=('log_index','min'))
        for r in borrows.itertuples():
            if int(r.borrow_micro)*10>opening[r.market]:
                extra.append(dict(market=r.market,tx=r.tx,block=int(block),timestamp=int(r.timestamp),borrow_micro=int(r.borrow_micro),preblock_cash_micro=opening[r.market],first_log_index=int(r.first_log_index),threshold_pass=True))
        for r in g.itertuples():cash[r.market]+=int(r.assets_micro)*(1 if r.kind in ['Supply','Repay','Liquidation'] else -1)
        assert min(cash.values())>=0
    extra=pd.DataFrame(extra)
    extra.to_csv(OUT/'data/qualifying_borrows_tail.csv',index=False)
    old=pd.read_csv(PE/'borrow_event_candidates.csv');q=pd.concat([old[old.threshold_pass],extra],ignore_index=True)
    chosen=pd.read_csv(OUT/'data/table8_column2_event_list.csv')
    lo=int(pd.Timestamp('2025-01-16',tz='UTC').timestamp())
    end=json.loads((ADD/'tail_coverage.json').read_text())['end']
    # Base timestamp clock has been independently validated for the complete ledger.
    anchor=pd.read_csv(ADD/'daily.csv').iloc[0]
    hi=int(anchor.timestamp)+2*(int(end)-int(anchor.block))
    rows=[]
    for r in chosen.itertuples():
        other=q[q.market.eq(r.market)&~(q.tx.eq(r.tx)&q.block.eq(r.block))]
        after=other[(other.timestamp>r.timestamp)|((other.timestamp==r.timestamp)&((other.block>r.block)|((other.block==r.block)&other.first_log_index.gt(r.first_log_index))))]
        nexttime=float(after.timestamp.min()) if len(after) else np.inf
        full_pre=r.timestamp-7*86400>=lo
        full_post=r.timestamp+7*86400<=hi
        none=not other.timestamp.between(r.timestamp-7*86400,r.timestamp+7*86400).any()
        rows.append(dict(event_id=r.event_id,old_next_timestamp=r.next_qualifying_timestamp,new_next_timestamp=nexttime,
                         pre168_covered=full_pre,post168_covered=full_post,isolated168_certified=bool(full_pre and full_post and none),
                         old_isolated168=r.isolated168))
    audit=pd.DataFrame(rows)
    audit.to_csv(OUT/'data/event_boundary_audit.csv',index=False)
    chosen[chosen.event_id.isin(audit.loc[audit.isolated168_certified,'event_id'])].to_csv(OUT/'data/table8_isolated_coverage_certified.csv',index=False)
    raw=pd.read_parquet(OUT/'data/table8_all_horizons.parquet').merge(audit,on='event_id',how='left',validate='many_to_one')
    results=[]
    H=['m1','pre','event','p1','p6','p24','p72','p168']
    counts=[]
    for panel,y in [('A','delta_market_duplication'),('B','joint_million')]:
        base=raw[raw.event_type.eq('borrow')].dropna(subset=[y]).copy()
        good=base.groupby('event_id').horizon.nunique();base=base[base.event_id.isin(good[good.eq(9)].index)]
        for sample in ['tail_completed_censored','coverage_certified_isolated']:
            d=base[base.timestamp.lt(base.new_next_timestamp)|base.horizon.isin(['m24','m1','pre','event'])].copy() if sample=='tail_completed_censored' else base[base.isolated168_certified.eq(True)].copy()
            for h in H:d['h_'+h]=d.horizon.eq(h).astype(float)
            f=event_fit(d,y,['h_'+h for h in H]);f['panel']=panel;f['sample']=sample;results.append(f)
            counts.append(dict(panel=panel,sample=sample,N=len(d),events=d.event_id.nunique(),p168_events=d[d.horizon.eq('p168')].event_id.nunique()))
    pd.concat(results).to_csv(OUT/'tables/table8_coverage_corrected_estimates.csv',index=False)
    pd.DataFrame(counts).to_csv(OUT/'tables/table8_coverage_corrected_samples.csv',index=False)
    correction={'qualifying_tail_borrows':len(extra),'old_isolated_events':int(audit.old_isolated168.sum()),
                'certified_isolated_events':int(audit.isolated168_certified.sum()),'old_isolated_lacking_pre168':int((audit.old_isolated168&~audit.pre168_covered).sum()),
                'changed_next_borrow_times':int(audit.old_next_timestamp.ne(audit.new_next_timestamp).sum()),
                'following_counts_old':{str(h):int((chosen.next_qualifying_timestamp-chosen.timestamp<=h*3600).sum()) for h in [24,72,168]},
                'following_counts_full_tail':{str(h):int((audit.new_next_timestamp.to_numpy()-chosen.timestamp.to_numpy()<=h*3600).sum()) for h in [24,72,168]},
                'coverage_end_timestamp':hi}
    (OUT/'logs/event_boundary_corrections.json').write_text(json.dumps(correction,indent=2))
    print('Boundary audit',correction,flush=True)


if __name__=='__main__':run()
