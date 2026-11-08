from chain_access import *
import pandas as pd,importlib.util
R=A.parent
spec=importlib.util.spec_from_file_location('source_collector',R/'code/empirical/collect_chain.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
CONFIG={42161:('0x6c247b1F6182318877311737BaC0844bAa518F5e','0xaf88d065e77c8cC2239327C5EDb3A432268e5831','0x878988f5f561081deEa117717052164ea1Ef0c82'),137:('0x1bF0c2541F820E775182832f06c0B7Fc27A25f67','0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359','0xa9c87daB340631C34BB738625C70499e29ddDC98')}
DATES=['2026-09-29','2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31']
def collect(chain,day):
 M,asset,fac=CONFIG[chain];boundary=int((pd.Timestamp(day,tz='UTC')+pd.Timedelta(days=1)).timestamp());h=block_at(chain,boundary);z=json.loads((A/'raw'/f'morpho_discovery_{chain}.json').read_text())['response']['data']['vaults'];assert z['pageInfo']['count']==z['pageInfo']['countTotal']
 selected=[x for x in z['items'] if x['asset']['address'].lower()==asset.lower() and int(x['creationTimestamp'])<boundary]
 c.V=selected;c.VA=[x['address'].lower() for x in selected];c.M=M.lower();c.ASSET=asset.lower();c.RAW=A/'raw/morpho_states';c.RAW.mkdir(exist_ok=True);c.rpc=lambda name,method,params:rpc(chain,method,params)
 out=c.collect((f'morpho_{chain}_{day}',h['block'],None));out['factory']=fac;out['header']=h;out['universe']='all API-indexed Vault V1 addresses; includes zero-assets vaults; creation before boundary';out['discovery_count_total']=z['pageInfo']['countTotal'];out['asset']=asset
 verify=batch(chain,h['block'],[(fac,sel('isMetaMorpho(address)')+word(int(v,16))) for v in c.VA]);out['factory_membership']={v:x[0] if x else None for v,x in zip(c.VA,verify)}
 (A/'raw'/f'morpho_{chain}_{day}.json').write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':
 for chain in CONFIG:
  for day in DATES:
   try:
    z=collect(chain,day);print(chain,day,len(z['vaults']),len(z['market']),set(z['factory_membership'].values()),flush=True)
   except Exception as e:(A/'raw'/f'morpho_{chain}_{day}.error.json').write_text(json.dumps({'error':str(e)}));print('ERROR',chain,day,str(e),flush=True)
