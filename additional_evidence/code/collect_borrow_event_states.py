"""Read every requested event horizon for the fixed ten-vault network; archive failures explicitly."""
from pathlib import Path
import sys,json,concurrent.futures,threading,time
import pandas as pd,numpy as np
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';O=P/'outputs';RAW=P/'raw/event_states';RAW.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(A/'.deps'));sys.path.insert(0,str(R/'code/empirical'));import collect_chain as cc
from chain_access import rpc,batch,sel,word
cc.RAW=RAW
import chain_access,panel_archive_rpc
cc.rpc=panel_archive_rpc.named
chain_access.rpc=panel_archive_rpc.generic
# Use the exact existing collector and its stored response format; no synthetic state substitution.
H={'m24':-86400,'m1':-3600,'pre':-2,'event':0,'p1':3600,'p6':21600,'p24':86400,'p72':259200,'p168':604800}

def main():
 e=pd.read_csv(O/'borrow_event_candidates.csv');e=e[e.keep_24h].copy();e['event_id']=e.market+':'+e.tx
 # Placebos: same timestamp, no Borrow in the whole UTC day in control market, same opening-supply decile.
 # Read pre-event states first; then construct positive-holder event eligibility and matching.
 jobs=sorted(e.block.sub(1).unique());preblocks=set(jobs);status=[]
 def get(block):
  try:
   z=cc.collect((f'block_{block}',int(block),None))
   if block in preblocks:
    universe=json.loads((P/'raw/operation_query.json').read_text())['markets'];missing=[m for m in universe if m not in z['market']]
    if missing:
     calls=[(cc.M,sel(fn)+m[2:]) for m in missing for fn in ['market(bytes32)','idToMarketParams(bytes32)']];answers=batch(8453,int(block),calls);rates=[];keys=[]
     for j,mid in enumerate(missing):
      state,params=answers[2*j:2*j+2];z['market'][mid]={'state':state,'params':params}
      if params[3] and state[2]>0 and z['timestamp']>state[4]:
       rates.append(('0x'+f'{params[3]:040x}',sel('borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))')+''.join(word(w) for w in params+state)));keys.append(mid)
     values=batch(8453,int(block),rates)
     for mid,value in zip(keys,values):z['market'][mid]['borrowRate']=value[0]
     (RAW/f'block_{block}_decoded.json').write_text(json.dumps(z))
   return dict(block=int(block),complete=True,hash=z['block_hash'],timestamp=z['timestamp'])
  except Exception as ex:return dict(block=int(block),complete=False,error=str(ex))
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
  for i,r in enumerate(ex.map(get,jobs),1):
   status.append(r)
   if i%100==0:print('pre states',i,len(jobs),sum(x['complete'] for x in status),flush=True)
 failed=[x['block'] for x in status if not x['complete']]
 if failed:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:repairs={x['block']:x for x in ex.map(get,failed)}
  status=[repairs.get(x['block'],x) for x in status]
 (P/'raw/pre_state_coverage.json').write_text(json.dumps(status,indent=2));print('pre states finished',len(jobs),flush=True)
 from build_panel import build
 ops=pd.read_parquet(P/'raw/market_operations_cash.parquet');borrowdays=set(zip(ops.loc[ops.kind.eq('Borrow'),'market'],pd.to_datetime(ops.loc[ops.kind.eq('Borrow'),'timestamp'],unit='s',utc=True).dt.strftime('%Y-%m-%d')));evs=[];placebos=[];missing=[]
 for r in e.itertuples():
  file=RAW/f'block_{r.block-1}_decoded.json'
  if not file.exists():missing.append(dict(event_id=r.event_id,reason='missing_pre_state'));continue
  z=json.loads(file.read_text());pp,vv=build(z);p=pd.DataFrame(pp);held=p[p.market.eq(r.market)&p.position.gt(0)]
  assert r.market in z['market'] or held.empty
  if r.market in z['market']:
   state=z['market'][r.market]['state'];assert int(state[0])-int(state[2])==int(r.preblock_cash_micro),(r.event_id,'preblock cash mismatch')
  rec=r._asdict();rec['pre_block_hash']=z['block_hash'];rec['vault_count']=len(held);rec['vaults']=';'.join(held.vault);rec['borrow_scaled']=r.borrow_micro/r.preblock_cash_micro if r.preblock_cash_micro>0 else np.nan;rec['event_type']='borrow';evs.append(rec)
  if held.empty:continue
  m=p.groupby('market').agg(supply=('market_supply','first'),count=('position',lambda s:int((s>0).sum())))
  for mid,entry in z['market'].items():
   if mid in m.index:continue
   state=entry['state'];supply=state[0]
   if 'borrowRate' in entry:
    first=entry['borrowRate']*(z['timestamp']-state[4]);second=first*first//(2*10**18);third=second*first//(3*10**18);supply+=state[2]*(first+second+third)//10**18
   m.loc[mid]=[supply,0]
  m=m[m.supply>0].copy();m['decile']=pd.qcut(m.supply.rank(method='first'),10,labels=False,duplicates='drop')
  if r.market not in m.index:continue
  day=pd.Timestamp(r.timestamp,unit='s',tz='UTC').strftime('%Y-%m-%d');cand=m[(m.decile==m.loc[r.market,'decile'])&m.index.to_series().ne(r.market)&m['count'].gt(0)];cand=cand[[ (x,day) not in borrowdays for x in cand.index]]
  if cand.empty:missing.append(dict(event_id=r.event_id,reason='no_same_decile_no_borrow_day_control'));continue
  mid=(np.log(cand.supply)-np.log(m.loc[r.market,'supply'])).abs().sort_values().index[0];hp=p[p.market.eq(mid)&p.position.gt(0)];pr=rec.copy();pr.update(event_id='placebo:'+r.event_id,matched_event_id=r.event_id,market=mid,event_type='placebo',vaults=';'.join(hp.vault),vault_count=len(hp),actual_borrow_micro=0,matched_borrow_micro=rec['borrow_micro'],borrow_micro=0);placebos.append(pr)
 events=pd.DataFrame(evs+placebos);events.to_csv(O/'borrow_event_list.csv',index=False);pd.DataFrame(missing).to_csv(O/'event_exclusions.csv',index=False);valid=events[events.vault_count>0].copy();grid=[]
 for r in valid.itertuples():
  for horizon,offset in H.items():grid.append(dict(event_id=r.event_id,event_type=r.event_type,market=r.market,horizon=horizon,block=int(r.block+offset//2),target_timestamp=int(r.timestamp+offset),event_block=r.block,vaults=r.vaults,vault_count=r.vault_count,borrow_scaled=r.borrow_scaled))
 grid=pd.DataFrame(grid);grid.to_csv(O/'event_horizon_grid.csv',index=False);todo=sorted(grid.block.unique());status=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
  for i,r in enumerate(ex.map(get,todo),1):
   status.append(r)
   if i%100==0:print('horizon states',i,len(todo),sum(x['complete'] for x in status),flush=True)
 failed=[x['block'] for x in status if not x['complete']]
 if failed:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:repairs={x['block']:x for x in ex.map(get,failed)}
  status=[repairs.get(x['block'],x) for x in status]
 (P/'raw/event_state_coverage.json').write_text(json.dumps(status,indent=2));print('all states finished',len(todo),flush=True)
if __name__=='__main__':main()
