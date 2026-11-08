"""Audit owner-day accounting before admitting any expanded behavioral regressions."""
from pathlib import Path
from collections import defaultdict
import pandas as pd,numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';O.mkdir(exist_ok=True)
p=R/'reports/revision5/vault_economic_events.parquet';v=pd.read_parquet(p)
Z='0x'+'0'*40;PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
assert not v.duplicated(['tx','log_index']).any()
deltas=defaultdict(lambda:defaultdict(int));flows=defaultdict(lambda:defaultdict(lambda:[0,0,0,0]));first={};zero_transfers=[]
for r in v.to_dict('records'):
 day=str(r['date'])[:10];typ=r['type'];sh=int(r['shares_raw']);asset=int(r['assets_raw'])
 if typ in ['Deposit','Withdraw']:
  a=r['onBehalf'];assert isinstance(a,str) and a!=Z
  a=a.lower();deltas[day][a]+=sh*(1 if typ=='Deposit' else -1)
  j=0 if typ=='Deposit' else 1;flows[day][a][j]+=asset;flows[day][a][j+2]+=1;first.setdefault(a,day)
 else:
  assert typ=='Transfer';a=r['from'].lower();b=r['to'].lower()
  if Z in [a,b]:zero_transfers.append(r);continue # identify and do not double count mint/burn event pairs
  deltas[day][a]-=sh;deltas[day][b]+=sh
  first.setdefault(a,day);first.setdefault(b,day)
bal=defaultdict(int);records=[];neg=[];total=[];checkpoints=[];dailystates=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv').set_index('date')
for date in pd.date_range('2025-01-15','2025-11-30'):
 day=str(date.date());before=bal.copy()
 for a,delta in deltas[day].items():bal[a]+=delta
 if day in ['2025-03-31','2025-06-30','2025-11-30']:
  checkpoints.extend({'date':day,'owner':a,'shares_raw':str(n)} for a,n in bal.items() if n>0)
 total.append({'event_spark_shares_raw':str(bal.get(PROXY,0)),'direct_spark_shares_raw':str(dailystates.loc[day,'treasury_shares']),'date':day,'event_total_shares_raw':str(sum(bal.values())),'direct_total_shares_raw':str(dailystates.loc[day,'total_shares']),'difference_raw':str(int(dailystates.loc[day,'total_shares'])-sum(bal.values()))})
 for a in sorted(set(before)|set(bal)):
  if bal[a]<0:neg.append({'date':day,'owner':a,'shares_raw':str(bal[a])})
  dep,wd,nd,nw=flows[day][a]
  if before.get(a,0)!=0 or bal[a]!=0 or dep or wd:
   records.append({'date':day,'owner':a,'opening_shares_raw':str(before.get(a,0)),'closing_shares_raw':str(bal[a]),'opening_shares':before.get(a,0)/1e18,'closing_shares':bal[a]/1e18,'deposit_usdc':dep/1e6,'withdraw_usdc':wd/1e6,'deposit_events':nd,'withdraw_events':nw,'first_seen':first[a],'spark':a==PROXY})
f=pd.DataFrame(records);f.to_parquet(O/'owner_day_candidate.parquet',index=False)
pd.DataFrame(checkpoints).to_csv(O/'owner_checkpoints.csv',index=False)
pd.DataFrame(neg).to_csv(O/'negative_owner_days.csv',index=False);pd.DataFrame(total).to_csv(O/'aggregate_share_reconciliation.csv',index=False)
g=v[v.type.isin(['Deposit','Withdraw'])].copy();g['asset']=g.assets_raw.astype(float)/1e6
own=g.groupby(['onBehalf','type']).asset.sum().unstack(fill_value=0).reset_index();own['gross']=own.Deposit+own.Withdraw;own.sort_values('gross',ascending=False).to_csv(O/'owner_turnover.csv',index=False)
summary={'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'events':len(v),'unique_deposit_beneficiaries':v.loc[v.type.eq('Deposit'),'onBehalf'].nunique(),'owners_any_event':len(first),'candidate_owner_days':len(f),'negative_owner_days':len(neg),'negative_owners':len(set(r['owner'] for r in neg)),'zero_address_transfers_in_api':len(zero_transfers),'spark_gross_turnover_share':float(own.loc[own.onBehalf.eq(PROXY),'gross'].sum()/own.gross.sum()),'first_date':str(v.date.min()),'last_date':str(v.date.max()),'regression_admissible':False,'reason':'candidate event-based shares require direct-state and transfer-coverage validation; addresses are not independent verified institutions'}
(O/'owner_audit.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(own.sort_values('gross',ascending=False).head(8).to_string(index=False))
