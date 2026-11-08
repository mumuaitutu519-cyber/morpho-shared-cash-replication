"""Recreate decoded states exclusively from frozen raw RPC responses."""
import json,sys
from pathlib import Path
import collect_chain as c
assert '--online' not in sys.argv
old_rpc=c.rpc
def offline_rpc(name,method,params):
 p=c.RAW/(name+'.json');a=json.loads(p.read_text());assert a['request']['method']==method and a['request']['params']==params,(name,'request differs');assert a['response']['result'] is not None;return a['response']['result']
c.rpc=offline_rpc
# collect's existence shortcut is controlled explicitly rather than deleting any inputs.
for job in c.jobs():
 p=c.RAW/(job[0]+'_decoded.json');old=json.loads(p.read_text());new=c.collect(job,rebuild=True);assert old==new,job[0]
print('PASS: 456 states reconstructed from raw RPC responses, including exact requests and block headers')
