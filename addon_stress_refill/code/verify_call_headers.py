"""Crosscheck trace-source candidate blocks against original RPC archive headers."""
import gzip,json
from pathlib import Path
import pandas as pd
from preflight import O
from rpc import multi
def run():
    needed={c:set(pd.read_csv(O/f'A4_call_audit_{c}.csv').block.astype(int)) for c in [1,42161]};headers={}
    for path in (Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/addon_stress_refill/out/portal_raw')).glob('*.json.gz'):
        z=json.load(gzip.open(path,'rt'));c=z['chain']
        for block in z['rows']:
            h=block['header'];b=h['number']
            if b not in needed.get(c,set()):continue
            key=(c,b);value=(h['hash'],h['timestamp']);assert key not in headers or headers[key]==value;headers[key]=value
    checks=[]
    for chain,blocks in needed.items():
        blocks=sorted(blocks);observed=multi(chain,[('eth_getBlockByNumber',[hex(b),False]) for b in blocks])
        for block,header in zip(blocks,observed):
            source_hash,stamp=headers[(chain,block)];assert header['hash']==source_hash and int(header['timestamp'],16)==stamp
            checks.append(dict(chain=chain,block=block,hash=source_hash,timestamp=stamp,hash_and_time_match=True))
    pd.DataFrame(checks).to_csv(O/'A4_independent_header_checks.csv',index=False);print('Candidate trace-source headers match RPC',len(checks),flush=True)
if __name__=='__main__':run()
