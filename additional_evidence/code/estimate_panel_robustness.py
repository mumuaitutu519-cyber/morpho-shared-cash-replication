from panel_evidence_stats import *
from statsmodels.stats.sandwich_covariance import cov_hac
spark='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
v=pd.read_parquet(R/'outputs/empirical/vault_panel.parquet');v=v[v.date.between('2025-01-15','2026-03-30')]
p=pd.read_parquet(R/'outputs/empirical/positions.parquet');p=p[p.date.between('2025-01-15','2026-03-30')]
d=pd.read_csv(A/'outputs/daily_estimation_data.csv');old=pd.read_csv(R/'outputs/empirical/daily.csv');old=old[old.date.between('2025-01-15','2026-03-30')].sort_values('date');old['J_assets']=old.J/old.assets
weighted=v.assign(w=v.D*v.assets).groupby('date').agg(w=('w','sum'),assets=('assets','sum'));old['weighted_duplication']=old.date.map(weighted.w/weighted.assets);undefined_days=v.loc[v.D.isna() & v.assets.gt(0),'date'].unique();old.loc[old.date.isin(undefined_days),'weighted_duplication']=np.nan
q=p[p.vault.ne(spark)];subs=[]
for day,g in q.groupby('date'):
 m=g.groupby('market').agg(P=('position','sum'),cash=('cash','first'),S=('standalone','sum'),borrow=('market_borrow','first'),supply=('market_supply','first'));m=m[m.P>0];J=np.minimum(m.P,m.cash).sum();S=m.S.sum();assets=v[v.date.eq(day)&v.vault.ne(spark)].assets.sum()/1e6
 subs.append(dict(date=day,assets=assets,duplication=(S-J)/S,J_assets=J/1e6/assets,cash_hhi=((m.cash/m.cash.sum())**2).sum(),utilization10=10*(m.P*m.borrow/m.supply).sum()/m.P.sum()))
sub=pd.DataFrame(subs).sort_values('date');rawflow=pd.read_csv(A/'outputs/spark_daily_flow.csv');flows=rawflow.set_index('date').spark_net_flow_micro
for frame in [old,sub]:
 frame['log_assets']=np.log(frame.assets);frame['spark_flow_share']=frame.date.map(flows).fillna(0)/1e6/frame.assets
 for name in ['cash_hhi','log_assets','utilization10','spark_flow_share']:frame['L_'+name]=frame[name].shift(1)
 frame['month']=frame.date.str[:7];frame['weekday']=pd.to_datetime(frame.date).dt.dayofweek.astype(str)
for outcome in ['duplication','J_assets']:
 terms=['L_cash_hhi','L_log_assets','L_utilization10']+(['L_spark_flow_share'] if outcome=='J_assets' else [])
 for spec in ['asset_weighted','exclude_Spark','HAC14_no_calendar_FE','lagged_outcome']:
  z=(sub if spec=='exclude_Spark' else old).copy();yname='weighted_duplication' if spec=='asset_weighted' else outcome
  xs=terms.copy();fe=[] if spec=='HAC14_no_calendar_FE' else ['month','weekday'];lags=14 if not fe else 7
  if spec=='lagged_outcome':z['lag_y']=z[yname].shift(1);xs+=['lag_y']
  z=z[z.date.ge('2025-01-16')].dropna(subset=[yname]+xs).copy();X=sm.add_constant(pd.concat([z[xs],pd.get_dummies(z[fe],drop_first=True,dtype=float)],axis=1) if fe else z[xs]);m=sm.OLS(z[yname],X).fit(cov_type='HAC',cov_kwds={'maxlags':lags,'use_correction':True},use_t=True)
  for x in xs:ROWS.append(dict(model='task4_'+outcome,spec=spec,variable=x,coefficient=m.params[x],standard_error=m.bse[x],t_statistic=m.tvalues[x],p_value=m.pvalues[x],covariance=f'HAC{lags}',wild_cluster_p=np.nan))
  if fe:
   gg=[groups(z[f]) for f in fe];yy=demean(z[yname].to_numpy(),gg);wr2=1-np.sum(m.resid**2)/np.sum(yy**2)
  else:wr2=np.nan
  META.append(dict(model='task4_'+outcome,spec=spec,Obs=len(z),FE=' + '.join(fe) or 'none',clusters='none',df_p=m.df_resid,R2=m.rsquared,within_R2=wr2,outcome_mean=z[yname].mean(),outcome=yname))
  z.to_csv(O/f'task4_daily_{outcome}_{spec}_data.csv',index=False)
save('task4_daily');print('daily robustness complete',flush=True)
c=pd.read_csv(A/'cross_chain/outputs/vault_state_panel.csv');c=c[~c.zero_S].copy();xs=['shared_market_share','active_markets','log_assets','utilization10','max_market_share']
for base,fe,mask in [('a',['chain'],c.date.eq('2026-09-29')),('b',['chain_state'],pd.Series(True,index=c.index)),('c',['entity','chain_state'],pd.Series(True,index=c.index))]:
 for chain in [1,8453,42161,137]:
  z=c[mask&c.chain.ne(chain)];fit('task4_cross_'+base,'exclude_'+str(chain),z,'D',xs,fe,['chain'] if base=='a' else ['entity']);save('task4_all')
 z=c[mask].copy()
 if z.date.nunique()>1:fit('task4_cross_'+base,'two_way_entity_date',z,'D',xs,fe,['entity','date'])
 else:TESTS.append(dict(model='task4_cross_'+base,spec='two_way_entity_date',test='availability',status='one date cluster: variance undefined'))
 save('task4_all')
print('cross robustness complete',flush=True)
# Existing shared-market estimator is market+date FE, market/date two-way clustering.
m=pd.read_csv(A/'outputs/market_estimation_at_least_2.csv');assert len(m)==3167
xs=['vault_count','utilization10','log_cash','largest_position_supply'];m['utilization_x_vaults']=m.utilization10*m.vault_count
fit('task5','interaction',m,'duplication',xs+['utilization_x_vaults'],['market','date'],['market','date']);cut=float(m.vault_count.median())
for spec,z in [('count_le_median',m[m.vault_count<=cut]),('count_gt_median',m[m.vault_count>cut])]:fit('task5',spec,z,'duplication',xs,['market','date'],['market','date'])
save('tasks4_5');(P/'robustness_status.json').write_text(json.dumps({'market_count_median':cut,'all_versions':'Archived states cover Morpho V1 native-USDC positions only. V2 adapters, their positions, and cross-token asset conversion states are absent. No all-version exposure was substituted.','undefined_asset_weighted_dates':list(undefined_days),'asset_weighted':'sum(assets_v*D_v)/sum(assets_v); same weighted outcome in both daily model control sets as explicitly requested','exclude_Spark':'Network S/J and aggregate controls recomputed from nine vaults; external Spark flow retained as a control in the J/assets specification, divided by nine-vault assets','HAC14':'Calendar fixed effects removed and lag 14 HAC used, as requested'},indent=2))
(O/'tasks4_5_notes.txt').write_text('Daily duplication controls: lagged cash concentration, log total assets and position-weighted utilization per 10 points. Daily J/assets adds lagged Spark committed net flow / aggregate assets. Asset-weighted duplication is sum(assets_v*D_v)/sum(assets_v). Dates with a positive-assets zero-S vault have an undefined weighted outcome and are excluded from that outcome only; these dates are listed in robustness_status.json. Spark exclusion recomputes the nine-vault network and controls. HAC14 columns omit year-month and weekday FE. Other daily columns use HAC7. Cross-chain controls match the frozen cross-chain round; leave-chain-out regressions recompute FE and cluster counts, retaining within-chain D. Market regressions use duplication as outcome, market/date FE and two-way clustered CR1 SE, t reference min(G,T)-1; utilization is per 10 points, cash is log million USDC. Low group has vault count <= median; high group > median. Negative two-way covariance diagonals are reported as missing SE, without replacement. *, **, *** denote 10%, 5%, 1%; parentheses contain t statistics.\n')
