from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd,statsmodels.api as sm
from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
A=Path(__file__).resolve().parents[1];R=A.parent;O=A/'outputs';r=pd.read_csv(O/'regressions.csv');m=pd.read_csv(O/'model_metadata.csv');checks=[]
assert np.allclose(r.coefficient/r.standard_error,r.t_statistic,rtol=1e-10);assert r.p_value.between(0,1).all() and r.wild_cluster_p.dropna().between(0,1).all();checks.append('All 31 coefficient rows: t=coefficient/SE; p-values within [0,1].')
p=pd.read_csv(O/'mechanism_observations.csv');g=pd.factorize(p.tx)[0];F=pd.get_dummies(p.tx,drop_first=True,dtype=float);X=sm.add_constant(pd.concat([p[['formula_million']],F],axis=1));fit=sm.OLS(p.delta_million,X).fit(cov_type='cluster',cov_kwds={'groups':g,'use_correction':True,'df_correction':True},use_t=True);b=r[(r.model=='mechanism')&(r.spec=='b_transaction_FE')].iloc[0];assert np.isclose(fit.params.formula_million,b.coefficient,rtol=1e-10) and np.isclose(fit.bse.formula_million,b.standard_error,rtol=1e-9);checks.append('Transaction FE slope and clustered SE agree with independent explicit-dummy OLS.')
for cutoff in [2,3]:
 z=pd.read_csv(O/f'market_estimation_at_least_{cutoff}.csv');terms=['vault_count','utilization10','log_cash','largest_position_supply'];F=pd.get_dummies(z[['market','date']],drop_first=True,dtype=float);X=sm.add_constant(pd.concat([z[terms],F],axis=1));fit=sm.OLS(z.duplication,X).fit();g1=pd.factorize(z.market)[0];g2=pd.factorize(z.date)[0];cov,_,_=cov_cluster_2groups(fit,g1,g2,use_correction=True);rr=r[(r.model=='market_duplication')&(r.spec==f'at_least_{cutoff}_vaults')].set_index('variable');assert np.allclose(fit.params[terms],rr.loc[terms].coefficient,rtol=1e-8,atol=1e-10);se=np.sqrt(np.diag(cov)[1:5]);assert np.allclose(se,rr.loc[terms].standard_error,rtol=1e-7,atol=1e-10);checks.append(f'Market >= {cutoff}: coefficients and two-way clustered SEs agree with independent explicit-dummy OLS and statsmodels covariance.')
d=pd.read_csv(O/'daily_estimation_data.csv');assert len(d)==439 and d.date.nunique()==439 and d.joint_exclusion25.sum()==62;assert np.allclose(d.gap25,1-4*d.J_assets) and np.allclose(d.gap10,1-10*d.J_assets)
j=r[r.model=='joint_budget'].pivot(index='variable',columns='spec',values='coefficient');assert np.allclose(j.gap25,-4*j.J_assets) and np.allclose(j.gap10,-10*j.J_assets);checks.append('Daily N=439; 62 joint-exclusion dates; gap25=1-4 J/assets and gap10=1-10 J/assets, including corresponding coefficient identities.')
c=pd.read_csv(O/'cross_protocol_summary.csv');assert len(c)==28 and (c.status=='complete').all();assert np.allclose(c.S_usdc-c.J_usdc,c.duplicate_usdc,atol=.00011);assert np.allclose(c.duplicate_usdc/c.S_usdc,c.duplication_rate,atol=1e-9);assert np.allclose(c.S_usdc/c.assets_usdc,c.S_assets) and np.allclose(c.J_usdc/c.assets_usdc,c.J_assets);assert (c.J_usdc<=c.S_usdc+.000001).all();checks.append('All 28 cross-protocol states reconcile S-J, duplication rate, S/assets and J/assets.')
contracts=pd.read_csv(O/'cross_protocol_contracts.csv');vs=pd.read_csv(O/'cross_protocol_vaults.csv')
for _,row in c.iterrows():
 v=vs[(vs.protocol==row.protocol)&(vs.chain_id==row.chain_id)&(vs.date==row.date)];assert len(v)==row.vaults and v.vault.nunique()==row.vaults;assert np.isclose(v.assets_micro.sum()/1e6,row.assets_usdc);h=contracts[(contracts.protocol==row.protocol)&(contracts.chain_id==row.chain_id)&(contracts.date==row.date)];assert h.block.nunique()==1 and h.block_hash.nunique()==1 and h.block_hash.iloc[0]==row.block_hash
checks.append('Every cross-protocol vault count and total asset sum matches its address-level table and unique block/hash.')
for f in (A/'raw').glob('block_*.json'):
 h=json.loads(f.read_text());assert h['timestamp']<h['boundary']<=h['next_timestamp'] and h['next_block']==h['block']+1 and h['block']<=h['finalized_head']
checks.append('All month-end and September 29 blocks precede UTC boundaries, with immediate next-block and finalized-head checks.')
expected={'Counting_the_same_cash.docx':'11bd3d97c4e15184429f00b7df91374bc388059cbd63b1922c7191e7f77866d3','Counting_the_same_cash.pdf':'07058da857e0bc72c0278fd3db0070fdc240f9e72bf4d016b9c8efbb3ed7cb46'}
found=[]
for name,digest in expected.items():
 f=R.parents[1]/name
 if f.exists():assert hashlib.sha256(f.read_bytes()).hexdigest()==digest;found.append(name)
checks.append('Manuscript SHA-256 unchanged: '+(', '.join(found) if found else 'manuscripts not included in this results-only archive; source workspace check recorded separately'))
(A/'checks.md').write_text('# Checks\n\n'+'\n'.join('- PASS: '+x for x in checks)+'\n');print('\n'.join(checks))
