from pathlib import Path
import pandas as pd,sqlite3,json
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';O=P/'outputs'
v=pd.read_parquet(R/'outputs/empirical/vault_panel.parquet');v=v[v.date.between('2025-01-16','2026-03-30')].sort_values(['vault','date']);assert len(v)==4390
path=P/'raw/vault_committed_flows.parquet'
if not path.exists():
 c=sqlite3.connect(f'file:{R}/real_consequences/raw/events.sqlite?mode=ro',uri=True)
 q="select block,date,tx,logindex,vault,event,assets_raw from logs where is_primary=1 and event in ('Deposit','Withdraw')"
 d=pd.read_sql_query(q,c);d.assets_raw=d.assets_raw.map(int);d['signed_micro']=d.assets_raw.where(d.event.eq('Deposit'),-d.assets_raw);d.to_parquet(path,index=False);c.close();print('flows',len(d),flush=True)
else:d=pd.read_parquet(path)
f=d.groupby(['vault','date']).signed_micro.sum();v['Flow']=pd.MultiIndex.from_frame(v[['vault','date']]).map(f).fillna(0).to_numpy()/1e12
for pct in [10,25]:
 v['refused'+str(pct)]=(v.assets*pct>v.capacity*100).astype(float);v['next_refused'+str(pct)]=v.groupby('vault')['refused'+str(pct)].shift(-1)
v.to_parquet(O/'daily_prediction_data.parquet',index=False)
print('daily data ready',len(v),flush=True)
