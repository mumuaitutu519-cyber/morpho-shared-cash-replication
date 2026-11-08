"""Historical native-USDC vault calls; same economic and trace exclusions as Table 11."""
import json
import pandas as pd
from hourly import blocks,cohort,sel,word,batches,M
from rpc import rpc,A
O=A/'out'
WITH=sel('withdraw(uint256,address,address)');REDEEM=sel('redeem(uint256,address,address)')
LIQ=sel('NotEnoughLiquidity()');MOUT=sel('withdraw(bytes32,address,address,address,uint256,uint256)')
def reason(s):
    if s.startswith('0x08c379a0'):
        try:
            b=bytes.fromhex(s[10:]);off=int.from_bytes(b[:32],'big');n=int.from_bytes(b[off:off+32],'big');return b[off+32:off+32+n].decode(errors='replace')
        except Exception:return ''
    return 'NotEnoughLiquidity()' if s[:10]==LIQ else s[:10]
def flatten(z,path=()):
    yield path,z
    for i,c in enumerate(z.get('calls',[])):yield from flatten(c,path+(i,))
def run():
    ts=list(pd.date_range('2025-09-09','2025-11-22',freq='D',tz='UTC'))+[pd.Timestamp('2026-03-31',tz='UTC')]
    br=blocks(1,ts);vs=cohort(1,int(pd.Timestamp('2025-11-22',tz='UTC').timestamp())-1);addresses=[v['address'].lower() for v in vs]
    first=br[0]['next_boundary_block'];last=br[-2]['next_boundary_block']-1;observed_end=br[-1]['next_boundary_block']-1
    traces=[];cert=[]
    for count,lo in enumerate(range(first,last+1,2000)):
        hi=min(last,lo+1999);after=0
        while True:
            vals=rpc(1,'trace_filter',[{'fromBlock':hex(lo),'toBlock':hex(hi),'toAddress':addresses,'after':after,'count':1000}]);traces+=vals;after+=len(vals)
            if len(vals)<1000:break
        cert.append(dict(from_block=lo,to_block=hi,traces=after,complete=True))
        if count%20==0:print('trace chunks',count+1,'of',(last-first)//2000+1,flush=True)
    pd.DataFrame(cert).to_csv(O/'A4_ethereum_trace_coverage.csv',index=False)
    candidates=[]
    for t in traces:
        a=t.get('action',{});data=a.get('input','');to=a.get('to','').lower()
        if to not in addresses or data[:10] not in [WITH,REDEEM] or not t.get('error'):continue
        tx=t['transactionHash'];tree=rpc(1,'debug_traceTransaction',[tx,{'tracer':'callTracer','timeout':'20s'}]);path=tuple(t['traceAddress']);walk=dict(flatten(tree));node=walk.get(path)
        assert node is not None and node.get('to','').lower()==to and node.get('input')==data
        output=node.get('output','');rr=reason(output)
        if rr!='NotEnoughLiquidity()' and 'insufficient liquidity' not in rr.lower():continue
        subtree=[z for p,z in walk.items() if len(p)>len(path) and p[:len(path)]==path and z.get('error')]
        if any('gas' in z.get('error','').lower() or 'oog' in z.get('error','').lower() for z in subtree):continue
        if any(z.get('to','').lower()==M and z.get('input','')[:10]==sel('withdraw((address,address,address,address,uint256),uint256,uint256,address,address)') and 'insufficient liquidity' not in reason(z.get('output','')).lower() for z in subtree):continue
        if node.get('type','').upper()=='STATICCALL':continue
        if node.get('type','').upper() in ['DELEGATECALL','CALLCODE'] and node.get('from','').lower()!=to:continue
        words=[int(data[i:i+64],16) for i in range(10,len(data),64)];assert len(words)==3
        block=t['blockNumber'];block=int(block,16) if isinstance(block,str) else block
        header=rpc(1,'eth_getBlockByNumber',[hex(block),False]);stamp=int(header['timestamp'],16);owner='0x'+word(words[2])[-40:]
        answer=batches(1,[(block-1,[(to,sel('balanceOf(address)')+owner[2:].zfill(64))])])[0][0];assert answer is not None
        shares=answer[0];calls=[(to,sel('convertToAssets(uint256)')+word(shares))]
        if data[:10]==REDEEM:calls.append((to,sel('previewRedeem(uint256)')+word(words[0])))
        answer=batches(1,[(block-1,calls)])[0];assert all(x is not None for x in answer)
        claim=answer[0][0];amount=words[0] if data[:10]==WITH else answer[1][0]
        candidates.append(dict(vault=to,owner=owner,tx=tx,block=block,timestamp=stamp,date=pd.Timestamp(stamp,unit='s',tz='UTC').strftime('%Y-%m-%d'),txindex=t.get('transactionPosition',0),trace_address=json.dumps(list(path)),claim=claim,request=amount,kept=(claim>=100_000_000 and 100*amount<=101*claim),strict_kept=(claim>=100_000_000 and amount<=claim)))
    pd.DataFrame(candidates).to_csv(O/'A4_ethereum_call_audit.csv',index=False)
    retained=[]
    if candidates:
        d=pd.DataFrame(candidates);d['utc_hour']=pd.to_datetime(d.timestamp,unit='s',utc=True).dt.floor('h').astype(str);d=d.sort_values(['block','txindex','trace_address'])
        for scope,flag in [('Table11','kept'),('strict_claim','strict_kept')]:
            for key,g in d[d[flag]].groupby(['owner','vault','utc_hour']):
                r=g.iloc[0].to_dict();lo=r['block'];success=[]
                for start in range(lo,observed_end+1,50000):
                    hi=min(start+49999,observed_end)
                    # Committed ERC-4626 withdrawals, with owner indexed in topic 3.
                    topic='0x'+__import__('Crypto.Hash.keccak',fromlist=['new']).new(data=b'Withdraw(address,address,address,uint256,uint256)',digest_bits=256).hexdigest()
                    logs=rpc(1,'eth_getLogs',[{'address':r['vault'],'fromBlock':hex(start),'toBlock':hex(hi),'topics':[topic,None,None,'0x'+r['owner'][2:].zfill(64)]}])
                    success=[l for l in logs if int(l['blockNumber'],16)>r['block'] or (int(l['blockNumber'],16)==r['block'] and int(l['transactionIndex'],16)>r['txindex'])]
                    if success:break
                if success:
                    l=min(success,key=lambda z:(int(z['blockNumber'],16),int(z['logIndex'],16)));h=rpc(1,'eth_getBlockByNumber',[l['blockNumber'],False]);wait=(int(h['timestamp'],16)-r['timestamp'])/3600
                else:wait=None
                retained.append({**r,'filter':scope,'calls_in_event':len(g),'resolved':bool(success),'wait_hours':wait})
    ev=pd.DataFrame(retained);ev.to_csv(O/'A4_ethereum_events.csv',index=False);out=[]
    periods=pd.read_csv(O/'periods.csv')
    for r in periods.itertuples():
        for scope in ['Table11','strict_claim']:
            x=ev[ev['filter'].eq(scope)&ev.date.between(r.start,r.end)] if len(ev) else ev
            if r.exclude_other_window and len(x):x=x[~x.date.between('2025-10-09','2025-10-17')]
            done=x[x.resolved] if len(x) else x
            out.append(dict(chain='Ethereum',period=r.period,filter=scope,events=len(x),holders=x.owner.nunique() if len(x) else 0,request_median=x.request.median()/1e6 if len(x) else None,completed_share=len(done)/len(x) if len(x) else None,wait_median_hours=done.wait_hours.median() if len(done) else None))
    pd.DataFrame(out).to_csv(O/'A4_ethereum.csv',index=False);print('Ethereum calls complete',len(traces),len(candidates),len(ev),flush=True)
if __name__=='__main__':
    try:run()
    except Exception as e:
        (O/'A4_ethereum_failure.json').write_text(json.dumps({'error':str(e)},indent=2));raise
