"""Offline raw-response replay. No network requests; partial collection fails validation."""
from pathlib import Path
import json,hashlib
import pandas as pd
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision33';V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
plan=json.loads((O/'collection_plan.json').read_text());s=pd.read_csv(O/'holder_states.csv',dtype=str).set_index(['tx','phase','owner']);assert len(plan)==93
n=0;headers=0
for p in plan:
 for phase,offset in [('before',-1),('after',0),('one_hour',1800),('six_hours',10800),('one_day',43200)]:
  b=p['block']+offset;key=f'{b}_'+hashlib.sha256('|'.join(p['owners']).encode()).hexdigest()[:12]
  h=json.loads((O/'raw'/f'header_{b}.json').read_text());assert h['request']['params']==[hex(b),False];head=h['response']['result'];assert int(head['number'],16)==b;assert int(head['timestamp'],16)==p['timestamp']+2*offset;headers+=1
  calls=[]
  for owner in p['owners']:calls.extend([selector('balanceOf(address)')+owner[2:].zfill(64),selector('maxWithdraw(address)')+owner[2:].zfill(64)])
  q=json.loads((O/'raw'/f'{key}_views.json').read_text());assert q['request']['params']==[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(b)]
  vals=[int(x,16) for x in decode_bytes_array(q['response']['result'],len(calls))];sh=vals[::2];cap=vals[1::2]
  calls=[selector('convertToAssets(uint256)')+f'{v:064x}' for v in sh];q=json.loads((O/'raw'/f'{key}_claims.json').read_text());assert q['request']['params']==[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(b)];cl=[int(x,16) for x in decode_bytes_array(q['response']['result'],len(calls))]
  for owner,ss,cc,qq in zip(p['owners'],sh,cap,cl):
   x=s.loc[(p['tx'],phase,owner)];assert int(x.shares_raw)==ss and int(x.claim_micro)==qq and int(x.capacity_micro)==cc;assert x.state_hash==head['hash'];assert 0<=cc<=qq;n+=1
assert len(s)==n
ex=pd.read_csv(O/'fixed_request_executions.csv',dtype=str);assert len(ex)==22
for x in ex.itertuples():
 q=json.loads((O/'execution_raw'/f'{x.state_block}_{x.owner}.json').read_text());req=q['request'];assert req['params'][1]==hex(int(x.state_block));call=req['params'][0];assert call['from']==x.owner and call['to']==V;assert call['data']==selector('withdraw(uint256,address,address)')+f'{int(x.request_micro):064x}'+x.owner[2:].zfill(64)*2
 z=q['response'];status='success' if 'result' in z else 'liquidity_revert' if z.get('error',{}).get('data')=='0x4323a555' else 'other';assert status==x.status
pairs=ex.pivot(index=['tx','owner','selection'],columns='phase',values='status');counts=pairs.groupby(['before','after']).size().to_dict();assert counts=={('liquidity_revert','liquidity_revert'):5,('liquidity_revert','success'):1,('success','success'):5}
comparison=pd.read_csv(O/'state_comparisons.csv');post=comparison[(comparison.phase=='after')&(comparison.identity!='Spark')&comparison.positive_opening_claim];assert len(post)==495 and post.unchanged_shares.all();assert int(post.material_capacity_gain.sum())==17 and int(post.covered_after_shortfall.sum())==1
r={'passed':True,'transactions':93,'deposit_observations':94,'owner_states_exactly_redecoded':n,'headers_checked':headers,'fixed_request_calls':len(ex),'execution_pairs':{str(k):int(v) for k,v in counts.items()},'immediate_positive_peer_positions':len(post),'scope':'Re-decodes retained original RPC responses, checks exact request arguments and integer states. Does not independently recollect chain data or re-solve original funding bounds.'};(O/'raw_validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
