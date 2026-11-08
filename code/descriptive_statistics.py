from pathlib import Path
import numpy as np,pandas as pd,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/revision37';O.mkdir(exist_ok=True)
d=pd.read_csv(R/'reports/revision28/daily_analysis.csv',parse_dates=['date']).set_index('date');v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v.date=pd.to_datetime(v.date)
g=v[~v.spark&v.date.ge('2025-01-16')&v.prior_claim_usdc.ge(1)].copy();n0=len(g)
while True:
 keep=g.groupby('owner').owner.transform('size').gt(1)&g.groupby('date').date.transform('size').gt(1)
 if keep.all():break
 g=g[keep].copy()
g=g.merge(d[['utilization','premium','eth_return_pp','eth_volatility_pp']],left_on='date',right_index=True,validate='many_to_one');g['log_claim']=np.log(g.prior_claim_usdc);g['centered_size']=g.log_claim-np.log(1000);g['deposit_pp']=100*g.deposit_any;g['withdraw_pp']=100*g.withdraw_any
g['log_low']=np.minimum(g.log_claim,np.log(100));g['log_high']=np.maximum(g.log_claim-np.log(100),0)
for k in ['utilization','premium','eth_return_pp','eth_volatility_pp']:
 g[k+'_size']=g[k]*g.centered_size
 for seg in ['low','high']:g[k+'_'+seg]=g[k]*g['log_'+seg]
assert (len(g),g.owner.nunique(),g.date.nunique(),n0-len(g))==(512978,12370,316,971)
rows=[]
def stats(sample,key,label,f):
 x=f[key].astype(float);assert x.notna().all() and np.isfinite(x).all();q=x.quantile([.25,.5,.75]);rows.append(dict(sample=sample,variable=key,label=label,N=len(x),mean=x.mean(),sd=x.std(ddof=1),min=x.min(),p25=q.loc[.25],median=q.loc[.5],p75=q.loc[.75],max=x.max()))
D=d.loc['2025-01-16':].copy();assert len(D)==319
labels=[('deposits','Gross deposits'),('withdrawals','Gross withdrawals'),('net','Net deposits'),('utilization','Utilization, lagged'),('premium','Premium, lagged'),('eth_return_pp','ETH return, lagged'),('eth_volatility_pp','ETH volatility, lagged'),('spark_lag','Net deposits, lagged'),('log_assets','Log assets, lagged')]
for k,label in labels:stats('Daily treasury model',k,label,D)
for h in [3,7]:
 z=D.copy();z['cumulative_net']=sum(d.net.shift(-i) for i in range(h)).loc[z.index];z=z[z.cumulative_net.notna()];assert len(z)==319-h+1
 for k,label in [('cumulative_net',f'{h}-day cumulative net')]+labels[3:]:stats(f'{h}-day treasury model',k,label,z)
ownerlabels=[('deposit_pp','Deposit (pp)'),('withdraw_pp','Withdrawal (pp)'),('log_claim',r'Log claim, $\ell$'),('premium_size',r'Premium $\times\widetilde\ell$'),('utilization_size',r'Utilization $\times\widetilde\ell$'),('eth_return_pp_size',r'ETH return $\times\widetilde\ell$'),('eth_volatility_pp_size',r'ETH volatility $\times\widetilde\ell$')]
for k,label in ownerlabels:stats('Owner linear model',k,label,g)
for k,label in [('log_low',r'$\ell_L$'),('log_high',r'$\ell_H$')]+[(k+'_'+seg,label+r' $\times\ell_'+('L' if seg=='low' else 'H')+'$') for k,label in [('premium','Premium'),('utilization','Utilization'),('eth_return_pp','ETH return'),('eth_volatility_pp','ETH volatility')] for seg in ['low','high']]:stats('Owner spline model',k,label,g)
s=pd.DataFrame(rows);s.to_csv(O/'regression_descriptive_statistics.csv',index=False)
# Validate identical original sample sizes and outcome scales against archived model records.
models=json.loads((R/'reports/revision28/models.json').read_text());checks=[]
for model,y,frame in [('deposits_HAC7','deposits',D),('withdrawals_HAC7','withdrawals',D),('net_HAC7','net',D),('sizeFE_deposit','deposit_pp',g),('sizeFE_withdraw','withdraw_pp',g)]:
 m=next(x for x in models if x['model']==model);assert m['n']==len(frame);gap=abs(m['mean']-frame[y].mean());assert gap<1e-10;checks.append({'model':model,'N':len(frame),'outcome_mean_gap':gap})
# Summaries are before fixed-effect absorption; this follows ordinary descriptive-table practice.
keys=g[['date','owner']].sort_values(['date','owner']).to_csv(index=False);(O/'owner_sample_keys.csv').write_text(keys)
validation={'passed':True,'checks':checks,'owner_singletons_removed':n0-len(g),'owner_sample_sha256':hashlib.sha256(keys.encode()).hexdigest(),'statistics_before_FE_absorption':True,'new_regressions':0};(O/'VALIDATION.json').write_text(json.dumps(validation,indent=2))

print(json.dumps(validation,indent=2))
