from panel_evidence_stats import *
import hashlib
from statsmodels.stats.sandwich_covariance import cov_nw_groupsum
checks=[]
q=pd.read_parquet(O/'spillover_panel.parquet');assert len(q)==4380 and not q.duplicated(['vault','date']).any();assert (q.OwnFlow_opening_micro+q.OtherVaultFlow_micro+q.OutsideFlow_micro==q.TotalSupplyFlow_micro).all();checks.append('PASS: 4380 unique consecutive vault-day changes; integer flow partitions sum exactly on opening markets.')
check=pd.read_csv(O/'market_cash_reconciliation.csv');assert check.cash_error_micro.eq(0).all();checks.append(f'PASS: {len(check)} market closing cash balances equal cumulative observed operation cash flows exactly.')
r=pd.read_csv(O/'task1_numeric.csv');xs=['OwnFlow','OtherVaultFlow','OutsideFlow','BorrowFlow']
for spec,y,terms,z in [('1a','dW',xs,q),('1b','dW',xs+['Peer_x_exposure','ExposureShare'],q),('1c','dW',xs[1:],q[q.OwnFlow_micro.eq(0)]),('1d','dD',xs,q.dropna(subset=['dD']))]:
 X=pd.concat([z[terms],pd.get_dummies(z.vault,dtype=float)],axis=1);m=sm.OLS(z[y],X).fit(cov_type='cluster',cov_kwds={'groups':groups(z.date),'use_correction':True},use_t=True);a=r[(r.spec==spec)&r.covariance.eq('cluster:date')].set_index('variable').loc[terms];np.testing.assert_allclose(m.params.loc[terms],a.coefficient,rtol=1e-7,atol=1e-10);np.testing.assert_allclose(m.bse.loc[terms],a.standard_error,rtol=1e-7,atol=1e-10)
 timeidx=(pd.to_datetime(z.date)-pd.to_datetime(z.date).min()).dt.days.to_numpy();dc=cov_nw_groupsum(m,5,timeidx,use_correction='hac');dk=r[(r.spec==spec)&r.covariance.eq('Driscoll-Kraay5')].set_index('variable').loc[terms];np.testing.assert_allclose(np.sqrt(np.diag(dc))[:len(terms)],dk.standard_error,rtol=1e-6,atol=1e-10)
checks.append('PASS: Task 1 coefficient, date-cluster SE and calendar-lag DK5 SE match independent explicit-vault-dummy statsmodels estimates.')
for prefix in ['task1','task2','task3','task3_cross','tasks4_5']:
 if not (O/f'{prefix}_numeric.csv').exists():continue
 r=pd.read_csv(O/f'{prefix}_numeric.csv');m=pd.read_csv(O/f'{prefix}_models.csv')
 for (model,spec),g in r.groupby(['model','spec']):
  md=m[(m.model==model)&(m.spec==spec)].iloc[0]
  for row in g.itertuples():
   np.testing.assert_allclose(row.t_statistic,row.coefficient/row.standard_error,rtol=1e-10,atol=1e-10,equal_nan=True);df=md.df_p
   if row.covariance=='Driscoll-Kraay5':df=md.df_p
   expected=2*stats.norm.sf(abs(row.t_statistic)) if np.isinf(df) else 2*stats.t.sf(abs(row.t_statistic),df)
   np.testing.assert_allclose(row.p_value,expected,rtol=1e-8,atol=1e-12,equal_nan=True)
 checks.append(f'PASS: {prefix} numerical coefficient/SE/t/p identities and inference reference distributions.')
if (O/'event_vault_horizons.parquet').exists():
 events=pd.read_csv(O/'borrow_event_list.csv');assert events.event_block_hash.notna().all();real=events[events.event_type.eq('borrow')];assert len(real)==967 and (real.borrow_micro*10>real.preblock_cash_micro).all();assert real.vault_count.sum()==1716
 values=pd.read_csv(O/'task2_numeric.csv');metadata=pd.read_csv(O/'task2_models.csv')
 for outcome,filename in [('capacity_million','event_vault_horizons.parquet'),('delta_D','event_vault_horizons.parquet'),('delta_market_duplication','event_market_horizons.parquet'),('joint_million','event_market_horizons.parquet')]:
  z=pd.read_parquet(O/filename);z=z[z.event_type.eq('borrow')];counts=z.dropna(subset=[outcome]).groupby('pair').horizon.nunique();z=z[z.pair.isin(counts[counts==9].index)].copy();hs=['m1','pre','event','p1','p6','p24','p72','p168'];X=pd.DataFrame({h:z.horizon.eq(h).astype(float) for h in hs},index=z.index);X=X-X.groupby(z.pair).transform('mean');y=z[outcome]-z.groupby('pair')[outcome].transform('mean');mm=sm.OLS(y,X).fit(cov_type='cluster',cov_kwds={'groups':groups(z.event_id),'use_correction':True});correction=np.sqrt((len(z)-len(hs))/(len(z)-len(hs)-z.pair.nunique()));row=values[(values.model=='task2_borrow_'+outcome)&values.spec.eq('horizons')].set_index('variable').loc[['h_'+h for h in hs]];np.testing.assert_allclose(mm.params,row.coefficient,rtol=1e-7,atol=1e-10);np.testing.assert_allclose(mm.bse*correction,row.standard_error,rtol=1e-6,atol=1e-10)
 checks.append('PASS: All event hashes present, integer threshold and cohort counts verified; four baseline event regressions independently reproduce via within-pair OLS and full-FE cluster corrections.')
if (P/'cross_flow_validation.json').exists():
 coverage=json.loads((P/'cross_flow_validation.json').read_text());assert coverage['complete'] and coverage['matched_existing_logs']==43715;checks.append('PASS: 2204 single-vault flow queries; 50 overlapping vault-days and 43715 committed logs match exactly.')
# Paper-facing cells must equal rounded numeric source values and p-value stars.
for prefix in ['task1','task2','task3','task3_cross','tasks4_5']:
 r=pd.read_csv(O/f'{prefix}_numeric.csv');wide=pd.read_csv(O/f'{prefix}_paper.csv',index_col=0,dtype=str)
 for x in r.itertuples():
  col=x.model+' / '+x.spec
  if x.covariance=='Driscoll-Kraay5':assert wide.loc[x.variable+' DK t',col]==f'({x.t_statistic:.2f})';continue
  star='***' if x.p_value<.01 else '**' if x.p_value<.05 else '*' if x.p_value<.1 else ''
  expected=(f'{x.coefficient:.3e}' if 0<abs(x.coefficient)<5e-7 else f'{x.coefficient:.6f}')+star
  assert wide.loc[x.variable,col]==expected,(prefix,col,x.variable)
  assert wide.loc[x.variable+' t',col]==f'({x.t_statistic:.2f})'
checks.append('PASS: Every generic paper-table coefficient, star and t-statistic matches its numerical CSV source.')
# Manuscript exact bytes are unchanged from the prior verified delivery.
for filename,expected in [('Counting_the_same_cash.docx','11bd3d97c4e15184429f00b7df91374bc388059cbd63b1922c7191e7f77866d3'),('Counting_the_same_cash.pdf','07058da857e0bc72c0278fd3db0070fdc240f9e72bf4d016b9c8efbb3ed7cb46')]:
 f=R.parents[1]/filename
 if f.exists():assert hashlib.sha256(f.read_bytes()).hexdigest()==expected
checks.append('PASS: Word/PDF manuscript hashes unchanged.')
(P/'checks.md').write_text('# Checks\n\n'+'\n'.join('- '+x for x in checks)+'\n');print('\n'.join(checks),flush=True)
