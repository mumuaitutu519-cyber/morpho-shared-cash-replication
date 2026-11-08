"""Online public-state collection. Write a new destination; frozen inputs are not replaced."""
from pathlib import Path
import argparse,requests,json,datetime,importlib.util,time
p=argparse.ArgumentParser();p.add_argument('--chain',type=int,choices=[1,8453],required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args();E=a.destination.resolve();assert not E.exists(),'Choose a new capture directory';(E/'raw').mkdir(parents=True)
R=Path(__file__).resolve().parents[2];name='ethereum' if a.chain==1 else 'base';token='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48' if a.chain==1 else '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913';url='https://ethereum-rpc.publicnode.com' if a.chain==1 else 'https://base.gateway.tenderly.co'
q='{vaults(first:1000,where:{chainId_in:['+str(a.chain)+']},orderBy:TotalAssetsUsd,orderDirection:Desc){items{address name asset{address symbol decimals} state{totalAssets totalAssetsUsd blockNumber}} pageInfo{count countTotal}}}'
z=requests.post('https://api.morpho.org/graphql',json={'query':q},timeout=40).json();assert 'errors' not in z;v=z['data']['vaults'];assert v['pageInfo']['count']==v['pageInfo']['countTotal'],'Pagination required before selection';(E/f'raw/{name}_all_discovery.json').write_text(json.dumps({'url':'https://api.morpho.org/graphql','query':q,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':z}));chosen=[x for x in v['items'] if x['asset']['address'].lower()==token and x['state'] and int(x['state']['totalAssets'])>0];(E/f'raw/{name}_all_selected.json').write_text(json.dumps(chosen,indent=2))
spec=importlib.util.spec_from_file_location('chain',R/'code/empirical/collect_chain.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.V=chosen;c.VA=[x['address'].lower() for x in chosen];c.ASSET=token;c.RAW=E/f'raw/{name}_all_chain';c.RAW.mkdir()
def rpc(label,method,params):
 request={'jsonrpc':'2.0','id':1,'method':method,'params':params}
 for attempt in range(3):
  try:
   response=requests.post(url,json=request,timeout=40).json();(c.RAW/(label+'.json')).write_text(json.dumps({'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request':request,'response':response}));assert response.get('result') is not None;return response['result']
  except Exception:
   if attempt==2:raise
   time.sleep(1)
c.rpc=rpc;header=rpc(name+'_finalized','eth_getBlockByNumber',['finalized',False]);block=int(header['number'],16);(E/f'raw/{name}_endpoint.json').write_text(json.dumps({'endpoint':url,'block':block,'header':header}));result=c.collect((name+'_all_current',block,None));print(name,len(result['vaults']),'vaults at',block)
