from pathlib import Path
import pandas as pd,numpy as np,json
O=Path('reports/revision39_pilot')
e=pd.read_csv('reports/revision26/ethena_daily_exact_claims.csv',dtype={'rpc_claim_micro':str});b=pd.read_csv('reports/revision6/withdrawal_capacity.csv');e=e.merge(b[['date','block_timestamp']],left_on='state_date',right_on='date',suffixes=('','_b'),validate='one_to_one');e['claim_usdc']=e.rpc_claim_micro.map(int)/1e6;e['shortfall_usdc']=e.claim_usdc-e.rpc_capacity_usdc;e['gap']=e.shortfall_usdc>1;e=e.sort_values('block_timestamp').reset_index(drop=True);e['spell_start']=e.gap&~e.gap.shift(fill_value=False);e['spell']=e.spell_start.cumsum();e['observed_state_utc']=pd.to_datetime(e.block_timestamp,unit='s',utc=True)
t=pd.read_csv('reports/revision29/treasury_transaction_links.csv');t=t[t.strict_deposit].sort_values(['timestamp','block']);end=1764547200
rows=[]
for limit in [1,1000000]:
 tt=t[t.treasury_Deposit.ge(limit*1e6)];st=tt.timestamp.to_numpy();ix=np.searchsorted(st,e.block_timestamp.to_numpy(),side='right');wait=np.where(ix<len(st),(st[np.minimum(ix,len(st)-1)]-e.block_timestamp)/3600,np.nan)
 e[f'wait_{limit}_hours']=wait
 for label,mask in [('all_gap_states',e.gap),('gap_spell_starts',e.spell_start),('covered_states',~e.gap)]:
  x=e[mask];w=x[f'wait_{limit}_hours'];rec={'sample':label,'minimum_supply_usdc':limit,'n':len(x),'censored':int(w.isna().sum()),'min_hours':w.min(),'p25_hours':w.quantile(.25),'median_hours':w.median(),'p75_hours':w.quantile(.75),'max_hours':w.max()}
  for h in [1,6,24]:rec[f'within_{h}h']=int(w.le(h).sum());rec[f'eligible_{h}h']=int((x.block_timestamp+h*3600<=end).sum())
  rows.append(rec)
e.to_csv(O/'ethena_observation_waits.csv',index=False);pd.DataFrame(rows).to_csv(O/'ethena_wait_summary.csv',index=False)
sp=[]
for k,g in e[e.gap].groupby('spell'):
 r=g.iloc[0];last=g.iloc[-1];sp.append({'spell':int(k),'first_observed_gap':str(r.observed_state_utc),'last_observed_gap':str(last.observed_state_utc),'gap_days':len(g),'opening_shortfall_million':r.shortfall_usdc/1e6,'max_shortfall_million':g.shortfall_usdc.max()/1e6,'wait_any_hours':r.wait_1_hours,'wait_million_hours':r.wait_1000000_hours})
pd.DataFrame(sp).to_csv(O/'ethena_gap_spells.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False));print(pd.DataFrame(sp).to_string(index=False))
