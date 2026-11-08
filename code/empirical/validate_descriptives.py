from pathlib import Path
import json,itertools
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[2];O=R/'outputs/empirical';p=pd.read_parquet(O/'positions.parquet');p=p[p.date.between('2025-01-16','2025-11-30')];names=['all10','exclude_spark','exclude_cbbtc','three_vaults'];s='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';three={s,'0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca','0xc0c5689e6f4d256e861f65465b691aeecc0deb12'};cb='0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836';out=[]
for name,z in zip(names,[p,p[p.vault!=s],p[p.market!=cb],p[p.vault.isin(three)]]):
 rows=[]
 for day,g in z.groupby('date'):
  m=g.groupby('market').agg(P=('position','sum'),cash=('cash','first'),S=('standalone','sum'));S=m.S.sum();J=np.minimum(m.P,m.cash).sum();rows.append({'date':day,'D':(S-J)/1e6,'rate':100*(S-J)/S})
 q=pd.DataFrame(rows);out.append({'sample':name,'days':len(q),'median_duplicate_usdc':float(q.D.median()),'median_rate_percent':float(q.rate.median())})
# The two way exposure construction is an exact marginal identity in every state.
a=pd.read_parquet(O/'vault_panel.parquet');assert a.asset_reconciliation_gap.eq(0).all();assert a.loc[a.D.notna(),'D'].between(-1e-12,1+1e-12).all();assert ((a.assets-a.positions)==a.loss).all()
# Pair-window/sample attrition, rather than the maximum planned row count.
b=pd.read_parquet(O/'pair_panel.parquet');c=pd.read_parquet(O/'estimation_panel.parquet');u={'candidate_pair_days':len(b),'valid_30_day_correlations':int(b.fisher_z.notna().sum()),'valid_all_pair_regressors':len(b.dropna(subset=['fisher_z','overlap','size_similarity','shared_utilization'])),'zero_capacity_primary':int(c.capacity.eq(0).sum()),'undefined_D_primary':int(c.D.isna().sum()),'log_change_invalid_primary':int(c.dlog_W.isna().sum()),'primary_vault_days':len(c)}
(O/'sample_attrition.json').write_text(json.dumps(u,indent=2));(O/'historical_descriptive_crosscheck.json').write_text(json.dumps(out,indent=2));print(json.dumps({'descriptives':out,'attrition':u},indent=2))
