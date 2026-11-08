"""A1 economic-request filtering and owner-vault-hour descriptive tables; no regressions."""
from pathlib import Path
import json,hashlib,gzip,sqlite3,concurrent.futures,datetime
import pandas as pd,numpy as np
import poolrpc
# Use independently paced archive endpoints without the long shared Azul/OnFinality queues.
poolrpc.PROVIDERS=[x for x in poolrpc.PROVIDERS if x[0] not in ["https://rpc.baseazul.dev","https://base.api.onfinality.io/public"]]
from rpc import word
E=Path(__file__).resolve().parents[1];O=E/'outputs';R=E.parent
CACHE=E/'raw/a1_convert_claims.json'

def fetch(j):
 key,v,b,o=j
 q={'jsonrpc':'2.0','id':0,'method':'eth_call','params':[{'to':v,'data':'0x70a08231'+word(o),'gas':'0xf4240'},hex(b-1)]}
 a=poolrpc.request_batch([q])[0];raw=[{'request':q,'response':a}]
 if not isinstance(a.get('result'),str) or len(a['result'])!=66:return key,{'error':'balance unavailable','raw':raw}
 shares=int(a['result'],16)
 q={'jsonrpc':'2.0','id':0,'method':'eth_call','params':[{'to':v,'data':'0x07a2d13a'+word(shares),'gas':'0xf4240'},hex(b-1)]}
 a=poolrpc.request_batch([q])[0];raw.append({'request':q,'response':a})
 if not isinstance(a.get('result'),str) or len(a['result'])!=66:return key,{'error':'convertToAssets unavailable','raw':raw}
 return key,{'vault':v,'preblock':b-1,'owner':o,'shares':str(shares),'claim_micro':str(int(a['result'],16)),'raw':raw}

def userop(r):
 q={'jsonrpc':'2.0','id':1,'method':'eth_getTransactionReceipt','params':[r['tx']]};key=hashlib.sha256(json.dumps(q,sort_keys=True).encode()).hexdigest();p=E/'raw/rpc'/(key+'.json.gz')
 packet=json.load(gzip.open(p,'rt'));rec=packet['response']['result'];topic=json.loads((E/'raw/entrypoint_event_source.json').read_text())['topic'];matched=[]
 for l in rec['logs']:
  t=l['topics']
  if len(t)==4 and t[0]==topic and ('0x'+t[2][-40:]).lower() in [r['owner'].lower(),r['caller'].lower()]:
   w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];matched.append({'hash':t[1],'success':bool(w[1])})
 return (not matched[0]['success']) if len(matched)==1 else (False if not matched else None),len(matched)

def main():
 d=pd.read_csv(O/'A1_liquidity_failures.csv',dtype={'requested_assets_micro':str});assert d.id.is_unique
 cache=json.loads(CACHE.read_text()) if CACHE.exists() else {};jobs={}
 for r in d.itertuples():
  key=f'{r.vault}:{r.block}:{r.owner}';jobs[key]=(key,r.vault,r.block,r.owner)
 pending=[j for k,j in jobs.items() if k not in cache or 'error' in cache[k]]
 assert not pending, 'This offline package requires all saved claim states.'
 print('claim queries',len(pending),flush=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
  futures=[ex.submit(fetch,j) for j in pending]
  for i,f in enumerate(concurrent.futures.as_completed(futures)):
   k,z=f.result();cache[k]=z;CACHE.write_text(json.dumps(cache))
   if i%25==0:print('claims',i+1,len(pending),flush=True)
 assert all('error' not in cache[k] for k in jobs),'Some exact claim reads are missing; rerun the resumable script.'
 names=pd.read_csv(R/'enrichment/outputs/base_all_vaults.csv');name_map=dict(zip(names.vault.str.lower(),names.name));d['vault_name']=d.vault.map(name_map).fillna(d.vault_name)
 rows=[]
 for r in d.to_dict('records'):
  z=cache[f"{r['vault']}:{r['block']}:{r['owner']}"];claim=int(z['claim_micro']);a=int(r['requested_assets_micro']);excess=100*a>101*claim;small=claim<100_000_000
  raw=json.loads((E/'raw/failure_states'/(hashlib.sha256(r['id'].encode()).hexdigest()+'.json')).read_text());capacity=raw['capacity_micro'];assets=raw['assets_micro']
  u,n=userop(r)
  rows.append({**r,'claim_convert_micro':str(claim),'claim_convert_USDC':claim/1e6,'requested_USDC':a/1e6,'excess_claim':excess,'claim_below_100':small,'kept':not(excess or small),'failed_userop':u,'matching_userop_events':n,'utc_hour':datetime.datetime.fromtimestamp(r['timestamp'],datetime.timezone.utc).strftime('%Y-%m-%dT%H:00:00Z'),'vault_cash_USDC':capacity/1e6,'vault_cash_assets':capacity/assets if assets else np.nan,'claim_difference_from_saved_preview_micro':claim-raw['owner_claim_micro'][0]})
 allcalls=pd.DataFrame(rows);allcalls.to_csv(O/'A1_clean_call_audit.csv',index=False)
 counts=[]
 for scope,x in [('all_162',allcalls),('primary_10',allcalls[allcalls.is_primary.eq(1)]),('additional_152',allcalls[allcalls.is_primary.eq(0)])]:
  counts.append({'sample':scope,'input_calls':len(x),'excess_only':int((x.excess_claim&~x.claim_below_100).sum()),'below_100_only':int((~x.excess_claim&x.claim_below_100).sum()),'both_reasons':int((x.excess_claim&x.claim_below_100).sum()),'excluded_calls':int((~x.kept).sum()),'retained_calls':int(x.kept.sum())})
 kept=allcalls[allcalls.kept].copy();kept['_trace']=kept.trace_address.map(lambda s:tuple(json.loads(s)));kept=kept.sort_values(['block','txindex','_trace'])
 db=sqlite3.connect(E/'raw/events.sqlite',timeout=60);db.row_factory=sqlite3.Row;events=[]
 for key,g in kept.groupby(['owner','vault','utc_hour'],sort=False):
  r=g.iloc[0].drop(labels=['_trace']).to_dict();fa=tuple(json.loads(r['trace_address']))
  # Actual committed calls allow ordering subsequent successes inside the same transaction.
  candidates=db.execute("select block,txindex,trace_address,timestamp,tx,assets_raw from calls where vault=? and owner=? and committed=1 and block>=? order by block,txindex",(r['vault'],r['owner'],int(r['block']))).fetchall()
  later=[dict(t) for t in candidates if (t['block'],t['txindex'],tuple(json.loads(t['trace_address'])))>(r['block'],r['txindex'],fa)]
  nxt=min(later,key=lambda t:(t['block'],t['txindex'],tuple(json.loads(t['trace_address'])))) if later else None
  r.update(event_id='|'.join(key),calls_in_event=len(g),event_failed_userop=bool(g.failed_userop.eq(True).any()) if g.failed_userop.notna().all() or g.failed_userop.eq(True).any() else None,wait_hours=(nxt['timestamp']-r['timestamp'])/3600 if nxt else np.nan,unresolved=nxt is None,next_success_tx=nxt['tx'] if nxt else None,next_success_amount_USDC=int(nxt['assets_raw'])/1e6 if nxt else np.nan)
  events.append(r)
 db.close();ev=pd.DataFrame(events);ev.to_csv(O/'A1_clean_events.csv',index=False)
 for c in counts:
  x=ev if c['sample']=='all_162' else ev[ev.is_primary.eq(1 if c['sample']=='primary_10' else 0)];c['deduplicated_events']=len(x);c['repeat_calls_collapsed']=c['retained_calls']-len(x)
 pd.DataFrame(counts).to_csv(O/'A1_clean_exclusions.csv',index=False)
 table=[]
 groups=sorted(list(ev.groupby('vault')),key=lambda z:z[1].vault_name.iloc[0])+[('ALL',ev)]
 for address,x in groups:
  name='ALL' if address=='ALL' else x.vault_name.iloc[0]
  scope='all_162' if address=='ALL' else ('primary_10' if x.is_primary.iloc[0]==1 else 'additional_152')
  table.append({'vault':name,'vault_address':address,'sample':scope,'events':len(x),'dates':x.date.nunique(),'failed_userop_events':int(x.event_failed_userop.eq(True).sum()),'request_median_USDC':x.requested_USDC.median(),'owner_claim_median_USDC':x.claim_convert_USDC.median(),'vault_cash_median_USDC':x.vault_cash_USDC.median(),'vault_cash_assets_median':x.vault_cash_assets.median(),'wait_median_hours':x.wait_hours.median(),'resolved_events':int((~x.unresolved).sum()),'unresolved_events':int(x.unresolved.sum())})
 pd.DataFrame(table).to_csv(O/'A1_clean_by_vault.csv',index=False)
 # A3 requires simultaneous positive positions of at least two selected vaults.
 m=pd.read_parquet(O/'market_daily_states.parquet');m=m[m.date.between('2025-01-16','2026-03-30')].copy();m['shared']=m.vaults.fillna('').map(lambda s:len(set(filter(None,s.split(';'))))>=2);m['hit']=m.shared&m.P.gt(0)&m.supply.gt(0)&m.cash_supply.lt(.001);eps=[]
 for market,g in m.sort_values(['market','date']).groupby('market'):
  last=None;run=[]
  for r in g.itertuples():
   day=pd.Timestamp(r.date)
   if not r.hit or (last is not None and (day-last).days!=1):
    if run:eps.append({'market':market,'start':run[0],'end':run[-1],'days':len(run)});run=[]
   if r.hit:run.append(r.date)
   last=day
  if run:eps.append({'market':market,'start':run[0],'end':run[-1],'days':len(run)})
 ep=pd.DataFrame(eps);hit=m[m.hit];ep.to_csv(O/'A3_shared_episodes.csv',index=False)
 pd.DataFrame([{'sample':'primary_10_shared_markets','dates':hit.date.nunique(),'markets':hit.market.nunique(),'episodes':len(ep),'episode_median_days':ep.days.median()}]).to_csv(O/'A3_shared_summary.csv',index=False)
 daily=pd.read_csv(O/'daily_states.csv');dates=set(ev.loc[ev.is_primary.eq(1),'date']);a=daily.loc[daily.date.isin(dates),'J_assets'];b=daily.loc[~daily.date.isin(dates),'J_assets']
 pd.DataFrame([{'sample':'primary_10','event_days':len(a),'non_event_days':len(b),'event_mean':a.mean(),'non_event_mean':b.mean(),'mean_difference':a.mean()-b.mean(),'event_median':a.median(),'non_event_median':b.median(),'median_difference':a.median()-b.median()}]).to_csv(O/'A1_clean_J_assets_comparison.csv',index=False)
 assert len(ev)==kept.groupby(['owner','vault','utc_hour']).ngroups
 assert len(a)+len(b)==439
 for c in counts:assert c['input_calls']==c['excess_only']+c['below_100_only']+c['both_reasons']+c['retained_calls'];assert c['retained_calls']==c['deduplicated_events']+c['repeat_calls_collapsed']
 checks={'input_calls':len(d),'unique_claim_states':len(jobs),'claim_preview_differences':int(allcalls.claim_difference_from_saved_preview_micro.ne(0).sum()),'ambiguous_userop_calls':int(allcalls.matching_userop_events.gt(1).sum()),'retained_calls':len(kept),'deduplicated_events':len(ev),'all_checks':'PASS','source_sha256':hashlib.sha256((O/'A1_liquidity_failures.csv').read_bytes()).hexdigest()}
 # Manuscripts are outside this data-only package; their source hashes are retained.
 assert sum(r['events'] for r in table[:-1])==table[-1]['events']==len(ev)
 (O/'A1_clean_checks.json').write_text(json.dumps(checks,indent=2))
 cp=E/'checks.md';base=cp.read_text().split('\n## A1 cleaning')[0] if cp.exists() else '# Checks\n';cp.write_text(base+'\n## A1 cleaning\n\n```json\n'+json.dumps(checks,indent=2)+'\n```\n')
 print(json.dumps(checks),flush=True)
if __name__=='__main__':main()
