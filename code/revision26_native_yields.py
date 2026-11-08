from pathlib import Path
import pandas as pd,numpy as np,json
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';days=pd.date_range('2025-01-15','2025-11-30');bound=days+pd.Timedelta(days=1)
def ser(rows):
 s=pd.Series({pd.Timestamp(z['x'],unit='s'):np.nan if z['y'] is None else float(z['y']) for z in rows}).sort_index();return s.reindex(bound).set_axis(days).astype(float)
res=pd.DataFrame(index=days);validation={}
for name in ['spark','moonwell','gauntlet']:
 h=json.loads((O/'raw'/f'{name}_native_inputs.json').read_text())['response']['data']['vaultByAddress']['historicalState'];total=ser(h['totalAssets']);allocated=total*0;weighted=total*0;missing=total*0
 for a in h['allocation']:
  p=ser(a['supplyAssets']);rate=ser(a['market']['historicalState']['supplyApy']);missing+=((p>0)&rate.isna()).astype(int);assert not ((p>0)&rate.isna()).any()
  allocated+=p.fillna(0);weighted+=p.fillna(0)*np.log1p(rate.fillna(0))
 fees=pd.Series({pd.Timestamp(z['x'],unit='s'):float(z['y']) for z in h['fee']}).sort_index();fee=fees.reindex(fees.index.union(bound)).sort_index().ffill().reindex(bound).set_axis(days);assert not fee.isna().any()
 gross=weighted/total;net=gross*(1-fee)
 res[name+'_native_APR']=gross;res[name+'_net_native_APR']=net;res[name+'_net_native_APY']=np.expm1(net);res[name+'_fee']=fee
 validation[name]={'days':len(total),'positive_positions_missing_rates':int(missing.sum()),'max_asset_reconciliation_gap_usdc':float((total-allocated).abs().max()/1e6),'native_net_APY_min':float(np.expm1(net).min()),'native_net_APY_max':float(np.expm1(net).max())}
 assert (total-allocated).abs().max()/1e6<.001
res['native_yield_premium_pp']=100*(res.spark_net_native_APR-(res.moonwell_net_native_APR+res.gauntlet_net_native_APR)/2)
res.to_csv(O/'native_yields.csv',index_label='date');(O/'native_yield_validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation,indent=2));print(res.loc[['2025-02-19','2025-06-21','2025-11-30']].to_string())
