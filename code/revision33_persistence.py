from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'reports/revision33'
s=pd.read_csv(O/'state_comparisons.csv');links=pd.read_csv(O/'transaction_source_cash_links.csv');m=pd.read_parquet(R/'reports/revision29/market_cash_sequence.parquet').sort_values(['block','log_index']);blocks=m.block.to_numpy();cats=sorted(m.cash_class.unique());prefix={c:np.r_[0,np.cumsum(np.where(m.cash_class==c,m.cash_delta_raw.map(int),0),dtype=object)] for c in cats}
post=s[(s.phase=='after')&(s.identity!='Spark')&s.positive_opening_claim];cohort=post[post.material_initial_shortfall][['tx','owner']];z=s.merge(cohort,on=['tx','owner']);z['gain_retained_over_1USDC']=z.capacity_change_usdc>1;z['fixed_request_feasible_size']=z.claim_micro>=z.claim_micro_before
rows=[]
for phase in ['after','one_hour','six_hours','one_day']:
 g=z[z.phase==phase]
 for scope,gg in [('all_initially_constrained',g),('unchanged_shares',g[g.unchanged_shares])]:
  rows.append(dict(phase=phase,scope=scope,n=len(gg),share_changed=int((~gg.unchanged_shares).sum()),claim_too_small_for_original_request=int((~gg.fixed_request_feasible_size).sum()),capacity_above_baseline=int(gg.gain_retained_over_1USDC.sum()),full_original_request_covered=int(gg.fixed_request_covered.sum()),median_capacity_change_usdc=gg.capacity_change_usdc.median(),min_capacity_change_usdc=gg.capacity_change_usdc.min(),max_capacity_change_usdc=gg.capacity_change_usdc.max()))
z.to_csv(O/'initially_constrained_paths.csv',index=False);pd.DataFrame(rows).to_csv(O/'persistence_summary.csv',index=False)
flow=[]
for (tx,phase),g in s.groupby(['tx','phase']):
 x=g.iloc[0];left=np.searchsorted(blocks,int(x.deposit_block),side='right');right=np.searchsorted(blocks,int(x.state_block),side='right');row=dict(tx=tx,phase=phase,deposit_block=int(x.deposit_block),state_block=int(x.state_block),complete_retained_ledger=int(x.state_block)<=int(blocks[-1]),intervening_market_operations=int(right-left))
 for c,p in prefix.items():row[c+'_net_cash_usdc']=float(p[right]-p[left])/1e6
 flow.append(row)
pd.DataFrame(flow).to_csv(O/'intervening_cash_flows.csv',index=False)
z=post.merge(links,on='tx',suffixes=('','_source'));z['source_group']=np.where(z.all_deposits_point_identified,'Point identified',np.where(z.marginal_lower_sum_usdc==0,'Zero lower bound','Positive-width positive lower bound'));group=[]
for name,g in z[z.material_capacity_gain].groupby('source_group'):
 group.append(dict(group=name,owner_event_pairs=len(g),transactions=g.tx.nunique(),deposits=int(g.deposit_count_source.sum()),deposit_usdc=g.deposit_usdc.sum(),marginal_lower_sum_usdc=g.marginal_lower_sum_usdc.sum(),marginal_upper_sum_usdc=g.marginal_upper_sum_usdc.sum(),clean_blocks=int((g.same_block_other_market_operations==0).sum()),median_capacity_gain_usdc=g.capacity_change_usdc.median(),full_request_switches=int(g.covered_after_shortfall.sum())))
pd.DataFrame(group).to_csv(O/'capacity_gain_source_groups.csv',index=False)
z[z.material_capacity_gain].to_csv(O/'capacity_gain_events.csv',index=False)
print(pd.DataFrame(rows).to_string(index=False));print(pd.DataFrame(group).to_string(index=False))
