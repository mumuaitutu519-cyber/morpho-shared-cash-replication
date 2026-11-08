"""Observe all ten fixed-sample vaults around the specified deposit block.

Online collection is explicit. Default replay validates every archived RPC request.
"""
from pathlib import Path
import importlib.util,json,sys
E=Path(__file__).resolve().parents[1];R=E.parent
spec=importlib.util.spec_from_file_location('chain',R/'code/empirical/collect_chain.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
c.RAW=E/'raw/cross_vault';c.RAW.mkdir(exist_ok=True)
online='--online' in sys.argv
if not online:
 def rpc(name,method,params):
  x=json.loads((c.RAW/(name+'.json')).read_text())
  assert x['request']['method']==method and x['request']['params']==params,name
  return x['response']['result']
 c.rpc=rpc
for phase,block in [('before',36399031),('after',36399032)]:
 name='oct04_'+phase;path=c.RAW/(name+'_decoded.json')
 old=json.loads(path.read_text()) if path.exists() else None
 z=c.collect((name,block,None),rebuild=not online)
 if not online:assert old==z
 # Read vault-share supply to distinguish changes in ownership from market interest.
 calls=[(v,c.sel('totalSupply()')) for v in c.VA]
 supplies=c.batch(name+'_vault_supply',block,calls)
 (c.RAW/(name+'_share_supply.json')).write_text(json.dumps(dict(zip(c.VA,[x[0] for x in supplies]))))
 print(phase,block,len(z['vaults']),'vaults',flush=True)
