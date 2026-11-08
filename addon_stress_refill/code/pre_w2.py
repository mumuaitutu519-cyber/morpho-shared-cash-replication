"""Read the exact last block before W2 for the frozen exposure groups."""
import json
from hourly import H,collect,rpc
def run():
    for chain in [1,42161]:
        br=json.loads((H/f'blocks_{chain}.json').read_text());r=next(r for r in br if r['utc']=='2025-11-03T00:00:00+00:00');b=r['pre_boundary_block'];header=rpc(chain,'eth_getBlockByNumber',[hex(b),False]);rr=dict(utc='pre_W2',target=r['target']-1,block=b,timestamp=int(header['timestamp'],16),hash=header['hash']);assert rr['timestamp']<r['target'];collect(chain,[rr]);print('pre-W2 state',chain,b,flush=True)
if __name__=='__main__':run()
