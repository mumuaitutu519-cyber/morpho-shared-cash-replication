"""Standalone Table8 column2 and +/-168h isolated-event reconstruction."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from statistics_common import event_fit

B=Path(__file__).resolve().parents[1]
D=B/'data'
O=B/'output'
O.mkdir(exist_ok=True)


def run():
    for row in json.loads((B/'input_manifest.json').read_text()):
        assert hashlib.sha256((B/row['path']).read_bytes()).hexdigest()==row['sha256']
    e=pd.read_csv(D/'borrow_event_list.csv')
    q=pd.read_csv(D/'borrow_event_candidates.csv');q=q[q.threshold_pass]
    metadata=[]
    for r in e.itertuples():
        g=q[q.market.eq(r.market)]
        if r.event_type=='borrow':g=g[~(g.tx.eq(r.tx)&g.block.eq(r.block))]
        after=g[(g.timestamp>r.timestamp)|((g.timestamp==r.timestamp)&((g.block>r.block)|((g.block==r.block)&g.first_log_index.gt(r.first_log_index))))]
        before=g[(g.timestamp<r.timestamp)|((g.timestamp==r.timestamp)&g.block.le(r.block))]
        nxt=float(after.timestamp.min()) if len(after) else np.inf
        prv=float(before.timestamp.max()) if len(before) else -np.inf
        metadata.append(dict(event_id=r.event_id,event_timestamp=r.timestamp,
            calendar_date=pd.Timestamp(r.timestamp,unit='s',tz='UTC').strftime('%Y-%m-%d'),
            next_qualifying_timestamp=nxt,isolated168=(prv<r.timestamp-168*3600 and nxt>r.timestamp+168*3600)))
    data=pd.read_parquet(D/'event_market_horizons.parquet').merge(pd.DataFrame(metadata),on='event_id',validate='many_to_one')
    rows=[];selection=[]
    horizons=['m1','pre','event','p1','p6','p24','p72','p168']
    for panel,y in [('A','delta_market_duplication'),('B','joint_million')]:
        base=data[data.event_type.eq('borrow')].dropna(subset=[y]).copy()
        counts=base.groupby('event_id').horizon.nunique();base=base[base.event_id.isin(counts[counts.eq(9)].index)]
        for sample in ['column2','isolated168']:
            d=base[base.timestamp.lt(base.next_qualifying_timestamp)|base.horizon.isin(['m24','m1','pre','event'])].copy() if sample=='column2' else base[base.isolated168].copy()
            for h in horizons:d['h_'+h]=d.horizon.eq(h).astype(float)
            r=event_fit(d,y,['h_'+h for h in horizons]);r['panel']=panel;r['sample']=sample;rows.append(r)
            selection.append(d[['event_id','horizon','market','timestamp',y]].assign(panel=panel,sample=sample))
            if sample=='isolated168' and panel=='B':
                ids=set(d.event_id)
                assert len(ids)==80
                e[e.event_id.isin(ids)].to_csv(O/'isolated80_event_list.csv',index=False)
    result=pd.concat(rows,ignore_index=True)
    result.to_csv(O/'estimates_unrounded.csv',index=False)
    pd.concat(selection).to_parquet(O/'sample_selection.parquet',index=False)
    expected=pd.read_csv(D/'expected_unrounded.csv')
    joined=result.merge(expected,on=['panel','sample','term','covariance'],suffixes=('_new','_old'),validate='one_to_one')
    checks=[]
    for variable in ['coefficient','se','t','p','wild_p_market','N','events','within_R2']:
        a,b=joined[variable+'_new'].to_numpy(),joined[variable+'_old'].to_numpy()
        ok=np.isclose(a,b,rtol=1e-8,atol=1e-10,equal_nan=True)
        checks.append(dict(variable=variable,matches=int(ok.sum()),rows=len(ok),all_match=bool(ok.all())))
    pd.DataFrame(checks).to_csv(O/'checks.csv',index=False)
    assert all(r['all_match'] for r in checks)
    print('PASS: original column2 and80-event sample reproduced; results use original and market/two-way inference.',flush=True)
    print('Coverage correction is supplied separately: two original isolated events lack pre-168h observations; see boundary_audit.csv.',flush=True)


if __name__=='__main__':run()
