from pathlib import Path
import ast,json
import pandas as pd
from rpc import rpc,A,R
def run():
    z=json.loads((R/'raw/chain_panel/2026-03-30_decoded.json').read_text());start=z['block']+1;end=z['block']+7*43200
    t=ast.parse((R/'code/empirical/collect_chain.py').read_text())
    M=next(ast.literal_eval(n.value) for n in t.body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='M' for x in n.targets))
    sigs=json.loads((R/'data/raw/revision5/event_signatures.json').read_text())
    topics={x['topic']:x['signature'].split('(')[0] for x in sigs if x['signature'].split('(')[0] in ['Supply','Withdraw','Borrow','Repay','Liquidate']}
    mids=json.loads((R/'additional_evidence/panel_evidence/raw/operation_query.json').read_text())['markets']
    rows=[];lo=start;step=2000
    while lo<=end:
        hi=min(lo+step-1,end)
        try: logs=rpc(8453,'eth_getLogs',[{'address':M,'fromBlock':hex(lo),'toBlock':hex(hi),'topics':[list(topics),mids]}])
        except RuntimeError:
            if step>100:step//=2;continue
            raise
        for l in logs:
            kind=topics[l['topics'][0]];data=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)]
            block=int(l['blockNumber'],16);assert l.get('blockTimestamp') is not None,'RPC log timestamp is missing'
            timestamp=int(l['blockTimestamp'],16) if isinstance(l['blockTimestamp'],str) else int(l['blockTimestamp'])
            assert timestamp==z['timestamp']+2*(block-z['block']),'RPC event timestamp differs from the validated block clock'
            if kind in ['Borrow','Withdraw']:amount=data[1];owner='0x'+l['topics'][2][-40:]
            else:amount=data[0];owner='0x'+l['topics'][3][-40:]
            rows.append(dict(tx=l['transactionHash'],log_index=int(l['logIndex'],16),block=block,block_hash=l['blockHash'],timestamp=timestamp,market=l['topics'][1],kind='Liquidation' if kind=='Liquidate' else kind,owner=owner.lower(),assets_micro=amount,bad_debt_micro=data[3] if kind=='Liquidate' else 0))
        lo=hi+1
        if (lo-start)%20000==0:print('tail',lo,end,len(rows),flush=True)
    # Verify the constant timestamp spacing against the archived endpoint at both boundaries.
    for b in [start,end]:
        h=rpc(8453,'eth_getBlockByNumber',[hex(b),False]);assert int(h['timestamp'],16)==z['timestamp']+2*(b-z['block'])
    d=pd.DataFrame(rows).sort_values(['block','log_index']);assert not d.duplicated(['tx','log_index']).any()
    from hourly import batches,sel,state
    old,_,_=state(z)
    # Query all ledger markets at the opening block, including inactive queues.
    opening=batches(8453,[(z['block'],[(M,sel('market(bytes32)')+m[2:]) for m in mids])])[0]
    closing=batches(8453,[(end,[(M,sel('market(bytes32)')+m[2:]) for m in mids])])[0]
    signed=d.assets_micro.where(d.kind.isin(['Supply','Repay','Liquidation']),-d.assets_micro)
    delta=signed.groupby(d.market).sum();checks=[]
    for m,a,b in zip(mids,opening,closing):
        before=a[0]-a[2];after=b[0]-b[2];gap=before+int(delta.get(m,0))-after
        checks.append(dict(market=m,opening=before,net_flow=int(delta.get(m,0)),closing=after,gap=gap))
    pd.DataFrame(checks).to_csv(A/'out/tail_cash_reconciliation.csv',index=False)
    assert max(abs(c['gap']) for c in checks)<=1,'Tail market cash reconciliation failed'
    d.to_parquet(A/'out/tail_operations.parquet',index=False)
    (A/'out/tail_coverage.json').write_text(json.dumps({'start':start,'end':end,'rows':len(d),'complete':True,'timestamp_source':'eth_getLogs blockTimestamp for every event; exact block-clock check','max_cash_gap_micro':max(abs(c['gap']) for c in checks)},indent=2))
    print('tail complete',len(d),flush=True)
if __name__=='__main__':run()
