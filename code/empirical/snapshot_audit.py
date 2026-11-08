from pathlib import Path
import json,datetime,pandas as pd
R=Path(__file__).resolve().parents[2];O=R/'outputs/empirical';rows=[];details=[]
old=json.loads((R/'raw/review/public_live_liquidity_0437.json').read_text())
def unpack(tag,time,g,rest=None):
 pub=0;allpos={};cash={};resid=0;blocks=[]
 for v in g.values():
  st=v['state'];pub+=int(v['liquidity']['underlying']);b=int(st['blockNumber']);blocks.append(b);q=sum(int(a['supplyAssets']) for a in st['allocation']);r=int(st['totalAssets'])-q;resid+=r
  details.append({'capture':tag,'vault':v['address'],'name':v['name'],'capture_utc':time,'vault_block':b,'vault_timestamp_utc':datetime.datetime.fromtimestamp(int(st['timestamp']),datetime.timezone.utc).isoformat(),'assets_micro':int(st['totalAssets']),'allocation_micro':q,'residual_micro':r})
  for a in st['allocation']:
   m=a['market']['marketId'];s=a['market']['state'];c=int(s['supplyAssets'])-int(s['borrowAssets']);assert m not in cash or cash[m]==c;cash[m]=c;allpos[m]=allpos.get(m,0)+int(a['supplyAssets'])
 J=sum(min(p,cash[m]) for m,p in allpos.items());rows.append({'capture':tag,'capture_utc':time,'graphql_usdc':pub/1e6,'rest_usdc':rest,'known_position_joint_usdc':J/1e6,'residual_usdc':resid/1e6,'vault_block_min':min(blocks),'vault_block_max':max(blocks),'atomic_state':len(set(blocks))==1})
unpack('early_2026-09-08',old['retrieved_utc'],old['response']['data'])
for p in sorted((R/'raw').glob('public_liquidity_*.json')):
 x=json.loads(p.read_text());g=x['responses']['graphql']['data'];rest=sum(int(z['data']['withdrawable_assets']) for k,z in x['responses'].items() if k!='graphql' and z.get('data'));tm=x['responses']['graphql']['attempts'][-1]['retrieved_utc'];unpack(x['date_utc'],tm,g,rest/1e6)
pd.DataFrame(rows).to_csv(O/'api_capture_reconciliation.csv',index=False);pd.DataFrame(details).to_csv(O/'api_vault_blocks.csv',index=False)
chain=pd.read_csv(O/'daily.csv');chain=chain[chain.date.str.startswith('snapshot')];v=pd.read_parquet(O/'vault_panel.parquet');v=v[v.date.str.startswith('snapshot')];sn=[]
for a in chain.itertuples():
 z=v[v.date==a.date];ex=z[z.name.eq('Extrafi XLend USDC')].iloc[0];sn.append({'name':a.date,'block':int(z.block.iloc[0]),'timestamp_utc':datetime.datetime.fromtimestamp(int(z.timestamp.iloc[0]),datetime.timezone.utc).isoformat(),'standalone_usdc':a.S,'joint_usdc':a.J,'duplicate_usdc':a.duplicate,'duplication':a.duplication,'extrafi_total_assets_usdc':ex.assets/1e6,'extrafi_positions_usdc':ex.positions/1e6,'extrafi_lost_assets_usdc':ex.loss/1e6,'asset_reconciliation_gap_micro':int(z.asset_reconciliation_gap.abs().max())})
pd.DataFrame(sn).to_csv(O/'synchronized_snapshots.csv',index=False)
print(pd.DataFrame(sn).to_string(index=False))
