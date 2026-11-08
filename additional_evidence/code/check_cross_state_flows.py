from pathlib import Path
import json,pandas as pd
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';O=P/'outputs'
coverage=json.loads((P/'cross_state_flow_coverage.json').read_text());assert len(coverage)==2204 and all(x['complete'] for x in coverage)
a=pd.read_parquet(P/'raw/cross_state_flows_single/all_events.parquet');a=a[a.within_state];b=pd.read_parquet(P/'raw/vault_committed_flows.parquet');p=pd.read_csv(O/'cross_state_flow_data.csv');available=sorted(set(p[p.chain.eq(8453)].date)&set(b.date));rows=[]
for day in available:
 vaults=set(p[p.chain.eq(8453)&p.date.eq(day)].vault)&set(b.vault)
 for vault in sorted(vaults):
  x=a[a.chain.eq(8453)&a.date.eq(day)&a.vault.eq(vault)];y=b[b.date.eq(day)&b.vault.eq(vault)];first={(r.tx,int(r.log_index)):int(r.signed_micro) for r in x.itertuples()};second={(r.tx,int(r.logindex)):int(r.signed_micro) for r in y.itertuples()};assert first==second,(day,vault,len(first),len(second),set(first)-set(second),set(second)-set(first));rows.append(dict(date=day,vault=vault,API_logs=len(first),archived_chain_logs=len(second),net_micro=sum(first.values()),match=True))
pd.DataFrame(rows).to_csv(O/'cross_state_flow_validation.csv',index=False)
assert len(rows)>0 and sum(x['API_logs'] for x in rows)>0
(P/'cross_flow_validation.json').write_text(json.dumps({'single_vault_queries':len(coverage),'complete':True,'events':len(a),'matched_existing_vault_days':len(rows),'matched_existing_logs':sum(x['API_logs'] for x in rows),'batch_query_status':'invalid coverage: multi-address query omitted known logged events; raw batch responses retained only as a source diagnostic','zero_flow_rule':'Zero only after complete single-vault pagination and exact snapshot-block cutoff'},indent=2));print('PASS',len(rows),'vault-days',sum(x['API_logs'] for x in rows),'events match exactly',flush=True)
