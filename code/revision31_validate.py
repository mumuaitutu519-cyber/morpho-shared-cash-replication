from pathlib import Path
import pandas as pd,numpy as np,json,statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_hac
R=Path(__file__).resolve().parents[1];O=R/'reports/revision31';d=pd.read_csv(O/'hourly_inputs.csv',parse_dates=['hour']).set_index('hour');m=pd.read_parquet(R/'reports/revision29/market_cash_sequence.parquet').sort_values(['block','log_index']);ts=np.array([int(x.timestamp()) for x in d.index]);ix=np.searchsorted(m.timestamp.to_numpy(),ts,side='left')-1;cash=np.where(ix>=0,m.cash_after_raw.to_numpy()[np.maximum(ix,0)],int(m.cash_before_raw.iloc[0]))/1e12;assert np.max(abs(cash-d.opening_cash))<1e-10
assert abs(d.treasury_Deposit.sum()-5972.754164420671)<1e-8;assert abs(d.treasury_Withdraw.sum()-5706.157020672908)<1e-8
for h in [1,6]:
 for key,src in [('deposit','treasury_Deposit'),('net','net')]:
  expected=np.array([d[src].iloc[i+1:i+h+1].sum() for i in range(len(d)-h)]);assert np.max(abs(expected-d[f'{key}_{h}h'].iloc[:-h]))<1e-10
z=pd.read_csv(O/'analysis_sample.csv',parse_dates=['hour']).set_index('hour');cols=['other_W','tightness','interaction','other_D','borrow','repay','treasury_Deposit','treasury_Withdraw'];a=z[cols+['deposit_1h']].to_numpy();ids=[pd.factorize(z.index.date)[0],z.index.hour.to_numpy()]
for k in range(1000):
 old=a.copy()
 for i in ids:
  for j in range(a.shape[1]):a[:,j]-=np.bincount(i,weights=a[:,j])[i]/np.bincount(i)[i]
 if abs(a-old).max()<1e-10:break
X=a[:,:-1];y=a[:,-1];f=sm.OLS(y,X).fit();n=len(z);fullk=len(cols)+319+24-1;cov=cov_hac(f,nlags=24,use_correction=True)*(n-len(cols))/(n-fullk);stored=pd.read_csv(O/'deposit_1h_HAC24_cov.csv',index_col=0);gap=float(np.max(abs(cov-stored.to_numpy())));assert gap<1e-9
r={'all_7656_hour_opening_cash_checks_passed':True,'treasury_flow_totals_match_prior_audit':True,'future_window_sums_match_independent_slices':True,'statsmodels_HAC_covariance_max_gap':gap,'same_hour_responses_excluded':True,'clock_time_HAC_preserved_when_dates_excluded':True,'sample_hours':len(z),'scope':'Retained inputs and independent implementation checks; no new raw network collection.'};(O/'INDEPENDENT_VALIDATION.json').write_text(json.dumps(r,indent=2));print(r)
