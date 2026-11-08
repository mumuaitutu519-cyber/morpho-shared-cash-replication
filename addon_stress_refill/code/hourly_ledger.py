"""Recorded cash flows for reconciliation of hourly Ethereum/Arbitrum states."""
import json,time,concurrent.futures
import pandas as pd
from hourly import H,morpho,R,A
from rpc import rpc
def run(chain):
    contract=morpho(chain)
    while not (H/f'blocks_{chain}.json').exists():
        if (H/f'failure_{chain}.json').exists():raise RuntimeError('hourly block collection unavailable')
        time.sleep(5)
    br=json.loads((H/f'blocks_{chain}.json').read_text());mids=set()
    folder=R/('additional_evidence/cross_chain/raw' if chain==1 else 'additional_evidence/raw')
    for f in folder.glob(f'morpho_{chain}_202*.json'):mids.update(json.loads(f.read_text())['market'])
    for f in H.glob(f'{chain}_*.json'):mids.update(json.loads(f.read_text())['market'])
    sigs=json.loads((R/'data/raw/revision5/event_signatures.json').read_text());topics={s['topic']:s['signature'].split('(')[0] for s in sigs if s['signature'].split('(')[0] in ['Supply','Withdraw','Borrow','Repay','Liquidate']}
    out=A/'out';oldfile=out/f'hourly_ledger_{chain}.parquet';universe=out/f'hourly_ledger_markets_{chain}.json'
    covered=set(json.loads(universe.read_text())) if universe.exists() and oldfile.exists() else set()
    missing=mids-covered
    if not missing:
        print('ledger cache complete',chain,len(covered),flush=True);return
    rows=[];cert=[];step=2000 if chain==1 else 50000
    for prefix in ['2025-10-0','2025-10-1','W2']:
        if prefix=='2025-10-1':continue
        rr=[r for r in br if r['utc']<'2025-10-18'] if prefix!='W2' else [r for r in br if r['utc']>='2025-10-27']
        start=rr[0]['block']+1;end=rr[-1]['block'];lo=start;n=0
        while lo<=end:
            hi=min(lo+step-1,end)
            try:logs=rpc(chain,'eth_getLogs',[{'address':contract,'fromBlock':hex(lo),'toBlock':hex(hi),'topics':[list(topics),sorted(missing)]}],attempts=2)
            except RuntimeError:
                if step>100:step//=2;continue
                raise
            for l in logs:
                kind=topics[l['topics'][0]];data=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];a=data[1] if kind in ['Borrow','Withdraw'] else data[0]
                rows.append(dict(market=l['topics'][1],block=int(l['blockNumber'],16),log_index=int(l['logIndex'],16),tx=l['transactionHash'],kind=kind,assets_micro=a,cash_delta_micro=a if kind in ['Supply','Repay','Liquidate'] else -a))
            cert.append(dict(chain=chain,from_block=lo,to_block=hi,logs=len(logs),complete=True,markets=json.dumps(sorted(missing))));lo=hi+1;n+=1
            if n%20==0:print('ledger',chain,lo,end,len(rows),flush=True)
    frames=([pd.read_parquet(oldfile)] if oldfile.exists() else [])+([pd.DataFrame(rows)] if rows else []);d=pd.concat(frames,ignore_index=True).sort_values(['block','log_index']);assert not d.duplicated(['tx','log_index']).any();d.to_parquet(oldfile,index=False)
    cov=out/f'hourly_ledger_coverage_{chain}.csv';frames=([pd.read_csv(cov)] if cov.exists() else [])+[pd.DataFrame(cert)];pd.concat(frames,ignore_index=True).to_csv(cov,index=False);universe.write_text(json.dumps(sorted(mids|covered)))
    print('ledger complete',chain,len(d),flush=True)
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fs={pool.submit(run,c):c for c in [1,42161]}
        for f in concurrent.futures.as_completed(fs):
            try:f.result()
            except Exception as e:(A/f'out/hourly_ledger_failure_{fs[f]}.json').write_text(json.dumps({'error':str(e)}));raise
