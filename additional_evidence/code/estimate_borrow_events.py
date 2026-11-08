from panel_evidence_stats import *
from build_panel import build
RAW=P/'raw/event_states';grid=pd.read_csv(O/'event_horizon_grid.csv');events=pd.read_csv(O/'borrow_event_list.csv');cache={};missing=[];vaultrows=[];marketrows=[]
for block in sorted(grid.block.unique()):
 f=RAW/f'block_{block}_decoded.json'
 if not f.exists():missing.append({'block':int(block),'reason':'state_not_available'});continue
 z=json.loads(f.read_text());pp,vv=build(z);p=pd.DataFrame(pp);v=pd.DataFrame(vv).set_index('vault');m=p.groupby('market').agg(P=('position','sum'),S=('standalone','sum'),cash=('cash','first'));m['J']=np.minimum(m.P,m.cash);m['duplication']=(m.S-m.J)/m.S.where(m.S>0)
 for addr,h in p.groupby('vault'):
  other=h.market.map(m.P)-h.position;increment=(np.minimum(h.position+other,h.cash)-np.minimum(other,h.cash)).sum();S=int(h.standalone.sum());v.loc[addr,'D']=(S-increment)/S if S else np.nan
 cache[block]=(z,p,v,m)
events['matched_borrow_micro']=events.get('matched_borrow_micro',pd.Series(np.nan,index=events.index));mask=events.event_type.eq('placebo');events.loc[mask,'matched_borrow_micro']=events.loc[mask,'borrow_micro'].where(events.loc[mask,'borrow_micro'].ne(0),events.loc[mask,'matched_borrow_micro']);events.loc[mask,'borrow_micro']=0
events['event_block_hash']=events.block.map(pd.read_csv(O/'borrow_event_headers.csv').set_index('block')['hash']);events.to_csv(O/'borrow_event_list.csv',index=False)
for r in grid.itertuples():
 if r.block not in cache:continue
 z,p,v,m=cache[r.block];assert abs(z['timestamp']-r.target_timestamp)<=1,(r.block,z['timestamp'],r.target_timestamp)
 for addr in r.vaults.split(';'):
  vv=v.loc[addr];vaultrows.append(dict(event_id=r.event_id,event_type=r.event_type,horizon=r.horizon,block=r.block,block_hash=z['block_hash'],timestamp=z['timestamp'],vault=addr,pair=r.event_id+':'+addr,vault_count=r.vault_count,borrow_scaled=r.borrow_scaled,capacity_micro=int(vv.capacity),D=vv.D))
 if r.market in m.index:mr=m.loc[r.market];dup=mr.duplication;J=int(mr.J)
 else:dup=np.nan;J=0
 marketrows.append(dict(event_id=r.event_id,event_type=r.event_type,horizon=r.horizon,block=r.block,block_hash=z['block_hash'],timestamp=z['timestamp'],market=r.market,pair=r.event_id,vault_count=r.vault_count,borrow_scaled=r.borrow_scaled,market_duplication=dup,J_micro=J))
v=pd.DataFrame(vaultrows);m=pd.DataFrame(marketrows)
for frame,keys,measures in [(v,['pair'],['capacity_micro','D']),(m,['pair'],['market_duplication','J_micro'])]:
 pre=frame[frame.horizon.eq('pre')].set_index('pair')
 for col in measures:frame['pre_'+col]=frame.pair.map(pre[col]);frame['delta_'+col]=frame[col]-frame['pre_'+col]
v['capacity_million']=v.delta_capacity_micro/1e12;v['capacity_share']=v.delta_capacity_micro/v.pre_capacity_micro.where(v.pre_capacity_micro>0);m['joint_million']=m.delta_J_micro/1e12
v.to_parquet(O/'event_vault_horizons.parquet',index=False);m.to_parquet(O/'event_market_horizons.parquet',index=False)
descriptive=[]
for frame,columns in [(v,['capacity_million','capacity_share','delta_D']),(m,['delta_market_duplication','joint_million'])]:
 for outcome in columns:
  statsframe=frame.groupby(['event_type','horizon'])[outcome].agg(['count','mean','median']).reset_index();statsframe['outcome']=outcome;descriptive.append(statsframe)
pd.concat(descriptive,ignore_index=True).to_csv(O/'event_horizon_descriptives.csv',index=False,float_format='%.17g')
# Every reported regression uses complete horizon panels for its own outcome; no filled states.
horizons=['m1','pre','event','p1','p6','p24','p72','p168'];summary=[]
for kind in ['borrow','placebo']:
 for outcome,frame in [('capacity_million',v),('capacity_share',v),('delta_D',v),('delta_market_duplication',m),('joint_million',m)]:
  z=frame[frame.event_type.eq(kind)].copy();valid=z.dropna(subset=[outcome]).groupby('pair').horizon.nunique();good=valid[valid==9].index;z=z[z.pair.isin(good)].copy()
  if z.empty:summary.append(dict(kind=kind,outcome=outcome,status='no_complete_pairs'));continue
  ev=z[['event_id','vault_count']].drop_duplicates();center=ev.vault_count.mean();z['count_centered']=z.vault_count-center
  hs=[];ints=[];sizes=[]
  for h in horizons:
   a='h_'+h;b='count_'+h;c='size_'+h;z[a]=z.horizon.eq(h).astype(float);z[b]=z[a]*z.count_centered;z[c]=z[a]*z.borrow_scaled;hs.append(a);ints.append(b);sizes.append(c)
  for spec,terms in [('horizons',hs),('sharing_interaction',hs+ints),('borrow_size_interaction',hs+sizes)]:
   fit('task2_'+kind+'_'+outcome,spec,z,outcome,terms,['pair'],['event_id']);save('task2')
  summary.append(dict(kind=kind,outcome=outcome,status='estimated',Obs=len(z),events=z.event_id.nunique(),pairs=z.pair.nunique(),sharing_center=center))
pd.DataFrame(summary).to_csv(O/'event_estimation_coverage.csv',index=False);(P/'event_missing_states.json').write_text(json.dumps(missing,indent=2))
# One horizon-row table, with all requested outcomes and specs in column groups.
r=pd.DataFrame(ROWS);wide={}
for (model,spec),z in r.groupby(['model','spec'],sort=False):
 out={}
 for a in z.itertuples():
  star='***' if a.p_value<.01 else '**' if a.p_value<.05 else '*' if a.p_value<.1 else '';label=a.variable
  for short,long in [('m1','-1h'),('pre','Pre-event block'),('event','Event block'),('p1','+1h'),('p6','+6h'),('p24','+24h'),('p72','+72h'),('p168','+168h')]:
   if a.variable=='h_'+short:label=long
   if a.variable=='count_'+short:label=long+' x sharing count (demeaned)'
   if a.variable=='size_'+short:label=long+' x borrow/opening cash'
  out[label]=(f'{a.coefficient:.3e}' if 0<abs(a.coefficient)<5e-7 else f'{a.coefficient:.6f}')+star;out[label+' t']=f'({a.t_statistic:.2f})'
 mm=next(x for x in META if x['model']==model and x['spec']==spec);out.update({'Vault-event FE':'Yes' if 'capacity' in model or model.endswith('delta_D') else 'No','Event FE':'No' if 'capacity' in model or model.endswith('delta_D') else 'Yes','Obs.':mm['Obs'],'Event clusters':mm['clusters'],'Within R-squared':mm['within_R2']});column=model.replace('task2_borrow_','Borrow | ').replace('task2_placebo_','Placebo | ').replace('capacity_million','Capacity: million USDC').replace('capacity_share','Capacity: share of pre-event').replace('delta_D','Exposure: D').replace('delta_market_duplication','Market: duplication rate').replace('joint_million','Market: J million USDC');wide[column+' | '+spec]=out
pd.DataFrame(wide).rename_axis('horizon_or_statistic').to_csv(O/'task2_horizon_paper.csv');save('task2')
(O/'task2_notes.txt').write_text('Events are market-transaction borrow amounts exceeding 10% of preceding-block idle cash. An event is excluded if another threshold event occurred in that market during the preceding 24 hours. Vault exposure membership and sharing count are measured immediately before the event. Horizons are -24h, -1h, preceding block, event block, +1h, +6h, +24h, +72h, +168h. Outcomes are relative to the preceding block; regression horizon coefficients additionally use -24h as the reference. Vault outcomes absorb vault-event FE; market outcomes absorb event FE and are entered once per market-event-horizon. SE cluster by event, CR1, t reference G-1. Sharing interactions demean pre-event vault counts across events in each outcome sample. Size interactions use borrow / preceding-block idle cash. Placebo size interactions use the matched borrow event\'s assigned intensity; actual control borrow is zero. Placebos use the same timestamp, no Borrow in the control market on that UTC date, nearest log supply within the same size decile; unmatched events are listed. Complete nine-horizon pairs are used per outcome. *, **, *** denote 10%, 5%, 1%; parentheses show t statistics.\n')
