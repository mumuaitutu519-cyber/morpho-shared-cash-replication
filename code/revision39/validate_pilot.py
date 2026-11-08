from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,collections
O=Path('reports/revision39_pilot');r=pd.read_parquet(O/'shared_positions.parquet');assert not r.duplicated(['timestamp','vault','market']).any();c=pd.read_csv(O/'shared_reconciliation.csv');base=c[c.timestamp.le(1764547200)];assert len(base)==3190 and base.asset_residual_usdc.abs().max()<=1e-6+1e-12
# Independent pure-Python regrouping for all original-window ten-vault dates.
gaps=[];d=pd.read_csv(O/'shared_daily.csv');g=d[d['sample'].eq('baseline10')&d.date.le('2025-11-30')]
for row in g.itertuples():
 z=r[r.timestamp.eq(row.timestamp)];mp=collections.defaultdict(list)
 for x in z.itertuples():mp[x.market].append((int(x.position_raw),int(x.cash_raw)))
 S=sum(min(p,m) for vals in mp.values() for p,m in vals);J=sum(min(sum(p for p,m in vals),vals[0][1]) for vals in mp.values());gaps.append(max(abs(S/1e6-row.S_usdc),abs(J/1e6-row.J_usdc),abs((S-J)/1e6-row.D_usdc)))
assert max(gaps)<1e-6
rpc=pd.read_csv(O/'direct_vault_asset_checks.csv');assert rpc.rpc_usdc.notna().sum()==30 and rpc.gap_usdc.abs().max()<1
e=pd.read_csv(O/'ethena_observation_waits.csv');assert len(e)==100 and e.gap.sum()==39 and e.spell_start.sum()==1
rr=pd.read_csv(O/'feedback_all_regressions.csv');old=pd.read_csv('reports/revision28/all_regressions.csv');x=rr[(rr.spec=='original')&(rr.bandwidth==7)];gaps2=[]
for v in x.itertuples():
 z=old[(old.model==v.outcome+'_HAC7')&(old.term==v.term)];assert len(z)==1;gaps2.append(abs(v.coef-z.coefficient.iloc[0]))
assert max(gaps2)<1e-8
# Same market references in the public API snapshot must agree.
l=json.loads((O/'raw/public_live_liquidity.json').read_text());seen={};S=0;pub=0
for v in l['response']['data'].values():
 pub+=int(v['liquidity']['underlying'])
 for a in v['state']['allocation']:
  m=a['market'];key=m['marketId'];s=m['state'];P=int(a['supplyAssets']);cash=int(s['supplyAssets'])-int(s['borrowAssets'])
  if key in seen:assert seen[key]['cash']==cash
  z=seen.setdefault(key,{'cash':cash,'pos':0,'S':0});z['pos']+=P;z['S']+=min(P,cash)
S=sum(z['S'] for z in seen.values());J=sum(min(z['pos'],z['cash']) for z in seen.values());live={'retrieved_utc':l['retrieved_utc'],'public_sum_usdc':pub/1e6,'benchmark_sum_usdc':S/1e6,'joint_benchmark_usdc':J/1e6,'public_minus_joint_usdc':(pub-J)/1e6,'public_excess_pct':100*(pub-J)/pub,'public_vs_reconstruction_gap_usdc':(pub-S)/1e6,'scope':'Current API snapshot; historical panel reconstructs benchmark, not historical screen disclosures; vault update blocks differ.'};(O/'public_snapshot_summary.json').write_text(json.dumps(live,indent=2))
market_checks=pd.read_csv(O/'direct_market_cash_checks.csv');assert len(market_checks)==66 and market_checks.rpc_cash_raw.notna().all() and market_checks.gap_usdc.abs().max()==0
res={'direct_market_cash_checks':66,'direct_market_cash_max_gap_usdc':0,'ten_vault_original_days':len(g),'original_vault_dates':len(base),'max_original_asset_residual_usdc':base.asset_residual_usdc.abs().max(),'integer_regroup_max_gap_usdc':max(gaps),'direct_RPC_checks':30,'direct_RPC_max_asset_gap_usdc':rpc.gap_usdc.abs().max(),'original_model_reproduction_max_gap':max(gaps2),'ethena_states':100,'gap_states':39,'daily_grid_gap_spells':1,'figures_visually_reviewed':True,'base_archive_sha256':hashlib.sha256((O/'R38_CN_LaTeX_source.zip').read_bytes()).hexdigest()};(O/'VALIDATION.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2));print(json.dumps(live,indent=2))
