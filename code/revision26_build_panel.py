"""Align API snapshot times to closing dates and construct validated candidate risk sets."""
from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26'
def history(name):return next(iter(json.loads((O/'raw'/f'{name}.json').read_text())['response']['data'].values()))['historicalState']
def series(a):
 return pd.Series({pd.Timestamp(int(z['x']),unit='s',tz='UTC').tz_localize(None)-pd.Timedelta(days=1):float(z['y']) if z['y'] is not None else np.nan for z in a}).sort_index()
h=history('vault_rates');dates=pd.date_range('2025-01-15','2025-11-30');d=pd.DataFrame(index=dates)
for name in ['vault','moonwell','gauntlet']:
 a=history(name+'_rates')
 for k in ['apy','netApy','totalAssets','totalSupply']:d[name+'_'+k]=series(a[k]).reindex(dates)
for k,a in history('market_rates').items():d['market_'+k]=series(a).reindex(dates)
allocation=history('spark_allocation');cash=pd.Series(0.,index=dates);positions=pd.Series(0.,index=dates);unreported=pd.Series(0,index=dates);names=[]
for a in allocation['allocation']:
 p=series(a['supplyAssets']).reindex(dates);m=a['market'];ms=series(m['historicalState']['supplyAssets']).reindex(dates);mb=series(m['historicalState']['borrowAssets']).reindex(dates)
 names.append(m['marketId']);unreported+=p.isna().astype(int);pp=p.fillna(0)
 assert not ((pp>0)&(ms.isna()|mb.isna())).any()
 positions+=pp;cash+=pd.Series(np.minimum(pp,(ms-mb).clip(lower=0).fillna(0)),index=dates)
d['cash_benchmark_usdc']=cash/1e6;d['positions_usdc']=positions/1e6;d['asset_residual_usdc']=d.vault_totalAssets/1e6-d.positions_usdc;d['unreported_position_series']=unreported
s=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date');s.index=pd.to_datetime(s.index)
d['direct_assets_raw']=s.total_assets_micro.map(int).astype(float);d['direct_shares_raw']=s.total_shares.map(int).astype(float);d['spark_claim_usdc']=s.claim_micro.map(int).astype(float)/1e6;d['spark_capacity_usdc']=s.max_withdraw_micro.map(int).astype(float)/1e6
d['supply_api_vs_direct_usdc']=(d.vault_totalAssets-d.direct_assets_raw)/1e6
d['peer_mean_net_apy']=(d.moonwell_netApy+d.gauntlet_netApy)/2;d['yield_premium_pp']=(d.vault_netApy-d.peer_mean_net_apy)*100
# Compound annualization: API net APY is not labeled a COMP-like reward rate.
d['gross_yield_pp']=100*d.vault_apy;d['net_yield_pp']=100*d.vault_netApy
native=pd.read_csv(O/'native_yields.csv',parse_dates=['date']).set_index('date');d=d.join(native,validate='one_to_one');d['net_native_yield_pp']=100*d.spark_net_native_APR
# Generic vault APY remains archived above, excluded from the analysis panel.
d['closing_date']=d.index;d.to_csv(O/'daily_conditions.csv',index_label='date')
v=pd.read_parquet(O/'owner_day_candidate.parquet');v['date']=pd.to_datetime(v.date);v['first_seen']=pd.to_datetime(v.first_seen)
# Use directly observed Spark shares. Keep all non-Spark balances from the audited ledger.
spark_open=s.treasury_shares.map(int).astype(float).shift()/1e18;spark_close=s.treasury_shares.map(int).astype(float)/1e18
v.loc[v.spark,'closing_shares']=v.loc[v.spark,'date'].map(spark_close)
v.loc[v.spark,'opening_shares']=v.loc[v.spark,'date'].map(spark_open)
prev=d[['direct_assets_raw','direct_shares_raw','cash_benchmark_usdc','net_native_yield_pp','native_yield_premium_pp','market_utilization','market_borrowApy']].shift().add_prefix('prior_');v=v.merge(prev,left_on='date',right_index=True,how='left',validate='many_to_one')
v['prior_claim_usdc']=v.opening_shares*1e18*v.prior_direct_assets_raw/v.prior_direct_shares_raw/1e6
v['prior_cash_coverage']=np.minimum(1,v.prior_cash_benchmark_usdc/v.prior_claim_usdc)
v['deposit_any']=v.deposit_usdc.gt(0).astype(int);v['withdraw_any']=v.withdraw_usdc.gt(0).astype(int);v['net_deposit_usdc']=v.deposit_usdc-v.withdraw_usdc
v['age_days']=(v.date-v.first_seen).dt.days
v['risk_set_incumbent']=v.prior_claim_usdc.ge(1)&v.date.ge('2025-01-16')
v.to_parquet(O/'owner_day_panel.parquet',index=False)
# Spot-check cash benchmark against newly collected owner-specific views.
q=pd.read_csv(O/'owner_rpc_validation.csv',dtype=str);comp=[]
for r in q.to_dict('records'):
 day=pd.Timestamp(r['date']);claim=int(r['rpc_shares_raw'])*d.loc[day,'direct_assets_raw']/d.loc[day,'direct_shares_raw']/1e6;pred=min(claim,d.loc[day,'cash_benchmark_usdc']);actual=int(r['rpc_max_withdraw_micro'])/1e6;comp.append({'date':r['date'],'owner':r['owner'],'cash_benchmark_prediction_usdc':pred,'rpc_capacity_usdc':actual,'gap_usdc':pred-actual})
c=pd.DataFrame(comp);c.to_csv(O/'owner_capacity_benchmark_validation.csv',index=False)
risk=v[v.risk_set_incumbent & ~v.spark];brief={'panel_rows':len(v),'incumbent_non_spark_rows':len(risk),'incumbent_non_spark_accounts':risk.owner.nunique(),'non_spark_below_quarter_coverage_rows':int(risk.prior_cash_coverage.lt(.25).sum()),'non_spark_below_full_coverage_rows':int(risk.prior_cash_coverage.lt(1).sum()),'non_spark_any_withdraw_days':int(risk.withdraw_any.sum()),'non_spark_any_deposit_days':int(risk.deposit_any.sum()),'condition_days':len(d),'max_asset_residual_usdc':float(d.asset_residual_usdc.abs().max()),'max_api_direct_asset_gap_usdc':float(d.supply_api_vs_direct_usdc.abs().max()),'max_owner_capacity_benchmark_gap_usdc':float(c.gap_usdc.abs().max()),'regressions_estimated':False,'notes':'The 1-USDC opening-claim threshold defines incumbent risk set; entry and amounts remain separate objects. Missing allocations are counted, not asserted actual zeros without asset reconciliation.'};(O/'panel_validation.json').write_text(json.dumps(brief,indent=2));print(json.dumps(brief,indent=2));print(d[['net_yield_pp','yield_premium_pp','asset_residual_usdc']].describe().to_string())
