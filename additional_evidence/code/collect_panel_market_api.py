"""Complete missing event types using the existing Morpho indexed-operation route."""
from pathlib import Path
import pandas as pd,json,gzip,urllib.request,time,concurrent.futures
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';RAW=P/'raw/market_api';RAW.mkdir(parents=True,exist_ok=True);URL='https://api.morpho.org/graphql'
markets=json.loads((P/'raw/operation_query.json').read_text())['markets']
QUERY='''query($where:MarketTransactionFilters){marketTransactions(first:1000,skip:0,orderBy:Timestamp,orderDirection:Asc,where:$where){pageInfo{count countTotal limit skip} items{txHash timestamp blockNumber txIndex logIndex type user{address} market{marketId} data{__typename ... on MarketTransactionTransferData {assets shares}}}}}'''
def run(job):
 start,end=job;folder=RAW/str(start);folder.mkdir(exist_ok=True);where={'chainId_in':[8453],'marketUniqueKey_in':markets,'timestamp_gte':start,'timestamp_lte':end-1,'type_in':['Borrow','Withdraw']};total=None;n=0;page=0
 while True:
  file=folder/f'{page:05d}.json.gz';q={'query':QUERY,'variables':{'where':dict(where)}}
  if file.exists():packet=json.load(gzip.open(file,'rt'))['response']
  else:
   errors=[]
   for attempt in range(5):
    try:
     req=urllib.request.Request(URL,json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'});packet=json.load(urllib.request.urlopen(req,timeout=40));assert not packet.get('errors'),str(packet.get('errors'))
     with gzip.open(file,'wt') as f:json.dump({'url':URL,'request':q,'response':packet},f)
     break
    except Exception as e:errors.append(str(e));time.sleep(2**attempt)
   else:
    status={'start':start,'end':end,'complete':False,'events':n,'errors':errors};(folder/'error.json').write_text(json.dumps(status));return status
  r=packet['data']['marketTransactions'];batch=r['items'];total=r['pageInfo']['countTotal'] if total is None else total;n+=len(batch)
  if not batch:break
  where['cursor']={k:batch[-1][k] for k in ['txHash','logIndex']};page+=1
  if page%50==0:print('market API',start,n,total,flush=True)
 assert n==total,(n,total);status={'start':start,'end_exclusive':end,'complete':True,'events':n,'expected':total,'pages':page+1};(folder/'complete.json').write_text(json.dumps(status));print(status,flush=True);return status
if __name__=='__main__':
 bounds=[pd.Timestamp('2025-01-16',tz='UTC')]+list(pd.date_range('2025-02-01','2026-03-01',freq='MS',tz='UTC'))+[pd.Timestamp('2026-03-31',tz='UTC')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:results=list(ex.map(run,[(int(a.timestamp()),int(b.timestamp())) for a,b in zip(bounds,bounds[1:])]))
 (P/'raw/market_api_coverage.json').write_text(json.dumps(results,indent=2))
