"""Frozen-cohort attribution comparisons, temporal cross-tab and gross/net flows."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,socket
from revision6_first_disposition import extrema,lp_check
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/revision23'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads((ROOT/p).read_text())
def read(p):return list(csv.DictReader((ROOT/p).open()))
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def write(n,rows):
 with (OUT/n).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 def deny(*a,**k):raise RuntimeError('Offline R23 analysis')
 socket.create_connection=deny;socket.socket.connect=deny
 inputs=['reports/revision22/vault_entry_joint_records.csv','reports/revision22/large_withdrawal_day_summary.csv',
 'reports/revision22/fee_residual_summary.json','reports/revision22/fee_residual_daily_audit.csv',
 'reports/revision6/domain_6_first_disposition_manifest.json','reports/revision6/withdrawal_capacity.csv',
 'reports/revision23/ANALYSIS_PLAN.md']
 save('input_manifest.json',{n:{'sha256':sha(ROOT/n),'bytes':(ROOT/n).stat().st_size} for n in inputs})
 v=read(inputs[0]);assert len(v)==94 and len({(x['tx'],x['log_index']) for x in v})==94
 frames={x['destination_tx']:x for x in load(inputs[4])['items']}
 cells=defaultdict(list)
 for x in v:
  prior=4*int(x['prior_close_capacity_micro'])<int(x['prior_close_claim_micro'])
  after=4*int(x['same_day_close_capacity_micro'])<int(x['same_day_close_claim_micro'])
  cell={(True,True):'both_below',(True,False):'prior_only',(False,True):'same_day_only',(False,False):'neither_below'}[(prior,after)]
  x.update({'prior_below_25pct':prior,'same_day_below_25pct':after,'timing_cell':cell,'positive_marginal_lower':int(x['lower_micro'])>0})
  cells[cell].append(x)
 write('deposit_timing_classification.csv',v)
 groups={**{k:cells[k] for k in ['both_below','prior_only','same_day_only','neither_below']},'all_vault':v,
 'prior_positive_below':[x for x in v if x['prior_below_25pct'] and x['positive_marginal_lower']],
 'same_day_positive_below':[x for x in v if x['same_day_below_25pct'] and x['positive_marginal_lower']]}
 witnesses=[];rows=[];maxerr=0
 for name,g in groups.items():
  pertx=defaultdict(list)
  for x in g:pertx[x['tx']].append(x)
  lower=upper=0
  for tx,h in sorted(pertx.items()):
   item=frames[tx];targets={int(x['native_transfer_log']) for x in h}
   events=[{**e,'target':e['log_index'] in targets} if e['kind']=='out' else e for e in item['events']]
   assert sum(e['kind']=='out' and e['target'] for e in events)==len(h)
   initial=int(item['opening_balance_micro']);lo=extrema(initial,events,False);hi=extrema(initial,events,True)
   check=lp_check(initial,events,lo[0],hi[0]);maxerr=max(maxerr,check['max_error_usdc'])
   lower+=lo[0];upper+=hi[0]
   witnesses.append({'group':name,'tx':tx,'target_native_logs':sorted(targets),'opening_micro':str(initial),
    'lower_micro':str(lo[0]),'upper_micro':str(hi[0]),'lower_focal_out_allocations_micro':list(map(str,lo[2])),
    'upper_focal_out_allocations_micro':list(map(str,hi[2])),'lp_error_usdc':check['max_error_usdc']})
  ml=sum(int(x['lower_micro']) for x in g);mu=sum(int(x['upper_micro']) for x in g)
  assert ml<=lower<=upper<=mu
  rows.append({'group':name,'deposits':len(g),'transactions':len(pertx),'positive_marginal_lower_deposits':sum(x['positive_marginal_lower'] for x in g),
   'deposit_micro':str(sum(int(x['deposit_micro']) for x in g)),'sum_marginal_lower_micro':str(ml),'sum_marginal_upper_micro':str(mu),
   'joint_lower_micro':str(lower),'joint_upper_micro':str(upper),'joint_lower_minus_marginal_micro':str(lower-ml),
   'marginal_upper_minus_joint_micro':str(mu-upper)})
 write('timing_cross_tab_and_joint_bounds.csv',rows);save('joint_endpoint_witnesses.json',witnesses)
 allrow=next(x for x in rows if x['group']=='all_vault');D=int(allrow['deposit_micro']);L=int(allrow['joint_lower_micro']);U=int(allrow['joint_upper_micro'])
 expected=load(inputs[4])['summary']['operation_bounds']['vault'];assert L==int(expected['lower_micro']) and U==int(expected['upper_micro'])
 both=len(cells['both_below']);prior=len(cells['prior_only']);after=len(cells['same_day_only']);neither=len(cells['neither_below'])
 summary={'cohort_deposits':94,'deposit_micro':str(D),'joint_funding_lower_micro':str(L),'joint_funding_upper_micro':str(U),
 'excess_attribution_lower_micro':str(D-U),'excess_attribution_upper_micro':str(D-L),'joint_width_micro':str(U-L),
 'zero_marginal_lower_deposits':sum(int(x['lower_micro'])==0 for x in v),'timing_counts':{k:len(g) for k,g in cells.items()},
 'timing_agreement_deposits':both+neither,'timing_disagreement_deposits':prior+after,'timing_disagreement_pct':100*(prior+after)/94,
 'positive_timing_counts':{k:sum(x['positive_marginal_lower'] for x in g) for k,g in cells.items()},
 'joint_groups':rows,'lp_max_error_usdc':maxerr,
 'interpretation':'Joint endpoints over the same per-transaction first-departure feasible sets. Temporal agreement is not entry-time capacity. Excess attribution is bounded, not point-observed.'}
 save('attribution_timing_summary.json',summary)
 days=read(inputs[1]);assert len(days)==8
 for x in days:
  x['account_net_withdraw_micro']=str(int(x['account_withdraw_micro'])-int(x['account_deposit_micro']))
  x['account_gross_withdraw_pct_prior_claim']=100*int(x['account_withdraw_micro'])/int(x['account_claim_prior_micro'])
  x['account_net_withdraw_pct_prior_claim']=100*int(x['account_net_withdraw_micro'])/int(x['account_claim_prior_micro'])
  assert x['account_gross_withdraw_pct_prior_claim']>25
 write('large_withdrawal_days_gross_net.csv',days)
 fees=load(inputs[2]);fee_fraction=100*int(fees['paired_verified_fee_raw'])/int(fees['original_residual_raw'])
 save('gross_net_and_fee_summary.json',{'selected_dates':[x['date'] for x in days],'net_withdraw_micro':{x['date']:x['account_net_withdraw_micro'] for x in days},
 'negative_net_dates':[x['date'] for x in days if int(x['account_net_withdraw_micro'])<0],
 'verified_fee_pct_original_gap':fee_fraction,'fee_coverage_unchanged':True,'no_reselection':True})
 result={'status':'PASS_WITH_UNCHANGED_COVERAGE_LIMITS','cohort_events':94,'timing_cells':4,'joint_group_solutions':7,
 'transaction_endpoint_pairs':len(witnesses),'lp_max_error_usdc':maxerr,'gross_selected_days_unchanged':8,
 'network_disabled':True,'regressions_reestimated':False,'new_raw_data_collected':False}
 save('analysis_validation.json',result);print(json.dumps(summary,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
