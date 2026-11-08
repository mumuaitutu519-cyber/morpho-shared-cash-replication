"""Independent public-RPC spot checks, large and seeded random holders."""
from pathlib import Path
import pandas as pd,numpy as np,requests,json,hashlib,datetime
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';S='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
f=pd.read_csv(O/'owner_checkpoints.csv',dtype=str);states=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str).set_index('date');out=[];selection=[]
for day,g in f.groupby('date'):
 g=g[g.owner.ne(S)].copy();g['value']=g.shares_raw.map(int);g=g.sort_values('value',ascending=False);top=g.head(5);random=g.iloc[5:].sample(min(10,len(g)-5),random_state=260907);chosen=pd.concat([top,random]);selection.extend(chosen.drop(columns='value').to_dict('records'))
selection=pd.DataFrame(selection);selection.to_csv(O/'owner_validation_selection.csv',index=False)
for day,g in selection.groupby('date'):
 b=int(states.loc[day,'block']);calls=[]
 for a in g.owner:
  calls.extend([selector('balanceOf(address)')+a[2:].zfill(64),selector('maxWithdraw(address)')+a[2:].zfill(64)])
 body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(b)]};p=O/'raw'/('owner_validation_'+day+'.json')
 if p.exists():ob=json.loads(p.read_text());assert ob['request']==body
 else:
  r=requests.post('https://base.drpc.org',json=body,timeout=50);ob={'url':r.url,'status':r.status_code,'request':body,'response':r.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(r.content).hexdigest()};p.write_text(json.dumps(ob,indent=2));p.with_suffix('.body').write_bytes(r.content)
 if 'result' not in ob['response']:print(day,ob['response'],flush=True);continue
 vals=[int(x,16) for x in decode_bytes_array(ob['response']['result'],len(calls))]
 for i,(_,r) in enumerate(g.iterrows()):out.append({'date':day,'owner':r.owner,'block':b,'event_shares_raw':r.shares_raw,'rpc_shares_raw':str(vals[2*i]),'gap_raw':str(vals[2*i]-int(r.shares_raw)),'rpc_max_withdraw_micro':str(vals[2*i+1])})
 print(day,'checked',len(g),'exact',sum(int(x['gap_raw'])==0 for x in out if x['date']==day),flush=True)
pd.DataFrame(out).to_csv(O/'owner_rpc_validation.csv',index=False)
# Localize the aggregate gap with integer arithmetic, not floating-point cancellation.
g=pd.read_csv(O/'aggregate_share_reconciliation.csv',dtype=str);gap=[]
for r in g.to_dict('records'):
 residual=int(r['difference_raw'])-(int(r['direct_spark_shares_raw'])-int(r['event_spark_shares_raw']));gap.append({'date':r['date'],'non_spark_aggregate_gap_raw':str(residual)})
pd.DataFrame(gap).to_csv(O/'non_spark_integer_reconciliation.csv',index=False)
summary={'planned_rpc_checks':45,'completed_rpc_checks':len(out),'rpc_exact_matches':sum(int(x['gap_raw'])==0 for x in out),'non_spark_aggregate_exact_days':sum(int(x['non_spark_aggregate_gap_raw'])==0 for x in gap),'state_days':len(gap),'all_accounts_independently_validated':False,'rpc_url':'https://base.drpc.org'};(O/'owner_validation.json').write_text(json.dumps(summary,indent=2));print(summary)
