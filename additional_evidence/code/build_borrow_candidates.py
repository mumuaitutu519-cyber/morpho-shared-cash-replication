from pathlib import Path
import pandas as pd,json
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';O=P/'outputs'
d=pd.read_parquet(P/'raw/market_operations_cash.parquet',columns=['market','tx','block','timestamp','assets_micro','preblock_cash_micro','kind','log_index']);b=d[d.kind.eq('Borrow')].groupby(['market','tx','block'],as_index=False).agg(timestamp=('timestamp','first'),borrow_micro=('assets_micro','sum'),preblock_cash_micro=('preblock_cash_micro','first'),first_log_index=('log_index','min'));b['threshold_pass']=b.borrow_micro*10>b.preblock_cash_micro;e=b[b.threshold_pass].sort_values(['market','timestamp','block','first_log_index']).copy();e['prior_large_timestamp']=e.groupby('market').timestamp.shift();e['keep_24h']=e.prior_large_timestamp.isna()|(e.timestamp-e.prior_large_timestamp>=86400)
f=O/'borrow_event_candidates.csv'
if f.exists():
 old=pd.read_csv(f);before=set(zip(old.loc[old.keep_24h,'market'],old.loc[old.keep_24h,'tx']));after=set(zip(e.loc[e.keep_24h,'market'],e.loc[e.keep_24h,'tx']));print('same-block ordering membership changes',len(after-before),len(before-after),flush=True)
e.to_csv(f,index=False);print('candidates',len(e),'retained',int(e.keep_24h.sum()),flush=True)
r=json.loads((P/'flow_checks.json').read_text());r.update(large_borrow_candidates=len(e),retained_events=int(e.keep_24h.sum()));(P/'flow_checks.json').write_text(json.dumps(r,indent=2))
