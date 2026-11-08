from audit_history import *
import numpy as np,math,hashlib
P=np.full((319,10,31),-1,dtype=np.int64);C=np.full((319,31),-1,dtype=np.int64);source=np.full((319,31),'',dtype=object);mi={m:i for i,m in enumerate(markets)};audit=[];failures=[]
for di,day in enumerate(dates):
 t=int((pd.Timestamp(day,tz='UTC')+pd.Timedelta(days=1)).timestamp())
 for m,mj in mi.items():
  if (m,t) in hist:C[di,mj]=hist[m,t][0]-hist[m,t][1];source[di,mj]='historical_graphql'
  for vi in range(10):
   if (vi,m,t) in pvals:P[di,vi,mj]=pvals[vi,m,t]
 rawfile=R/(day+'.json');a=json.loads(rawfile.read_text())
 for folder in [R,ROOT/'raw/history_audit_publicnode',ROOT/'raw/history_audit_tenderly']:
  f=folder/(day+'.json')
  if not f.exists():continue
  z=json.loads(f.read_text())
  for att in z['attempts']:
   if 'error' in att:failures.append({'date':day,'source':str(f.relative_to(ROOT)),'attempt':att['attempt'],'error':att['error'],'retrieved_utc':att['retrieved_utc']})
  if z['decoded'] is not None:a=z;rawfile=f
 for j,meta in enumerate(a['calls']):
  ok,h=a['decoded'][j] if a['decoded'] is not None else (False,'');vals=[int(h[k:k+64],16) for k in range(0,len(h),64)] if h else []
  status='unresolved';mj=mi[meta['market']];value=None
  if ok and meta['kind']=='market' and len(vals)==6:
   value=vals[0]-vals[2];assert value>=0;C[di,mj]=value;source[di,mj]='historical_rpc';status='observed'
  if ok and meta['kind']=='position' and len(vals)==3 and vals[0]==0:
   value=0;P[di,meta['vault_index'],mj]=0;status='zero_supply_shares_observed'
  if ok and meta['kind']=='position' and vals and vals[0]>0:status='nonzero_supply_shares_requires_conversion'
  audit.append({'date':day,'block':a['block'],**meta,'value_raw':value,'status':status,'raw_file':str(rawfile.relative_to(ROOT))})
pd.DataFrame(audit).to_csv(O/'historical_missing_field_audit.csv',index=False);pd.DataFrame(failures,columns=['date','source','attempt','error','retrieved_utc']).to_csv(O/'api_failures.csv',index=False)
valid=(P>=0).all(axis=(1,2))&(C>=0).all(axis=1); excluded=[dates[i] for i in range(319) if not valid[i]]
(O/'excluded_dates.json').write_text(json.dumps({'excluded_dates':excluded,'unknown_positions':int((P<0).sum()),'unknown_market_cash':int((C<0).sum())},indent=2))
assert valid.any(),'No complete dates; stop rather than impute'
rows=[];totals=[];smatrix=np.zeros((319,31),dtype=np.int64);jmatrix=smatrix.copy();dmat=smatrix.copy()
cb='0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836';ci=mi[cb]
old_daily=pd.read_csv(old/'shared_daily.csv');old_daily=old_daily[old_daily['sample'].eq('baseline10')].set_index('date');gaps=[]
for di,day in enumerate(dates):
 if not valid[di]:
  for m in markets:rows.append({'date':day,'market':m,'name':names[m],'status':'excluded_incomplete_date'})
  continue
 p=P[di];c=C[di];sm=np.minimum(p,c[None,:]).sum(axis=0);jm=np.minimum(p.sum(axis=0),c);dm=sm-jm;assert (dm>=0).all();S=int(sm.sum());J=int(jm.sum());D=S-J;assert int(dm.sum())==D
 smatrix[di]=sm;jmatrix[di]=jm;dmat[di]=dm
 # Independently construct total S and J in Python integer arithmetic.
 S2=sum(min(int(p[v,m]),int(c[m])) for v in range(10) for m in range(31));J2=sum(min(sum(int(p[v,m]) for v in range(10)),int(c[m])) for m in range(31));gaps.append([abs(S-S2),abs(J-J2),abs(int(dm.sum())-(S2-J2))])
 cashshare=c/c.sum() if c.sum()>0 else np.full(31,np.nan);dshare=dm/D if D>0 else np.full(31,np.nan);drop=int(dm.argmax());sf=S-int(sm[ci]);sd=S-int(sm[drop]);within=np.divide(dm,sm,out=np.full(31,np.nan),where=sm>0)
 totals.append({'date':day,'S_raw':S,'J_raw':J,'D_raw':D,'duplication_ratio':D/S if S>0 else None,'cash_hhi':sum(cashshare**2),'duplication_hhi':sum(dshare**2),'exclude_cbbtc_ratio':(D-int(dm[ci]))/sf if sf>0 else None,'dynamic_excluded_market':markets[drop],'exclude_largest_ratio':(D-int(dm[drop]))/sd if sd>0 else None,'cbbtc_share_difference':dshare[ci]-cashshare[ci],'old_S_gap_usdc':S/1e6-old_daily.loc[day,'S_usdc'],'old_J_gap_usdc':J/1e6-old_daily.loc[day,'J_usdc']})
 for mj,m in enumerate(markets):rows.append({'date':day,'market':m,'name':names[m],'chain_id':8453,'loan_asset':V[0]['asset']['address'],'cash_raw':int(c[mj]),'S_raw':int(sm[mj]),'J_raw':int(jm[mj]),'D_raw':int(dm[mj]),'cash_share':cashshare[mj],'duplication_share':dshare[mj],'within_market_duplication_ratio':within[mj],'positive_vaults':int((p[:,mj]>0).sum()),'cash_million_usdc':c[mj]/1e12,'cash_source':source[di,mj],'status':'complete'})
f=pd.DataFrame(rows);f.to_csv(O/'market_decomposition_daily.csv',index=False);d=pd.DataFrame(totals);d.to_csv(O/'market_totals_daily.csv',index=False)
summary=f[f.status.eq('complete')].groupby(['market','name']).agg(cash_share_median=('cash_share','median'),duplication_share_median=('duplication_share','median'),within_market_duplication_ratio_median=('within_market_duplication_ratio','median'),positive_vaults_median=('positive_vaults','median'),cash_million_usdc_median=('cash_million_usdc','median'),n_days=('date','count'),n_within_market_ratio_days=('within_market_duplication_ratio','count')).reset_index().sort_values(['duplication_share_median','market'],ascending=[False,True]);summary.insert(0,'rank',range(1,len(summary)+1));summary.to_csv(O/'market_decomposition.csv',index=False)
# All 2^10 masks are enumerated. Empty mask is explicitly undefined; 1023 non-empty subsets.
ratios=np.full((1024,319),np.nan);subsetrows=[]
for mask in range(1024):
 vs=[i for i in range(10) if mask&(1<<i)];k=len(vs)
 subsetrows.append({'mask':mask,'k':k,'contains_spark':4 in vs,'vaults':';'.join(V[i]['address'].lower() for i in vs)})
 if k==0:continue
 pp=P[valid][:,vs,:];cc=C[valid];s=np.minimum(pp,cc[:,None,:]).sum(axis=(1,2));j=np.minimum(pp.sum(axis=1),cc).sum(axis=1);assert (s>=j).all()
 if k==1:assert (s-j==0).all(),'k=1 nonzero duplication; stop'
 ratios[mask,valid]=np.divide(s-j,s,out=np.full(s.shape,np.nan),where=s>0)
subs=pd.DataFrame(subsetrows);subs.to_csv(O/'subset_manifest.csv',index=False);np.savez_compressed(O/'subset_daily_ratios.npz',ratio=ratios,dates=np.array(dates))
kr=[];kd=[]
for k in range(1,11):
 for group in ['all','with_spark','without_spark']:
  choose=subs.k.eq(k)
  if group!='all':choose &= subs.contains_spark.eq(group=='with_spark')
  masks=subs.loc[choose,'mask'].to_numpy();z=ratios[masks];med=[];lo=[];hi=[]
  for di,day in enumerate(dates):
   xs=z[:,di];xs=xs[np.isfinite(xs)];a=np.quantile(xs,[.1,.5,.9]) if len(xs) else [np.nan]*3
   lo.append(a[0]);med.append(a[1]);hi.append(a[2]);kd.append({'date':day,'k':k,'group':group,'valid_subsets':len(xs),'p10':a[0],'median':a[1],'p90':a[2]})
  finite=np.asarray(med)[np.isfinite(med)];kr.append({'k':k,'subset_count':len(masks),'group':group,'duplication_ratio_median':np.median(finite) if len(finite) else np.nan,'p10':np.nanmedian(lo) if len(finite) else np.nan,'p90':np.nanmedian(hi) if len(finite) else np.nan,'time_p10_of_daily_medians':np.quantile(finite,.1) if len(finite) else np.nan,'time_p90_of_daily_medians':np.quantile(finite,.9) if len(finite) else np.nan,'n_days':len(finite)})
pd.DataFrame(kr).to_csv(O/'k_curve.csv',index=False);pd.DataFrame(kd).to_csv(O/'k_curve_daily.csv',index=False)
checks={'fixed_dates':319,'complete_dates':int(valid.sum()),'vaults':10,'markets':31,'excluded_dates':excluded,'identity_max_error_raw':np.array(gaps).max(axis=0).tolist(),'negative_market_duplicates':0,'k1_max_duplication':float(np.nanmax(ratios[subs.k.eq(1)])),'nonempty_subsets':1023,'empty_subset_undefined':True,'api_failed_attempts':len(failures),'audit_call_count':len(audit),'unresolved_audit_calls':sum(x['status']=='unresolved' for x in audit),'median_duplication_ratio':d.duplication_ratio.median(),'cash_hhi_median':d.cash_hhi.median(),'duplication_hhi_median':d.duplication_hhi.median(),'exclude_cbbtc_median':d.exclude_cbbtc_ratio.median(),'exclude_largest_median':d.exclude_largest_ratio.median(),'cbbtc_cash_share_median':summary.set_index('market').loc[cb,'cash_share_median'],'cbbtc_duplication_share_median':summary.set_index('market').loc[cb,'duplication_share_median'],'cbbtc_daily_difference_median':d.cbbtc_share_difference.median(),'old_daily_S_max_gap_usdc':d.old_S_gap_usdc.abs().max(),'old_daily_J_max_gap_usdc':d.old_J_gap_usdc.abs().max()}
(O/'validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2));print(pd.DataFrame(kr).to_string(index=False))
