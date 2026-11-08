from pathlib import Path
import json,hashlib
import pandas as pd,numpy as np
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';O=P/'outputs'
def md(df):
 columns=list(df.columns);lines=['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']
 for row in df.itertuples(index=False,name=None):lines.append('| '+' | '.join('NA' if pd.isna(x) else format(float(x),'.15g') if isinstance(x,(float,np.floating)) else str(x) for x in row)+' |')
 return '\n'.join(lines)
parts=[];mods=[];tests=[]
for pre in ['task1','task2','task3','task3_cross','tasks4_5']:
 f=O/f'{pre}_numeric.csv'
 if f.exists():parts.append(pd.read_csv(f));mods.append(pd.read_csv(O/f'{pre}_models.csv'))
 f=O/f'{pre}_tests.csv'
 if f.exists() and f.stat().st_size>5:tests.append(pd.read_csv(f))
a=pd.concat(parts,ignore_index=True);m=pd.concat(mods,ignore_index=True);assert not a.duplicated(['model','spec','variable','covariance']).any();a.to_csv(O/'all_estimates.csv',index=False,float_format='%.17g');m.to_csv(O/'all_models.csv',index=False,float_format='%.17g');t=pd.concat(tests,ignore_index=True);t.to_csv(O/'all_tests.csv',index=False,float_format='%.17g')
quote=[]
for row in a.to_dict('records'):
 for key in ['coefficient','standard_error','t_statistic','p_value','wild_cluster_p']:
  if pd.notna(row.get(key)):quote.append(dict(source='all_estimates.csv',model=row['model'],spec=row['spec'],variable=row['variable'],covariance=row['covariance'],statistic=key,value=row[key]))
for row in m.to_dict('records'):
 for key in ['Obs','df_p','within_R2','R2','pseudo_R2','outcome_mean']:
  if pd.notna(row.get(key)):quote.append(dict(source='all_models.csv',model=row['model'],spec=row['spec'],variable='',covariance='',statistic=key,value=row[key]))
for filename in ['flow_checks.json','supply_identity_checks.json','task3_cross_status.json']:
 file=P/filename
 if file.exists():
  for key,value in json.loads(file.read_text()).items():
   if isinstance(value,(int,float)) and not isinstance(value,bool):quote.append(dict(source=filename,model='sample',spec='',variable='',covariance='',statistic=key,value=value))
for row in m.to_dict('records'):
 for item in str(row.get('clusters','')).split(';'):
  if ':' in item:
   key,val=item.rsplit(':',1)
   if val.isdigit():quote.append(dict(source='all_models.csv',model=row['model'],spec=row['spec'],variable='',covariance='',statistic='clusters_'+key,value=int(val)))
for filename in ['all_tests.csv','event_horizon_descriptives.csv','event_estimation_coverage.csv']:
 frame=pd.read_csv(O/filename)
 for idx,row in frame.iterrows():
  for key in frame.select_dtypes(include='number').columns:
   if pd.notna(row[key]):quote.append(dict(source=filename,model=str(row.get('model',row.get('event_type','event'))),spec=str(row.get('spec',row.get('horizon',row.get('kind','')))),variable=str(row.get('test',row.get('outcome',''))),covariance=str(row.get('covariance','')),statistic=key,value=row[key]))
pd.DataFrame(quote).to_csv(O/'quoteable_values.csv',index=False,float_format='%.17g')
flow=json.loads((P/'flow_checks.json').read_text());supply=json.loads((P/'supply_identity_checks.json').read_text());rob=json.loads((P/'robustness_status.json').read_text());prediction=json.loads((P/'task3_status.json').read_text())
text=['# Panel evidence for Counting the same cash','', 'All monetary regression variables are million USDC unless the variable is a fraction, utilization per 10 percentage points, or a logarithm. Raw event amounts and states retain integer micro-USDC. All fitted specifications and numerical inference results are reported below.','', '## Task 1. Cross-vault spillover','',f"The first-difference panel contains {flow['vault_days']} vault-days. Net OwnFlow is zero in {flow['own_zero_net']} observations; {flow['own_no_operations']} contain no own Supply or Withdraw operations. Column 1c follows the specified net-zero criterion. Opening-market reconciliation includes a separately recorded own-flow adjustment on {flow['own_flow_outside_opening_nonzero']} days.", '',md(a[(a.model=='task1')&a.variable.isin(['OtherVaultFlow','OutsideFlow','BorrowFlow','Peer_x_exposure'])][['spec','variable','coefficient','t_statistic','p_value','covariance']]),'',md(t[t.model.eq('task1')][['spec','test','difference','t_statistic','p_value','covariance']]),'', 'In 1a, peer inflows and outside inflows are positively associated with capacity changes and borrowing is negatively associated, matching the cash-budget direction; the net-zero-own-flow and exposure-change columns have small, statistically insignificant peer-flow estimates.','', '## Task 2. Large borrow events','']
if (O/'event_estimation_coverage.csv').exists():
 cov=pd.read_csv(O/'event_estimation_coverage.csv');text += [f"The operation ledger contains {flow['large_borrow_candidates']} above-threshold market-transactions; the preceding-24-hour rule retains {flow['retained_events']}.", '',md(cov),'']
 immediate=a[a.model.str.startswith('task2_')&a.spec.eq('horizons')&a.variable.eq('h_event')];text += [md(immediate[['model','coefficient','t_statistic','p_value']]),'']
 desc=pd.read_csv(O/'event_horizon_descriptives.csv');direct=desc[desc.horizon.eq('event')]
 text += ['Event-time coefficients above compare the event block with the −24-hour reference, with event-pair fixed effects. The following descriptive changes instead compare the event block with its immediately preceding block; available-pair counts can exceed the complete-nine-horizon estimation samples.', '',md(direct[['event_type','outcome','count','mean','median']]),'', 'Borrow-event mean immediate changes are −0.133880 million USDC in individual capacity and −0.155055 million USDC in market joint cash, while market duplication increases by 0.015662. These average level directions agree with cash-budget tightening. Relative to −24 hours, the capacity-level coefficient is positive and insignificant; market joint cash declines and market duplication rises significantly. All signs and horizons are retained.', '', 'Capacity-share changes are raw ratios using the opening capacity denominator. Small positive denominators generate extreme ratios, including the placebo path; these values are retained without trimming. Subsequent horizons include intervening operations.']

else:text+=['Event-state collection status is recorded under raw/. No event regression is reported until its archived states have been read and checked.']
text+=['','## Task 3. Next-state refused requests','',md(a[a.model.str.startswith('task3_')&a.variable.eq('D')][['model','spec','coefficient','t_statistic','p_value','wild_cluster_p']]),'', 'With the lagged refusal indicator, D is positive for the 25% request and negative for the 10% request, with both wild-bootstrap p-values above 0.10. Without that indicator, both D coefficients are negative; these dynamic estimates differ from a positive-shortage prediction.','', 'Cross-chain regressions use committed net inflow during the UTC day through the current snapshot block. Next-state outcomes include observed zero-capacity next states; current zero-S predictors remain excluded. The cross-chain lagged-outcome LPM uses 1,799 transitions and 338 vaults; its D coefficient is −0.088010, t = −1.705783, p = 0.088970. Exact transition counts and intervals are recorded in task3_cross_status.json.','', '## Task 4. Robustness','',md(m[m.model.str.startswith('task4')][['model','spec','Obs','FE','clusters','within_R2','R2']]),'', 'The asset-weighted outcome is sum(assets_v × D_v)/sum(assets_v); three dates with undefined D at positive assets are excluded from this outcome, leaving 436 days. Spark exclusion recomputes the nine-vault network and aggregate controls. HAC14 removes the calendar effects as specified. All-version network exposure requires V2 adapter positions and token-conversion states absent from the archive. The September-only cross-section contains one date cluster, so its entity/date two-way covariance is undefined.','', 'Shared-market exposure coefficients remain positive in every leave-chain-out column; all estimates and covariance choices are retained in the complete table below.','', '## Task 5. Market-day heterogeneity','',f"The median sample-vault count is {rob['market_count_median']:.0f}. Low-count observations have count ≤ the median; high-count observations have count > the median.",'',md(a[a.model.eq('task5')][['spec','variable','coefficient','t_statistic','p_value']]),'', 'The positive utilization-by-vault-count interaction and larger utilization coefficient in the high-count group agree with greater duplication when more vaults draw on heavily utilized markets.','', 'Logit wild p-values for the ten-vault panel use [restricted WCLR-C inference](https://arxiv.org/html/2406.00650v1), with 9,999 Rademacher draws and seed 20261003.','', '## Sample sizes and inference','',md(m),'','## Complete numerical estimates','',md(a),'','## Accounting validation and scope','',f"The {flow['operations']} committed market operations reconcile {flow['market_cash_checks']} observed market closing balances with maximum error {flow['max_cash_error_micro']} micro-USDC. Ten randomly drawn vault-days also match direct peer-flow recomputation. The unadjusted supply-stock/net-supply difference exceeds 1 USDC on {supply['raw_supply_stock_identity_over_1USDC']} market-days; interest and bad debt are separately recorded, with zero remaining balance error. Interest in this reconciliation is derived from the stock-flow balance. Liquidation repayments are recorded separately from voluntary Repay, and enter neither a fabricated OutsideFlow nor a renamed BorrowFlow.",'','Exact machine-readable values are in outputs/quoteable_values.csv, all_estimates.csv, all_models.csv and all_tests.csv. Every paper-facing table has its numeric companion and definitions note.']
(P/'Results_report.md').write_text('\n'.join(text)+'\n')
print('report estimates',len(a),'models',len(m),'quoteable values',len(quote),flush=True)
