"""Read-only reconstruction and mandatory integer-unit reconciliation gates."""
from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

A = Path(__file__).resolve().parents[1]
R = Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/Replication_Package')
O = A / 'out'
O.mkdir(exist_ok=True)

def state(z):
    markets = {}
    for m,x in z['market'].items():
        s,ss,b,bs,last,fee = x['state']
        if 'borrowRate' in x:
            first=x['borrowRate']*(z['timestamp']-last)
            second=first*first//(2*10**18)
            third=second*first//(3*10**18)
            interest=b*(first+second+third)//10**18
            s+=interest; b+=interest
            fa=interest*fee//10**18
            if fa: ss+=fa*(ss+10**6)//(s-fa+1)
        markets[m] = dict(supply=s, borrow=b, cash=s-b, shares=ss)
    vaults=[]; positions=[]
    for v in z['vaults']:
        total=0; capacity=0
        for rank,m in enumerate(v['queue']):
            a=markets[m]; shares=z['positions'][v['address']][m][0]
            p=shares*(a['supply']+1)//(a['shares']+10**6)
            total+=p; c=min(a['cash'],z['morpho_token_balance'])
            capacity+=min(p,c)
            positions.append(dict(date=z['name'],block=z['block'],vault=v['address'],market=m,rank=rank,position=p,cash=c,market_cash=a['cash'],supply=a['supply'],borrow=a['borrow']))
        # Effective lostAssets follows the archived V1.1 accounting rule.
        loss=max(v['lostAssets'],v['lastTotalAssets']-total) if v['lostAssets'] is not None else 0
        vaults.append(dict(date=z['name'],block=z['block'],timestamp=z['timestamp'],vault=v['address'],name=v['name'],assets=v['totalAssets'],positions=total,loss=loss,capacity=capacity,gap=total+loss-v['totalAssets']))
    return markets,vaults,positions

def run():
    inventory=[]; vv=[]; pp=[]; mm=[]
    for path in sorted((R/'raw/chain_panel').glob('202*_decoded.json')):
        z=json.loads(path.read_text()); markets,vaults,positions=state(z)
        vv+=vaults; pp+=positions
        mm.extend(dict(date=z['name'],block=z['block'],timestamp=z['timestamp'],market=m,**x) for m,x in markets.items())
        inventory.append(dict(path=str(path),rows=len(vaults),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),role='daily raw state'))
    v=pd.DataFrame(vv); p=pd.DataFrame(pp); m=pd.DataFrame(mm)
    v.to_parquet(O/'vault_states.parquet',index=False);p.to_parquet(O/'positions.parquet',index=False)
    ms=m.copy();ms['shares']=ms.shares.map(str);ms.to_parquet(O/'market_states.parquet',index=False)
    checks={'asset_rows':len(v),'max_asset_gap_micro':int(v.gap.abs().max())}
    (O/'gate_results.json').write_text(json.dumps(checks,indent=2))
    assert v.gap.abs().max()<=1,checks
    opath=R/'additional_evidence/panel_evidence/raw/market_operations.parquet'
    d=pd.read_parquet(opath).sort_values(['block','log_index'])
    cp=R/'additional_evidence/panel_evidence/raw/opening_market_cash.json'
    c0=json.loads(cp.read_text())
    assert not d.duplicated(['tx','log_index']).any()
    assert set(d.kind)<=set(['Supply','Withdraw','Borrow','Repay','Liquidation'])
    d['cash_delta']=d.assets_micro*np.select([d.kind.isin(['Supply','Repay','Liquidation']),d.kind.isin(['Borrow','Withdraw'])],[1,-1],default=0)
    cashrows=[]
    for market,g in d.groupby('market'):
        blocks=g.block.to_numpy(); balances=g.cash_delta.cumsum().to_numpy()+int(c0[market])
        for r in m[m.market.eq(market)].itertuples():
            idx=np.searchsorted(blocks,r.block,side='right')-1
            observed=int(balances[idx]) if idx>=0 else int(c0[market])
            cashrows.append(dict(date=r.date,block=r.block,market=market,opening=int(c0[market]),ledger_cash=observed,state_cash=r.cash,gap=observed-r.cash))
    q=pd.DataFrame(cashrows);q.to_csv(O/'market_cash_reconciliation.csv',index=False)
    checks.update(operation_rows=len(d),cash_checks=len(q),max_cash_gap_micro=int(q.gap.abs().max()))
    (O/'gate_results.json').write_text(json.dumps(checks,indent=2))
    assert q.gap.abs().max()<=1,checks
    daily=[]; requests=[]
    for date,g in p[p.date.between('2025-01-16','2026-03-30')].groupby('date'):
        vg=v[v.date.eq(date)]
        S=sum(min(int(x.position),int(x.cash)) for x in g.itertuples())
        # Full-position queue withdrawals exhaust each shared market at most once.
        cash={k:int(h.cash.iloc[0]) for k,h in g.groupby('market')}
        J=0
        for vault in vg.sort_values(['assets','vault'],ascending=[False,True]).vault:
            for x in g[g.vault.eq(vault)].sort_values('rank').itertuples():
                take=min(int(x.position),cash[x.market]);cash[x.market]-=take;J+=take
        assets=sum(int(x) for x in vg.assets)
        positive=g[g.position.gt(0)]
        util=float((positive.position*(positive.borrow/positive.supply)).sum()/positive.position.sum())
        daily.append(dict(date=date,block=int(vg.block.iloc[0]),timestamp=int(vg.timestamp.iloc[0]),S=S,J=J,assets=assets,Dup=(S-J)/S,JA=J/assets,Util=util))
        for f in [5,10,25]:
            req=[int(a)*f//100 for a in vg.assets]; passed=all(r<=int(c) for r,c in zip(req,vg.capacity)); total=sum(req)
            requests.append(dict(date=date,f=f,all_pass=passed,excluded=passed and total>J,request=total,J=J,gap=max(total-J,0)))
    daily=pd.DataFrame(daily);requests=pd.DataFrame(requests)
    daily.to_csv(O/'daily.csv',index=False);requests.to_csv(O/'joint_requests.csv',index=False)
    f25=requests[requests.f.eq(25)];passes=int(f25.all_pass.sum());excluded=int(f25.excluded.sum())
    med=100*daily.Dup.median();rate=100*excluded/passes
    checks.update(days=len(daily),table1_median_Dup_pct=med,table5_passes=passes,table5_excluded=excluded,table5_excluded_pct=rate)
    checks['reference_gate']=round(med,2)==57.86 and passes==81 and excluded==62 and round(rate,2)==76.54
    inventory.extend([dict(path=str(opath),rows=len(d),role='ordered operation ledger'),dict(path=str(cp),rows=len(c0),role='opening market cash')])
    pd.DataFrame(inventory).to_csv(O/'input_inventory.csv',index=False)
    (O/'gate_results.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2),flush=True)
    assert checks['reference_gate'],'Reference table gate failed; do not start additional estimates.'
    return checks

if __name__=='__main__':run()
