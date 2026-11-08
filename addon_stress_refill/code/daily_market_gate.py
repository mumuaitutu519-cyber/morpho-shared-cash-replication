"""Complete the 33-market cash grid, including markets outside current queues."""
import json
import numpy as np,pandas as pd
from hourly import batches,M,sel
from preflight import O,R
def run():
    vaults=pd.read_parquet(O/'vault_states.parquet');days=vaults[['date','block']].drop_duplicates().sort_values('date');mids=json.loads((R/'additional_evidence/panel_evidence/raw/operation_query.json').read_text())['markets'];d=pd.read_parquet(R/'additional_evidence/panel_evidence/raw/market_operations.parquet').sort_values(['block','log_index']);c0=json.loads((R/'additional_evidence/panel_evidence/raw/opening_market_cash.json').read_text());flows={}
    for m,g in d.groupby('market'):
        delta=g.assets_micro.where(g.kind.isin(['Supply','Repay','Liquidation']),-g.assets_micro);flows[m]=(g.block.to_numpy(),delta.cumsum().to_numpy()+int(c0[m]))
    rows=[]
    for start in range(0,len(days),12):
        group=days.iloc[start:start+12];values=batches(8453,[(int(r.block),[(M,sel('market(bytes32)')+m[2:]) for m in mids]) for r in group.itertuples()])
        for r,answer in zip(group.itertuples(),values):
            for mid,x in zip(mids,answer):
                assert x is not None;actual=x[0]-x[2];bs,cs=flows[mid];idx=np.searchsorted(bs,r.block,side='right')-1;expected=int(cs[idx]) if idx>=0 else int(c0[mid]);rows.append(dict(date=r.date,block=r.block,market=mid,cash=actual,ledger_cash=expected,gap=expected-actual))
        print('daily 33-market checks',min(start+12,len(days)),len(days),flush=True)
    q=pd.DataFrame(rows);q.to_parquet(O/'full_daily_market_cash.parquet',index=False);q.to_csv(O/'full_daily_market_cash_reconciliation.csv',index=False);assert len(q)==440*33 and q.gap.abs().max()<=1
    gate=json.loads((O/'gate_results.json').read_text());gate.update(full_daily_market_checks=len(q),full_daily_market_max_gap_micro=int(q.gap.abs().max()));(O/'gate_results.json').write_text(json.dumps(gate,indent=2))
if __name__=='__main__':run()
