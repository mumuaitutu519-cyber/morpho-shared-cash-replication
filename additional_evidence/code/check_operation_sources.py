from pathlib import Path
import gzip,json,pandas as pd
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';O=P/'outputs'
d=pd.read_parquet(P/'raw/market_operations_cash.parquet',columns=['tx','log_index','block','timestamp','market','kind','owner','assets_micro']);d=d.set_index(['tx','log_index']);checks=[];seen=set()
for f in sorted((P/'raw/operations').glob('*/*.jsonl.gz')):
 if f.name.startswith('._'):continue
 for line in gzip.open(f,'rt'):
  r=json.loads(line);head=r['header']
  for log in r.get('logs',[]):
   key=(log['transactionHash'],log['logIndex'])
   if key in seen:continue
   seen.add(key);row=d.loc[key];topics=log['topics'];w=[int(log['data'][i:i+64],16) for i in range(2,len(log['data']),64)];owner='0x'+topics[2][-40:]
   assert row.block==head['number'] and row.timestamp==head['timestamp'] and row.market==topics[1] and row.owner==owner and row.assets_micro==w[1],(key,row.to_dict(),log)
   checks.append(dict(tx=key[0],log_index=key[1],block=head['number'],block_hash=head['hash'],kind=row.kind,assets_micro=int(row.assets_micro),match=True))
pd.DataFrame(checks).to_csv(O/'operation_source_crosscheck.csv',index=False);print('raw SQD / Morpho API exact matches',len(checks),flush=True)
