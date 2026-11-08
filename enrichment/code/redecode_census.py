from pathlib import Path
import importlib.util,json
E=Path(__file__).resolve().parents[1];R=E.parent
spec=importlib.util.spec_from_file_location('chain',R/'code/empirical/collect_chain.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
for chain,token in [('base','0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'),('ethereum','0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48')]:
 c.V=json.loads((E/f'raw/{chain}_all_selected.json').read_text());c.VA=[x['address'].lower() for x in c.V];c.ASSET=token;c.RAW=E/f'raw/{chain}_all_chain'
 def offline(name,method,params):
  a=json.loads((c.RAW/(name+'.json')).read_text());assert a['request']['method']==method and a['request']['params']==params,name;assert a['response']['result'] is not None;return a['response']['result']
 c.rpc=offline;p=c.RAW/f'{chain}_all_current_decoded.json';old=json.loads(p.read_text());new=c.collect((old['name'],old['block'],None),rebuild=True);assert old==new
 print('PASS',chain,len(new['vaults']),'vaults: reconstructed from exact archived requests and raw responses')
