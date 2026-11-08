from pathlib import Path
import json,pandas as pd
from revision24_rpc import decode_bytes_array,selector
R=Path(__file__).resolve().parents[1];O=R/'reports/revision29';s=pd.read_csv(O/'holder_before_after_states.csv',dtype=str);n=0
for (b,phase),g in s.groupby(['deposit_block','phase'],sort=False):
 v=json.loads((O/'raw'/f'{b}_{phase}_views.json').read_text());c=json.loads((O/'raw'/f'{b}_{phase}_claims.json').read_text());views=decode_bytes_array(v['response']['result'],2*len(g));claims=decode_bytes_array(c['response']['result'],len(g));calls=decode_bytes_array('0x'+v['request']['params'][0]['data'][10:],2*len(g))
 for i,r in enumerate(g.itertuples()):
  assert calls[2*i]==selector('balanceOf(address)')+r.owner[2:].zfill(64)
  assert int(views[2*i],16)==int(r.shares_raw)
  assert int(views[2*i+1],16)==int(r.capacity_micro)
  assert int(claims[i],16)==int(r.claim_micro)
  assert int(v['request']['params'][1],16)==int(r.state_block)
  n+=1
x=pd.read_csv(O/'ethena_fixed_request_execution.csv',dtype=str)
for r in x.itertuples():
 z=json.loads((O/'raw'/f'{r.deposit_block}_{r.phase}_ethena_fixed_withdraw.json').read_text());resp=z['response'];status='success' if 'result' in resp else 'liquidity_revert' if resp.get('error',{}).get('data')=='0x4323a555' else 'other';assert r.status==status
 before=s[(s.deposit_block==r.deposit_block)&(s.phase=='before')&(s.named_identity=='Ethena')].iloc[0];data=z['request']['params'][0]['data'];assert int(data[10:74],16)==int(before.claim_micro);assert z['request']['params'][0]['from']==before.owner
j=pd.read_csv(R/'reports/revision30/source_to_peer_capacity.csv',dtype=str);linked=j[j.lower_micro.notna()];assert len(linked)==4
for r in linked.itertuples():assert int(r.lower_micro)==int(r.upper_micro)==int(r.deposit_micro_before)
result={'historical_owner_states_redecoded':n,'execution_requests_rechecked':len(x),'source_matched_events':len(linked),'raw_state_checks_passed':True,'scope':'Offline decoding of retained RPC records and exact source-table joins; not independent network recollection or re-solving all original provenance bounds.'};(R/'reports/revision30/raw_validation.json').write_text(json.dumps(result,indent=2));print(result)
