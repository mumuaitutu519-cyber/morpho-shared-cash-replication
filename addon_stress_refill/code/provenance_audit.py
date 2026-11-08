"""Normalize old cache metadata and check inputs without changing responses."""
from pathlib import Path
import json,hashlib
import pandas as pd
from preflight import O
def run():
    repairs=[]
    for path in (O/'rpc').glob('*.json'):
        z=json.loads(path.read_text())
        if not isinstance(z,dict) or 'response' not in z:continue
        if z['request']['id']!=z['response']['id']:
            repairs.append(dict(path=str(path),canonical_request_id=z['request']['id'],wire_request_and_response_id=z['response']['id'],response_unchanged=True,prior_packet_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),response_sha256=hashlib.sha256(json.dumps(z['response'],sort_keys=True).encode()).hexdigest()));z['cache_canonical_id']=z['request']['id'];z['request']['id']=z['response']['id'];path.write_text(json.dumps(z))
    repairfile=O/'RPC_cache_metadata_repairs.csv';columns=['path','canonical_request_id','wire_request_and_response_id','response_unchanged','prior_packet_sha256','response_sha256'];frames=([pd.read_csv(repairfile)] if repairfile.exists() else [])+[pd.DataFrame(repairs,columns=columns)];pd.concat(frames,ignore_index=True).drop_duplicates('path').to_csv(repairfile,index=False)
    inventory=pd.read_csv(O/'all_input_inventory.csv');checked=[]
    for row in inventory.itertuples():
        if len(str(row.sha256))!=64:continue
        observed=hashlib.sha256(Path(row.path).read_bytes()).hexdigest();assert observed==row.sha256,('original source changed',row.path);checked.append(dict(path=row.path,sha256=observed,unchanged=True))
    pd.DataFrame(checked).to_csv(O/'original_source_integrity.csv',index=False);print('Original source hashes unchanged',len(checked),'old cache metadata normalized',len(repairs),flush=True)
if __name__=='__main__':run()
