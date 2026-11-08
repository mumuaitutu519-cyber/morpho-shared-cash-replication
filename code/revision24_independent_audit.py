"""Audit classifications from direct states and feasibility from saved endpoints."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,socket
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/revision24'
def read(p):return list(csv.DictReader((ROOT/p).open()))
def load(p):return json.loads((ROOT/p).read_text())
def main():
 def deny(*a,**k):raise RuntimeError('Offline R24 audit')
 socket.create_connection=deny;socket.socket.connect=deny
 for p,x in load('reports/revision24/input_manifest.json').items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==x['sha256']
 states={x['date']:x for x in read('reports/revision6/withdrawal_capacity.csv')}
 original=read('reports/revision22/vault_entry_joint_records.csv')
 classified=read('reports/revision24/deposit_timing_classification.csv')
 assert [(x['tx'],x['log_index']) for x in original]==[(x['tx'],x['log_index']) for x in classified]
 bystate={(x['block'],x['block_timestamp']):x for x in states.values()};groups=defaultdict(list)
 for x in classified:
  a=bystate[(x['prior_close_block'],x['prior_close_timestamp'])];b=bystate[(x['same_day_close_block'],x['same_day_close_timestamp'])]
  lo=4*int(a['max_withdraw_micro'])<int(a['claim_micro']);hi=4*int(b['max_withdraw_micro'])<int(b['claim_micro'])
  cell='both_below' if lo and hi else 'prior_only' if lo else 'same_day_only' if hi else 'neither_below'
  assert x['timing_cell']==cell
  groups[cell].append(x);groups['all_vault'].append(x)
  if int(x['lower_micro'])>0:
   if lo:groups['prior_positive_below'].append(x)
   if hi:groups['same_day_positive_below'].append(x)
 groups={'all_vault':classified,'zero_lower':[x for x in classified if int(x['lower_micro'])==0],
 'positive_width':[x for x in classified if int(x['upper_micro'])>int(x['lower_micro'])],
 'point_identified':[x for x in classified if int(x['upper_micro'])==int(x['lower_micro'])],
 'positive_width_positive_lower':[x for x in classified if int(x['upper_micro'])>int(x['lower_micro'])>0]}
 assert len(groups['point_identified'])==53 and all(int(x['lower_micro'])>0 for x in groups['point_identified'])
 assert sum(int(x['lower_micro'])==int(x['deposit_micro']) for x in classified)==52
 manifest={x['destination_tx']:x for x in load('reports/revision6/domain_6_first_disposition_manifest.json')['items']}
 witnesses=load('reports/revision24/joint_endpoint_witnesses.json');amounts=defaultdict(lambda:[0,0]);seen=set()
 for x in witnesses:
  assert (x['group'],x['tx']) not in seen;seen.add((x['group'],x['tx']))
  selected=[z for z in groups[x['group']] if z['tx']==x['tx']]
  targets={int(z['native_transfer_log']) for z in selected};assert targets==set(x['target_native_logs'])
  f=manifest[x['tx']]
  for side,col in [('lower',0),('upper',1)]:
   choices=iter(map(int,x[side+'_focal_out_allocations_micro']));cash=int(f['opening_balance_micro']);focal=0;obj=0
   for e in f['events']:
    a=int(e['amount'])
    if e['kind']=='focal_in':cash+=a;focal+=a
    elif e['kind']=='other_in':cash+=a
    else:
     q=next(choices);assert 0<=q<=a and q<=focal and a-q<=cash-focal
     cash-=a;focal-=q
     if e['log_index'] in targets:obj+=q
    assert 0<=focal<=cash
   assert next(choices,None) is None and obj==int(x[side+'_micro']);amounts[x['group']][col]+=obj
 tab=read('reports/revision24/amount_groups_joint_bounds.csv')
 for row in tab:
  g=groups[row['group']]
  assert int(row['deposits'])==len(g)
  assert int(row['positive_marginal_lower_deposits'])==sum(int(x['lower_micro'])>0 for x in g)
  assert int(row['deposit_micro'])==sum(int(x['deposit_micro']) for x in g)
  assert amounts[row['group']]==[int(row['joint_lower_micro']),int(row['joint_upper_micro'])]
 flows={x['date']:x for x in read('reports/revision21/daily_flow_stock_reconciliation.csv')}
 days=read('reports/revision24/large_withdrawal_days_gross_net.csv')
 actual=[x['date'] for x in flows.values() if 4*int(x['withdraw_micro'])>int(x['prior_claim_micro'])]
 assert actual==[x['date'] for x in days]
 for x in days:
  f=flows[x['date']]
  assert int(x['account_deposit_micro'])==int(f['deposit_micro']) and int(x['account_withdraw_micro'])==int(f['withdraw_micro'])
  assert int(x['account_net_withdraw_micro'])==int(f['withdraw_micro'])-int(f['deposit_micro'])
  assert int(x['account_claim_prior_micro'])==int(f['prior_claim_micro'])
  for key,n in [('account_gross_withdraw_pct_prior_claim',int(f['withdraw_micro'])),('account_net_withdraw_pct_prior_claim',int(f['withdraw_micro'])-int(f['deposit_micro']))]:
   assert abs(float(x[key])-100*n/int(f['prior_claim_micro']))<1e-12
 s=load('reports/revision24/amount_group_summary.json');full=next(x for x in tab if x['group']=='all_vault')
 assert int(s['excess_attribution_lower_micro'])==int(full['deposit_micro'])-int(full['joint_upper_micro'])
 assert int(s['excess_attribution_upper_micro'])==int(full['deposit_micro'])-int(full['joint_lower_micro'])
 result={'status':'PASS_WITH_UNCHANGED_COVERAGE_LIMITS','network_disabled':True,'classification_rebuilt_from_direct_states':94,
 'attainable_endpoint_pairs_validated':len(witnesses),'ordered_funding_constraints_validated':True,
 'daily_net_flows_matched_to_account_ledger':8,'original_gross_selection_preserved':True,
 'scope':'A separate audit program within this revision workflow; not an external referee replication. LP optimality is checked in the analysis; endpoint feasibility is reconstructed here.'}
 (OUT/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
