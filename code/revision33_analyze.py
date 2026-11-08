from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'reports/revision33';s=pd.read_csv(O/'holder_states.csv',dtype=str);plan=json.loads((O/'collection_plan.json').read_text());a=pd.read_csv(R/'reports/revision24/deposit_timing_classification.csv',dtype=str);m=pd.read_parquet(R/'reports/revision29/market_cash_sequence.parquet').sort_values(['block','log_index']);out=[];summ=[]
for col in ['shares_raw','claim_micro','capacity_micro']:s[col]=s[col].map(int)
b=s[s.phase=='before'].set_index(['tx','owner']);full=[]
for phase in ['after','one_hour','six_hours','one_day']:
 z=s[s.phase==phase].set_index(['tx','owner']).join(b[['shares_raw','claim_micro','capacity_micro']],rsuffix='_before',how='inner');z['unchanged_shares']=z.shares_raw==z.shares_raw_before;z['positive_opening_claim']=z.claim_micro_before>0;z['capacity_change_usdc']=(z.capacity_micro-z.capacity_micro_before).map(float)/1e6;z['claim_change_usdc']=(z.claim_micro-z.claim_micro_before).map(float)/1e6;z['prior_cash_shortfall_usdc']=(z.claim_micro_before-z.capacity_micro_before).map(float)/1e6;z['fixed_request_covered']=z.capacity_micro>=z.claim_micro_before;z['material_initial_shortfall']=z.prior_cash_shortfall_usdc>1;z['covered_after_shortfall']=z.material_initial_shortfall&z.fixed_request_covered;z['material_capacity_gain']=z.capacity_change_usdc>1;z['phase']=phase;full.append(z.reset_index())
 for identity,selector in [('all_peers',z.identity!='Spark'),('Ethena',z.identity=='Ethena'),('other_sampled_peers',z.identity=='unnamed prior-top-five')]:
  for scope,keep in [('all_positions',selector&z.positive_opening_claim),('unchanged_shares',selector&z.positive_opening_claim&z.unchanged_shares)]:
   g=z[keep];summ.append({'phase':phase,'identity':identity,'scope':scope,'observations':len(g),'transactions':g.index.get_level_values('tx').nunique(),'initial_shortfalls':int(g.material_initial_shortfall.sum()),'positive_gain_over_1USDC':int(g.material_capacity_gain.sum()),'gain_over_1millionUSDC':int(g.capacity_change_usdc.gt(1e6).sum()),'switch_to_fixed_full_request_covered':int(g.covered_after_shortfall.sum()),'median_capacity_change_usdc':g.capacity_change_usdc.median(),'maximum_capacity_change_usdc':g.capacity_change_usdc.max()})
if not full:print('Awaiting post-deposit states');raise SystemExit
z=pd.concat(full,ignore_index=True);z.to_csv(O/'state_comparisons.csv',index=False);pd.DataFrame(summ).to_csv(O/'comparison_summary.csv',index=False)
# Operations and source bounds: sums are explicitly event marginal sums, not newly optimized endpoints.
for p in plan:
 g=a[a.tx==p['tx']];mm=m[m.tx==p['tx']];bm=m[m.block==p['block']];record={'tx':p['tx'],'block':p['block'],'date':p['date'],'deposit_count':len(g),'deposit_usdc':sum(map(int,g.deposit_micro))/1e6,'marginal_lower_sum_usdc':sum(map(int,g.lower_micro))/1e6,'marginal_upper_sum_usdc':sum(map(int,g.upper_micro))/1e6,'all_deposits_point_identified':all(g.lower_micro==g.upper_micro),'same_block_other_market_operations':int((bm.tx!=p['tx']).sum()),'same_block_other_cash_change_usdc':float(bm.loc[bm.tx!=p['tx'],'cash_delta_raw'].sum())/1e6,'exact_linked_vault_supply_usdc':float(mm.loc[mm.tagged_supply,'assets_raw'].sum())/1e6}
 out.append(record)
pd.DataFrame(out).to_csv(O/'transaction_source_cash_links.csv',index=False)
# Fixed-request execution census and deterministic controls, after the immediate census is complete.
post=z[(z.phase=='after')&(z.identity!='Spark')&z.positive_opening_claim&z.unchanged_shares].copy();selected=post[post.covered_after_shortfall].copy();selected['selection']='all_immediate_shortfall_to_covered'
if len(post.tx.unique())==93:
 comps=[]
 for name,mask in [('unchanged_failure',post.material_initial_shortfall&~post.fixed_request_covered),('unchanged_success',~post.material_initial_shortfall&post.fixed_request_covered)]:
  g=post[mask].sort_values(['deposit_block','owner']).head(5).copy();g['selection']=name;comps.append(g)
 selected=pd.concat([selected]+comps,ignore_index=True).drop_duplicates(['tx','owner'])
selected[['tx','owner','identity','deposit_block','claim_micro_before','selection']].to_csv(O/'execution_selection.csv',index=False)
summary={'planned_transactions':93,'observed_immediate_transactions':int(post.tx.nunique()),'immediate_unchanged_peer_observations':len(post),'switches':int(post.covered_after_shortfall.sum()),'switch_transactions':int(post.loc[post.covered_after_shortfall,'tx'].nunique()),'source_cash_link_rows':len(out),'owner_capacity_sums_not_joint_liquidity':True,'complete_phases':s.groupby('phase').tx.nunique().to_dict()};(O/'analysis_progress.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));print(pd.DataFrame(summ).query("phase=='after'").to_string(index=False))
