"""Complete native-USDC Morpho V1 cohorts, including zero-current-assets addresses, at frozen states."""
from chain_access import *
import pandas as pd,importlib.util
R=A.parent;C=A/'cross_chain';RAW=C/'raw'
CONFIG={1:('ethereum','0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'),8453:('base','0x833589fcd6edb6e08f4c7c32d4f71b54bda02913')}
DATES=['2026-09-29','2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31']
spec=importlib.util.spec_from_file_location('chain_collector',R/'code/empirical/collect_chain.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
def discovery(chain):
 p=RAW/f'discovery_{chain}.json'
 if p.exists():return json.loads(p.read_text())['response']['data']['vaults']['items']
 q='{vaults(first:1000,where:{chainId_in:['+str(chain)+']}){items{address name asset{address symbol decimals} state{totalAssets} creationTimestamp} pageInfo{count countTotal}}}'
 u='https://api.morpho.org/graphql';req=urllib.request.Request(u,json.dumps({'query':q}).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'})
 with urllib.request.urlopen(req,timeout=40) as r:z=json.loads(r.read())
 assert 'errors' not in z;v=z['data']['vaults'];assert v['pageInfo']['count']==v['pageInfo']['countTotal'],v['pageInfo'];p.write_text(json.dumps({'url':u,'query':q,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':z}));return v['items']
def collect(chain,day):
 p=RAW/f'morpho_{chain}_{day}.json'
 if p.exists():return json.loads(p.read_text())
 name,asset=CONFIG[chain];boundary=int((pd.Timestamp(day,tz='UTC')+pd.Timedelta(days=1)).timestamp())
 if day=='2026-09-29':
  old=json.loads((R/f'enrichment/raw/{name}_all_chain/{name}_all_current_decoded.json').read_text());h={'chain':chain,'block':old['block'],'hash':old['block_hash'],'timestamp':old['timestamp'],'selection':'original September 29 census block'}
 else:h=block_at(chain,boundary)
 V=[x for x in discovery(chain) if x['asset']['address'].lower()==asset and x['creationTimestamp']<=h['timestamp']]
 c.V=V;c.VA=[x['address'].lower() for x in V];c.ASSET=asset;c.M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';c.RAW=RAW/'decoded';c.RAW.mkdir(exist_ok=True);c.rpc=lambda label,method,params:rpc(chain,method,params);c.batch=lambda label,b,calls:batch(chain,b,calls)
 out=c.collect((f'morpho_{chain}_{day}',h['block'],None));assert out['block_hash']==h['hash'];out['header']=h;out['chain']=chain;out['asset']=asset
 if day=='2026-09-29':
  oldset={v['address'] for v in old['vaults']};newset={v['address'] for v in out['vaults'] if v['totalAssets']>0};out['census_comparison']={'previous_positive_count':len(oldset),'positive_count':len(newset),'added_positive':sorted(newset-oldset),'lost_positive':sorted(oldset-newset)}
 p.write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':
 for chain in CONFIG:
  for day in DATES:
   try:
    z=collect(chain,day);print(chain,day,len(z['vaults']),sum(v['totalAssets']>0 for v in z['vaults']),len(z['market']),z.get('census_comparison',''),flush=True)
   except Exception as e:(RAW/f'morpho_{chain}_{day}.error.json').write_text(json.dumps({'error':str(e)}));print('ERROR',chain,day,str(e),flush=True)
