"""Keep the 252-event table and apply the requested exact-claim rule separately."""
import sqlite3,json
import pandas as pd
from preflight import R,O
def run():
    d=pd.read_csv(R/'real_consequences/outputs/A1_clean_call_audit.csv',dtype={'requested_assets_micro':str,'claim_convert_micro':str});d['strict_kept']=[int(a)<=int(c) and int(c)>=100_000_000 for a,c in zip(d.requested_assets_micro,d.claim_convert_micro)];d['_path']=d.trace_address.map(lambda s:tuple(json.loads(s)));d=d.sort_values(['block','txindex','_path']);dbpath=R/'real_consequences/raw/events.sqlite';db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True);db.row_factory=sqlite3.Row;rows=[]
    for key,g in d[d.strict_kept].groupby(['owner','vault','utc_hour'],sort=False):
        r=g.iloc[0].drop(labels='_path').to_dict();fa=tuple(json.loads(r['trace_address']));candidates=db.execute('select block,txindex,trace_address,timestamp,tx,assets_raw from calls where vault=? and owner=? and committed=1 and block>=? order by block,txindex',(r['vault'],r['owner'],int(r['block']))).fetchall();later=[dict(t) for t in candidates if (t['block'],t['txindex'],tuple(json.loads(t['trace_address'])))>(r['block'],r['txindex'],fa)];nxt=min(later,key=lambda s:(s['block'],s['txindex'],tuple(json.loads(s['trace_address'])))) if later else None
        r.update(calls_in_event=len(g),wait_hours=(nxt['timestamp']-r['timestamp'])/3600 if nxt else None,unresolved=nxt is None,next_success_tx=nxt['tx'] if nxt else None);rows.append(r)
    db.close();ev=pd.DataFrame(rows);ev.to_csv(O/'A4_base_strict_events.csv',index=False);d.drop(columns='_path').to_csv(O/'A4_base_strict_call_audit.csv',index=False)
    periods=pd.read_csv(O/'periods.csv');out=[]
    for r in periods.itertuples():
        x=ev[ev.date.between(r.start,r.end)]
        if r.exclude_other_window:x=x[~x.date.between('2025-10-09','2025-10-17')]
        done=x[~x.unresolved];out.append(dict(chain='Base',period=r.period,filter='strict_claim',events=len(x),holders=x.owner.nunique(),request_median=x.requested_USDC.median(),completed_share=len(done)/len(x) if len(x) else None,wait_median_hours=done.wait_hours.median()))
    old=pd.read_csv(O/'A4_base.csv');old=old[old['filter'].eq('Table11')];pd.concat([old,pd.DataFrame(out)],ignore_index=True).to_csv(O/'A4_base.csv',index=False);print('Base exact-claim events',len(ev),flush=True)
if __name__=='__main__':run()
