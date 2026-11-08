from pathlib import Path
import pandas as pd,numpy as np,json,statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
O=Path('reports/revision39_pilot');d=pd.read_csv('reports/revision28/daily_analysis.csv',parse_dates=['date']).set_index('date').sort_index()
a=json.loads(Path('reports/revision26/raw/spark_allocation.json').read_text())['response']['data']['vaultByAddress']['historicalState']['allocation'];common='0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836';p=next(x for x in a if x['market']['marketId'].lower()==common);pos=pd.Series({pd.Timestamp(x['x'],unit='s').normalize()-pd.Timedelta(days=1):int(x['y'])/1e6 for x in p['supplyAssets'] if x['y'] is not None});d['vault_market_position']=pos
# Current states are aligned to closing dates; all explanatory states shifted one day.
d['total_supply']=d.market_supplyAssets/1e6;d['total_borrow']=d.market_borrowAssets/1e6;d['external_supply']=d.total_supply-d.vault_market_position
assert d.external_supply.gt(0).all()
d['outside_pressure']=100*(d.total_borrow/d.external_supply).shift()
# Treasury share of vault allocation is a proportional exposure scenario, not earmarked provenance.
d['treasury_weight']=d.spark_claim_usdc/(d.direct_assets_raw/1e6);d['external_treasury_supply']=d.total_supply-d.vault_market_position*d.treasury_weight
d['treasury_removed_pressure']=100*(d.total_borrow/d.external_treasury_supply).shift()
d['lag_D']=d.deposits.shift();d['lag_W']=d.withdrawals.shift();d['lag_log_supply']=np.log(d.total_supply).shift();d['lag_log_borrow']=np.log(d.total_borrow).shift();d['lag_external_supply_million']=d.external_supply.shift()/1e6;d['lag_borrow_million']=d.total_borrow.shift()/1e6;d['lag_vault_fraction']=(d.vault_market_position/d.total_supply).shift()
commoncols=['premium','eth_return_pp','eth_volatility_pp','log_assets'];specs={
'original':['utilization','spark_lag']+commoncols,
'outside_pressure':['outside_pressure','spark_lag']+commoncols,
'outside_pressure_gross_lags':['outside_pressure','lag_D','lag_W']+commoncols,
'treasury_removed_pressure':['treasury_removed_pressure','spark_lag']+commoncols,
'original_gross_lags':['utilization','lag_D','lag_W']+commoncols,
'original_control_supply':['utilization','lag_log_supply','lag_D','lag_W']+commoncols,
'borrow_supply_separate':['lag_log_borrow','lag_log_supply','lag_D','lag_W']+commoncols,
'outside_components':['lag_borrow_million','lag_external_supply_million','lag_D','lag_W']+commoncols}
g=d.loc['2025-01-16':'2025-11-30'].copy();assert len(g)==319;results=[];models=[]
# Fill Jan-15 opening flow from full event ledger only to form Jan-16 lag, not arbitrary zero.
v=pd.read_parquet('reports/revision5/vault_economic_events.parquet');v=v[v.onBehalf.eq('0x2917956eff0b5eaf030abdb4ef4296df775009ca')&v.date.eq('2025-01-15')];opening=v.groupby('type').assets_raw.sum()/1e12
g.loc[pd.Timestamp('2025-01-16'),'lag_D']=opening.get('Deposit',0);g.loc[pd.Timestamp('2025-01-16'),'lag_W']=opening.get('Withdraw',0)
# Original lag convention may include Jan-15 ledger amount; verify rather than replace.
print('LAGIDENTITY',float((g.lag_D-g.lag_W-g.spark_lag).abs().max()),flush=True)
cal=pd.get_dummies(pd.DataFrame({'month':g.index.month.astype(str),'weekday':g.index.dayofweek.astype(str)},index=g.index),drop_first=True,dtype=float)
for name,cols in specs.items():
 assert g[cols].notna().all().all(),g[cols].isna().sum()
 X=sm.add_constant(pd.concat([g[cols],cal],axis=1));assert np.linalg.matrix_rank(X)==len(X.columns)
 co=[]
 for y in ['deposits','withdrawals','net']:
  f=sm.OLS(g[y],X).fit();co.append(f.params)
  for bw in [7,14]:
   r=f.get_robustcov_results(cov_type='HAC',maxlags=bw,use_correction=True,use_t=True)
   for j,k in enumerate(X.columns):results.append({'spec':name,'outcome':y,'bandwidth':bw,'term':k,'coef':r.params[j],'se':r.bse[j],'p':r.pvalues[j],'n':len(g),'r2':f.rsquared})
 assert abs(co[0]-co[1]-co[2]).max()<1e-8
rr=pd.DataFrame(results);mask=rr.bandwidth.eq(7)&rr.spec.ne('original')&rr.term.isin(['outside_pressure','treasury_removed_pressure','utilization','lag_log_borrow','lag_log_supply','lag_borrow_million','lag_external_supply_million']);rr.loc[mask,'holm_new_family']=multipletests(rr.loc[mask,'p'],method='holm')[1]
rr.to_csv(O/'feedback_all_regressions.csv',index=False);g.to_csv(O/'feedback_panel.csv');focal=rr[(rr.bandwidth==7)&rr.term.isin(['utilization','outside_pressure','treasury_removed_pressure','lag_log_supply','lag_log_borrow','lag_external_supply_million','lag_borrow_million'])];focal.to_csv(O/'feedback_focal.csv',index=False)
print(focal.to_string(index=False));summ={'days':len(g),'pressure_min_pct':g.outside_pressure.min(),'pressure_max_pct':g.outside_pressure.max(),'pressure_median_pct':g.outside_pressure.median(),'pressure_above100_days':int(g.outside_pressure.gt(100).sum()),'outside_pressure_IQR':g.outside_pressure.quantile(.75)-g.outside_pressure.quantile(.25),'original_utilization_IQR':g.utilization.quantile(.75)-g.utilization.quantile(.25),'new_focal_tests':int(mask.sum()),'disclaimer':'Removing a denominator component is not an instrument; borrower allocation to removed supplier is not observed.'};(O/'feedback_summary.json').write_text(json.dumps(summ,indent=2));print(summ)
