"""Close raw-event owner and aggregate share balances without using residuals as mints."""
from pathlib import Path
import pandas as pd,json
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27'
a=pd.read_csv(O/'aggregate_share_reconciliation.csv',dtype=str);f=pd.read_csv(O/'verified_fee_mint_pairs.csv',dtype=str);fees={d:sum(map(int,g.fee_shares_raw)) for d,g in f.groupby('date')};cum=0;rows=[]
for r in a.to_dict('records'):
 cum+=fees.get(r['date'],0);sp=int(r['event_spark_shares_raw'])+cum;total=int(r['event_total_shares_raw'])+cum
 assert sp==int(r['direct_spark_shares_raw']),r['date']
 assert total==int(r['direct_total_shares_raw']),r['date']
 rows.append({**r,'cumulative_raw_fee_shares':str(cum),'reconstructed_spark_shares_raw':str(sp),'reconstructed_total_shares_raw':str(total),'spark_gap_raw':'0','aggregate_gap_raw':'0'})
pd.DataFrame(rows).to_csv(O/'verified_daily_share_reconciliation.csv',index=False)
s={'daily_states':len(rows),'spark_exact_matches':len(rows),'aggregate_exact_matches':len(rows),'raw_fee_event_count':len(f),'source':'Deposit/withdrawal/transfer ledger plus independently paired raw fee mints; direct state used only as comparison.'}
(O/'closed_share_validation.json').write_text(json.dumps(s,indent=2));print(s)
