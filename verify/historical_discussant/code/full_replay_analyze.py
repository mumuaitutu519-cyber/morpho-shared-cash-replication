"""Self-contained full replay; paths relative to this distributable bundle."""
from pathlib import Path
import json,hashlib,time
import numpy as np
import pandas as pd
from numba import njit

B=Path(__file__).resolve().parents[1]
D=B/'data'
O=B/'output'
O.mkdir(exist_ok=True)


@njit(cache=True)
def pay(cash,pos,queue,lengths,remaining,order):
    paid=0
    for v in order:
        if remaining[v]==0:continue
        for k in range(lengths[v]):
            m=queue[v,k]
            amount=min(remaining[v],pos[v,m],cash[m])
            if amount>0:
                remaining[v]-=amount;pos[v,m]-=amount;cash[m]-=amount;paid+=amount
            if remaining[v]==0:break
    return paid


@njit(cache=True)
def replay(cash0,pos0,queue,lengths,request,order,events,times,start):
    cash=cash0.copy();pos=pos0.copy();remaining=request.copy()
    initial=pay(cash,pos,queue,lengths,remaining,order)
    inflows=np.zeros(3,np.int64);clipped=0
    left24=remaining.copy();recorded24=False
    if remaining.sum()==0:return 0.,False,1.,initial,inflows,clipped,remaining.copy()
    for j in range(len(events)):
        if not recorded24 and times[j]>start+86400:
            left24=remaining.copy();recorded24=True
        m,kind,amount,own=events[j]
        if own:continue
        if kind<=2:
            cash[m]+=amount;inflows[kind]+=amount
            pay(cash,pos,queue,lengths,remaining,order)
            if remaining.sum()==0:
                if not recorded24:left24=remaining.copy()
                return (times[j]-start)/3600.,False,1.,initial,inflows,clipped,left24
        else:
            take=min(amount,cash[m]);cash[m]-=take;clipped+=amount-take
        assert cash[m]>=0
    if not recorded24:left24=remaining.copy()
    return 168.,True,(request.sum()-remaining.sum())/request.sum(),initial,inflows,clipped,left24


def run():
    begin=time.perf_counter()
    for r in json.loads((B/'input_manifest.json').read_text()):
        assert hashlib.sha256((B/r['path']).read_bytes()).hexdigest()==r['sha256'],r['path']
    p=pd.read_parquet(D/'positions.parquet');v=pd.read_parquet(D/'vault_states.parquet')
    cashgrid=pd.read_parquet(D/'market_cash.parquet')
    d=pd.concat([pd.read_parquet(D/'market_operations.parquet'),pd.read_parquet(D/'tail_operations.parquet')],ignore_index=True).sort_values(['block','log_index'])
    assert not d.duplicated(['tx','log_index']).any()
    markets=sorted(set(d.market)|set(p.market));mi={m:i for i,m in enumerate(markets)}
    vaults=sorted(v.vault.unique());vi={a:i for i,a in enumerate(vaults)}
    kinds={'Supply':0,'Repay':1,'Liquidation':2,'Borrow':3,'Withdraw':4}
    ev=np.column_stack([d.market.map(mi),d.kind.map(kinds),d.assets_micro,d.owner.isin(vaults).astype(int)]).astype(np.int64)
    blocks=d.block.to_numpy();times=d.timestamp.to_numpy()
    endcoverage=json.loads((D/'tail_coverage.json').read_text())['end']
    rows=[];pervault=[]
    for number,(date,g) in enumerate(p[p.date.between('2025-01-16','2026-03-30')].groupby('date'),1):
        vg=v[v.date.eq(date)].set_index('vault').reindex(vaults)
        block=int(vg.block.iloc[0]);start=int(vg.timestamp.iloc[0]);endblock=block+7*43200
        assert endblock<=endcoverage
        cash=np.zeros(len(markets),np.int64)
        for r in cashgrid[cashgrid.date.eq(date)].itertuples():cash[mi[r.market]]=int(r.cash)
        positions=np.zeros((10,len(markets)),np.int64);queue=np.full((10,32),-1,np.int64);lengths=np.zeros(10,np.int64)
        for r in g.itertuples():
            a,m=vi[r.vault],mi[r.market];positions[a,m]=int(r.position);queue[a,r.rank]=m;lengths[a]=max(lengths[a],r.rank+1)
        assets=vg.assets.to_numpy(np.int64)
        lo=np.searchsorted(blocks,block,side='right');hi=np.searchsorted(blocks,endblock,side='right')
        for ordername,priority in [('large_first',np.argsort(-assets,kind='stable')),('small_first',np.argsort(assets,kind='stable'))]:
            for f in [5,10,25]:
                request=assets*f//100
                tau,censored,fraction,initial,inflow,clipped,left24=replay(cash,positions,queue,lengths,request,priority,ev[lo:hi],times[lo:hi],start)
                rows.append(dict(date=date,f=f,order=ordername,tau=tau,censored=censored,paid_fraction=fraction,initial_paid_micro=initial,request_micro=int(request.sum()),supply_inflow_micro=int(inflow[0]),repay_inflow_micro=int(inflow[1]),liquidation_inflow_micro=int(inflow[2]),clipped_outflow_micro=clipped))
                if f==25 and ordername=='large_first':
                    assert (left24.sum()>0)==(tau>24)
                    for i,a in enumerate(vaults):pervault.append(dict(date=date,vault=a,request_micro=int(request[i]),remaining_24h_micro=int(left24[i]),not_paid24=int(left24[i]>0)))
        if number%25==0:
            pd.DataFrame(rows).to_csv(O/'replay_checkpoint.csv',index=False)
            print('Replay checkpoint',number,439,flush=True)
    q=pd.DataFrame(rows);q.to_csv(O/'full_replay.csv',index=False)
    pd.DataFrame(pervault).to_csv(O/'vault_replay_24h.csv',index=False)
    expected=pd.read_csv(D/'expected_replay.csv')
    joined=q.merge(expected,on=['date','f','order'],suffixes=('_new','_old'),validate='one_to_one')
    checks=[]
    for c in ['tau','censored','paid_fraction','initial_paid_micro','request_micro','supply_inflow_micro','repay_inflow_micro','liquidation_inflow_micro','clipped_outflow_micro']:
        dtype=float if c in ['tau','paid_fraction'] else np.int64
        gap=np.abs(joined[c+'_new'].astype(dtype)-joined[c+'_old'].astype(dtype))
        checks.append({'variable':c,'max_absolute_difference':float(gap.max()),'different_rows':int((gap>1e-12).sum())})
    pd.DataFrame(checks).to_csv(O/'replay_verification.csv',index=False)
    assert len(joined)==439*6 and not any(c['different_rows'] for c in checks)
    (O/'run_status.json').write_text(json.dumps({'status':'PASS','dates':439,'runs':len(q),'vault24_rows':len(pervault),'elapsed_seconds':time.perf_counter()-begin},indent=2))
    print('Full replay matches all archived runs:',len(q),flush=True)


if __name__=='__main__':run()
