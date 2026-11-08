"""Joint requests and observed cross-vault states; all inequalities use integer USDC units."""
from pathlib import Path
import json,importlib.util
import pandas as pd,numpy as np
E=Path(__file__).resolve().parents[1];R=E.parent;O=E/'outputs';O.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('panel',R/'code/empirical/build_panel.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
SP='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
CB='0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836'
pos=pd.read_parquet(R/'outputs/empirical/positions.parquet');pos=pos[pos.date.between('2025-01-16','2026-03-30')]
v=pd.read_parquet(R/'outputs/empirical/vault_panel.parquet');v=v[v.date.between('2025-01-16','2026-03-30')];assert len(v)==4390 and (v.groupby('date').size()==10).all()
assert not v.duplicated(['date','vault']).any()
names=v[['vault','name']].drop_duplicates();three=names[names.name.str.contains('Spark|Moonwell Flagship|Gauntlet USDC Core',case=False)].vault.tolist();assert len(three)==3,names
daily=[];checks=[];hist=[]
for day,g in pos.groupby('date',sort=True):
 def totals(z):
  s=sum(min(int(r.position),int(r.market_cash)) for r in z.itertuples())
  j=sum(min(sum(int(x) for x in h.position),int(h.market_cash.iloc[0])) for _,h in z.groupby('market'))
  return s,j
 S,J=totals(g);vg=v[v.date==day];assert S==sum(int(x) for x in vg.capacity)
 for addr,h in g.groupby('vault'):
  sx=sum(min(int(x.position),int(x.market_cash)) for x in h.itertuples());wx=int(vg[vg.vault==addr].capacity.iloc[0]);checks.append({'date':day,'vault':addr,'standalone_micro':sx,'queue_capacity_micro':wx,'gap_micro':sx-wx})
 for label,z in [('All ten vaults',g),('Excluding Spark',g[g.vault!=SP]),('Excluding the dominant market',g[g.market!=CB]),('Three-vault subset, daily',g[g.vault.isin(three)])]:
  s,j=totals(z);hist.append({'date':day,'scope':label,'S_usdc':s/1e6,'J_usdc':j/1e6,'duplicate_usdc':(s-j)/1e6,'duplication_pct':100*(s-j)/s if s else np.nan})
 for f in [5,10,25]:
  requests=[int(a)*f//100 for a in vg.assets];passed=[r<=int(w) for r,w in zip(requests,vg.capacity)];rq=sum(requests)
  daily.append({'date':day,'block':int(vg.block.iloc[0]),'request_pct':f,'vaults':len(vg),'individual_passes':sum(passed),'all_individual_pass':all(passed),'request_micro':rq,'J_micro':J,'S_micro':S,'joint_budget_excluded':all(passed) and rq>J,'cash_gap_micro':max(rq-J,0),'assets_micro':sum(int(a) for a in vg.assets)})
dd=pd.DataFrame(daily);dd.to_csv(O/'joint_request_daily.csv',index=False);pd.DataFrame(checks).to_csv(O/'standalone_queue_comparison.csv',index=False)
summary=[]
for f,g in dd.groupby('request_pct'):
 passed=g[g.all_individual_pass];bad=g[g.joint_budget_excluded];gap=bad.cash_gap_micro/1e6
 summary.append({'request_pct':int(f),'dates':len(g),'all_individual_pass':len(passed),'joint_budget_excluded':len(bad),'excluded_pct_of_passed':100*len(bad)/len(passed),'excluded_pct_all_dates':100*len(bad)/len(g),'median_gap_request_pct':float((100*bad.cash_gap_micro/bad.request_micro).median()) if len(bad) else None,'not_excluded':len(passed)-len(bad),'median_gap_usdc':float(gap.median()) if len(bad) else None,'max_gap_usdc':float(gap.max()) if len(bad) else None,'mean_gap_usdc':float(gap.mean()) if len(bad) else None})
pd.DataFrame(summary).to_csv(O/'joint_request_summary.csv',index=False)
pd.DataFrame(hist).to_csv(O/'historical_cash_daily.csv',index=False)
hs=pd.DataFrame(hist).groupby('scope',sort=False).agg(days=('date','size'),median_S_usdc=('S_usdc','median'),median_J_usdc=('J_usdc','median'),median_duplicate_usdc=('duplicate_usdc','median'),median_duplication_pct=('duplication_pct','median')).reset_index();hs.to_csv(O/'historical_cash_summary.csv',index=False)
x=pd.read_csv(R/'enrichment/outputs/cross_chain.csv');x['S_assets_pct']=100*x.S_usdc/x.assets_usdc;x['J_assets_pct']=100*x.J_usdc/x.assets_usdc;x.to_csv(O/'cross_chain_ratios.csv',index=False)
# Reconstruct all ten vaults before and after; keep zero/non-participating vaults in the audit.
states={};cross=[]
for phase in ['before','after']:
 z=json.loads((E/f'raw/cross_vault/oct04_{phase}_decoded.json').read_text());pr,vr=b.build(z);states[phase]=(z,pd.DataFrame(pr),pd.DataFrame(vr))
before,after=states['before'],states['after'];assert before[0]['block']+1==after[0]['block']==36399032
for addr in before[2].vault:
 rec={'vault':addr,'name':before[2].set_index('vault').loc[addr,'name']}
 for phase,(z,p,q) in states.items():
  vp=q.set_index('vault').loc[addr];pp=p[(p.vault==addr)&(p.market==CB)];a=pp.iloc[0] if len(pp) else None
  rec.update({phase+'_market_shares':str(z['positions'][addr].get(CB,[0])[0]),phase+'_position_usdc':int(a.position)/1e6 if a is not None else 0.,phase+'_capacity_usdc':int(vp.capacity)/1e6,phase+'_assets_usdc':int(vp.assets)/1e6,phase+'_common_cash_usdc':int(z['market'][CB]['state'][0]-z['market'][CB]['state'][2])/1e6})
  vs=json.loads((E/f'raw/cross_vault/oct04_{phase}_share_supply.json').read_text());rec[phase+'_vault_shares']=str(vs[addr])
 rec['market_shares_unchanged']=rec['before_market_shares']==rec['after_market_shares'];rec['vault_shares_unchanged']=rec['before_vault_shares']==rec['after_vault_shares'];rec['capacity_change_usdc']=rec['after_capacity_usdc']-rec['before_capacity_usdc'];rec['positive_common_position']=rec['before_position_usdc']>0 or rec['after_position_usdc']>0;cross.append(rec)
cv=pd.DataFrame(cross);cv.to_csv(O/'cross_vault_capacity.csv',index=False)
# Common-market aggregates use exact integer positions and cash, not printed rounded values.
agg=[]
for phase,(z,p,q) in states.items():
 pp=p[p.market==CB];cash=int(z['market'][CB]['state'][0])-int(z['market'][CB]['state'][2]);positions=sum(int(x) for x in pp.position)
 standalone=sum(min(int(x),cash) for x in pp.position);joint=min(positions,cash)
 assert positions>cash and joint==cash
 agg.append({'phase':phase,'block':z['block'],'selected_positions_micro':positions,'cash_micro':cash,'standalone_micro':standalone,'joint_micro':joint,'duplicate_micro':standalone-joint})
pd.DataFrame(agg).to_csv(O/'common_market_aggregate.csv',index=False)

# Rebuild the fixed 17-position cohort at every retained horizon.
c=pd.read_csv(R/'reports/revision33/state_comparisons.csv',dtype={'shares_raw':str,'shares_raw_before':str});initial=c[(c.phase=='after')&(c.identity!='Spark')&c.positive_opening_claim&c.material_initial_shortfall&c.unchanged_shares][['tx','owner']];assert len(initial)==17
paths=c.merge(initial,on=['tx','owner'],validate='many_to_one');paths.to_csv(O/'capacity_paths.csv',index=False);pers=[]
for phase in ['after','one_hour','six_hours','one_day']:
 g=paths[paths.phase==phase];u=g[g.unchanged_shares];assert len(g)==17
 pers.append({'phase':phase,'observed':len(g),'changed_shares':len(g)-len(u),'unchanged':len(u),'gains':int(u.material_capacity_gain.sum()),'full_request_covered':int(u.fixed_request_covered.sum()),'median_gain_usdc':float(u.capacity_change_usdc.median())})
pd.DataFrame(pers).to_csv(O/'capacity_persistence.csv',index=False)
res={'status':'PASS','historical_dates':439,'vault_dates':4390,'integer_inequalities':True,'S_equals_W_states':sum(x['gap_micro']==0 for x in checks),'maximum_S_W_gap_micro':max(abs(x['gap_micro']) for x in checks),'joint_requests':summary,'cross_vaults':len(cv),'positive_common_market_vaults':int(cv.positive_common_position.sum()),'persistence':pers}
(O/'analysis_checks.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2));print(cv[['name','before_position_usdc','after_position_usdc','before_capacity_usdc','after_capacity_usdc','market_shares_unchanged','vault_shares_unchanged']].to_string(index=False))
