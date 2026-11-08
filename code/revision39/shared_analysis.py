from pathlib import Path
import json,pandas as pd,numpy as np
O=Path('reports/revision39_pilot');sel=json.loads((O/'selected_vaults.json').read_text());rows=[];rec=[];conflicts=[];marketvals={};marketnames={}
def series(a):
 assert len({int(x['x']) for x in a})==len(a)
 return {int(x['x']):None if x['y'] is None else int(x['y']) for x in a}
for rank,v in enumerate(sel,1):
 a=json.loads((O/'raw'/('history_'+v['address'].lower()+'.json')).read_text())['response']['data']['vaultByAddress'];h=a['historicalState'];assets=series(h['totalAssets']);parts=[]
 for al in h['allocation']:
  m=al['market'];key=m['marketId'].lower();marketnames[key]=str(m.get('collateralAsset',{}));parts.append((key,series(al['supplyAssets']),series(m['historicalState']['supplyAssets']),series(m['historicalState']['borrowAssets'])))
 for stamp,A in assets.items():
  if A is None:continue
  known=0;missing=0;invalid=0
  for key,p,s,b in parts:
   P=p.get(stamp)
   if P is None:missing+=1;continue
   known+=P
   if P<=0:continue
   S=s.get(stamp);B=b.get(stamp)
   if S is None or B is None:invalid+=1;continue
   assert P>=0 and S>=0 and B>=0 and S>=B,(key,stamp)
   mk=(stamp,key)
   if mk in marketvals and marketvals[mk]!=(S,B):conflicts.append([stamp,key,marketvals[mk],(S,B)])
   marketvals[mk]=(S,B)
   rows.append({'timestamp':stamp,'date':str(pd.Timestamp(stamp,unit='s',tz='UTC').date()-pd.Timedelta(days=1)),'rank':rank,'vault':v['address'].lower(),'name':v['name'],'market':key,'position_raw':P,'supply_raw':S,'borrow_raw':B,'cash_raw':S-B,'standalone_raw':min(P,S-B)})
  rec.append({'timestamp':stamp,'rank':rank,'vault':v['address'].lower(),'assets_raw':A,'known_positions_raw':known,'asset_residual_usdc':(A-known)/1e6,'null_positions':missing,'invalid_positive_markets':invalid})
r=pd.DataFrame(rows);c=pd.DataFrame(rec);r.to_parquet(O/'shared_positions.parquet',index=False);c.to_csv(O/'shared_reconciliation.csv',index=False)
print('RECON',c.shape,'maxgap',c.asset_residual_usdc.abs().max(),'bad>1',c.asset_residual_usdc.abs().gt(1).sum(),'invalid',c.invalid_positive_markets.sum(),'conflicts',len(conflicts),flush=True)
assert not conflicts
# A <=1 USDC arithmetic residual is explicitly retained; not a missing positive exposure.
valid=c[c.asset_residual_usdc.abs().le(1)&c.invalid_positive_markets.eq(0)]
old=['0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a','0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca','0xc0c5689e6f4d256e861f65465b691aeecc0deb12']
summ=[];daily=[];markets=[]
sets={'original3':old,'baseline8':[x['address'].lower() for x in sel[:8]],'baseline10':[x['address'].lower() for x in sel],'baseline9_exclude_extrafi':[x['address'].lower() for x in sel if x['name']!='Extrafi XLend USDC'],'exclude_spark':[x['address'].lower() for x in sel if x['name']!='Spark USDC Vault']}
for label,vs in sets.items():
 okay=valid[valid.vault.isin(vs)].groupby('timestamp').vault.nunique();okay=okay[okay.eq(len(vs))].index;z=r[r.vault.isin(vs)&r.timestamp.isin(okay)]
 for stamp,g in z.groupby('timestamp'):
  mm=g.groupby('market').agg(position_raw=('position_raw','sum'),cash_raw=('cash_raw','first'),supply_raw=('supply_raw','first'),separate_raw=('standalone_raw','sum'),vaults=('vault','nunique'))
  mm['joint_raw']=np.minimum(mm.position_raw,mm.cash_raw);mm['duplicate_raw']=mm.separate_raw-mm.joint_raw;assert (mm.duplicate_raw>=0).all();assert (mm.position_raw<=mm.supply_raw+100).all()
  S=int(mm.separate_raw.sum());J=int(mm.joint_raw.sum());D=S-J;date=g.date.iloc[0]
  row={'sample':label,'timestamp':stamp,'date':date,'S_usdc':S/1e6,'J_usdc':J/1e6,'D_usdc':D/1e6,'dup_pct':100*D/S if S else np.nan,'funded_markets':len(mm),'overlap_markets':int(mm.duplicate_raw.gt(0).sum()),'largest_market_share_pct':100*mm.duplicate_raw.max()/D if D else np.nan,'assets_usdc':c[c.timestamp.eq(stamp)&c.vault.isin(vs)].assets_raw.sum()/1e6};daily.append(row)
  for market,x in mm.iterrows():markets.append({'sample':label,'date':date,'market':market,'dup_usdc':x.duplicate_raw/1e6,'vaults':x.vaults})
d=pd.DataFrame(daily);d.to_csv(O/'shared_daily.csv',index=False);pd.DataFrame(markets).to_csv(O/'shared_market_contributions.csv',index=False)
for label in sets:
 for window,limit in [('original319','2025-11-30'),('extended593','2026-08-31')]:
  g=d[d['sample'].eq(label)&d.date.le(limit)].copy();summ.append({'sample':label,'window':window,'n':len(g),'first_date':g.date.min(),'last_date':g.date.max(),'median_S_million':g.S_usdc.median()/1e6,'median_J_million':g.J_usdc.median()/1e6,'median_D_million':g.D_usdc.median()/1e6,'median_dup_pct':g.dup_pct.median(),'p25_dup_pct':g.dup_pct.quantile(.25),'p75_dup_pct':g.dup_pct.quantile(.75),'max_dup_pct':g.dup_pct.max(),'median_largest_market_pct':g.largest_market_share_pct.median(),'median_overlap_markets':g.overlap_markets.median(),'positive_dup_days':int(g.D_usdc.gt(1).sum())})
pd.DataFrame(summ).to_csv(O/'shared_summary.csv',index=False);print(pd.DataFrame(summ).to_string(index=False));(O/'shared_validation.json').write_text(json.dumps({'vaults':len(sel),'vault_dates':len(c),'max_asset_residual_usdc':c.asset_residual_usdc.abs().max(),'reconciliation_failed_dates':int(c.asset_residual_usdc.abs().gt(1).sum()),'null_position_observations':int(c.null_positions.sum()),'positive_position_missing_market_states':int(c.invalid_positive_markets.sum()),'cross_query_market_conflicts':len(conflicts)},indent=2))
