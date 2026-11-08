"""Same-UTC-day committed net inflow at each frozen cross-chain state, with no look-ahead."""
from pathlib import Path
import json,gzip,time,urllib.request,concurrent.futures
import pandas as pd
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'real_consequences/code'));import rpc_limiter
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';C=A/'cross_chain';RAW=P/'raw/cross_state_flows_single';RAW.mkdir(parents=True,exist_ok=True);O=P/'outputs';URL='https://api.morpho.org/graphql'
rpc_limiter.RATES[URL]=3.
p=pd.read_csv(C/'outputs/vault_state_panel.csv');p['vault']=p.vault.str.lower();Q='''query($where:VaultV1TransactionFilters){vaultV1Transactions(first:1000,orderBy:Time,orderDirection:Asc,where:$where){pageInfo{hasNextPage count endCursor{txHash logIndex}} items{txHash timestamp blockNumber txIndex logIndex type assets shares vault{address}}}}'''
def run(job):
 chain,day,part,g=job;block=int(g.block.iloc[0]);f=(C/'raw' if chain in [1,8453] else A/'raw')/f'morpho_{chain}_{day}.json';z=json.loads(f.read_text());stamp=z.get('timestamp',z.get('header',{}).get('timestamp'));assert stamp is not None,z.keys();stamp=int(stamp);start=int(pd.Timestamp(day,tz='UTC').timestamp());where={'chainId_in':[int(chain)],'vaultAddress_in':g.vault.tolist(),'timestamp_gte':start,'timestamp_lte':stamp,'type_in':['Deposit','Withdraw']};folder=RAW/f'{chain}_{day}_{part}';folder.mkdir(exist_ok=True);page=0;rows=[]
 while True:
  q={'query':Q,'variables':{'where':dict(where)}};file=folder/f'{page:04d}.json.gz'
  if file.exists():r=json.load(gzip.open(file,'rt'))['response']
  else:
   for attempt in range(4):
    try:
     rpc_limiter.wait(URL,1)
     req=urllib.request.Request(URL,json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'});r=json.load(urllib.request.urlopen(req,timeout=35));assert not r.get('errors'),r
     with gzip.open(file,'wt') as f:json.dump({'url':URL,'request':q,'response':r},f)
     break
    except Exception as ex:
     if getattr(ex,'code',None)==429:rpc_limiter.backoff(URL,'429 resets in '+str(getattr(ex,'headers',{}).get('Retry-After','60'))+'s')
     if attempt==3:raise
     time.sleep(2**attempt)
  result=r['data']['vaultV1Transactions'];items=result['items'];assert len(items)==result['pageInfo']['count']
  for item in items:
   assert item['assets'] is not None
   rows.append(dict(chain=int(chain),date=day,snapshot_block=block,snapshot_timestamp=stamp,vault=item['vault']['address'].lower(),tx=item['txHash'],log_index=item['logIndex'],block=int(item['blockNumber']),timestamp=int(item['timestamp']),type=item['type'],assets_micro=int(item['assets'])))
  page+=1
  if not result['pageInfo']['hasNextPage']:break
  where['cursor']=result['pageInfo']['endCursor'];assert where['cursor']
 out={'chain':int(chain),'date':day,'part':part,'snapshot_block':block,'snapshot_timestamp':stamp,'pages':page,'returned_events':len(rows),'complete':True};(folder/'complete.json').write_text(json.dumps(out));return rows,out
if __name__=='__main__':
 jobs=[(int(c),d,i,g.iloc[i:i+1]) for (c,d),g in p.groupby(['chain','date']) for i in range(0,len(g))]
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for i,result in enumerate(ex.map(run,jobs),1):
   results.append(result)
   if i%100==0:print('single-vault flow jobs',i,len(jobs),flush=True)
 rows=[r for x,meta in results for r in x];d=pd.DataFrame(rows);assert not d.duplicated(['chain','date','tx','log_index']).any();d['within_state']=d.block<=d.snapshot_block;d['signed_micro']=d.assets_micro.where(d.type.eq('Deposit'),-d.assets_micro);d.to_parquet(RAW/'all_events.parquet',index=False);flow=d[d.within_state].groupby(['chain','date','vault']).signed_micro.sum();p['Flow_micro']=pd.MultiIndex.from_frame(p[['chain','date','vault']]).map(flow).fillna(0).astype('int64');p['Flow']=p.Flow_micro/1e12;p.to_csv(O/'cross_state_flow_data.csv',index=False);(P/'cross_state_flow_coverage.json').write_text(json.dumps([x[1] for x in results],indent=2));print('cross-state flows complete',len(d),len(p),flush=True)
