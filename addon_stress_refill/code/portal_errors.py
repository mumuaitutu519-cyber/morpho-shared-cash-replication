"""Extend the original Table 11 public trace scan, with exact owner reads."""
import json,time,gzip,hashlib,urllib.request,urllib.error,concurrent.futures,sys
import pandas as pd
from hourly import A,R,cohort,blocks,sel,batches,word,morpho
from rpc import rpc,multi
from ethereum_errors import reason
O=A/'out';P=O/'portal_raw';P.mkdir(exist_ok=True)
WITH=sel('withdraw(uint256,address,address)');REDEEM=sel('redeem(uint256,address,address)')
source=json.loads((R/'real_consequences/raw/query.json').read_text())
WITH_TOPIC=next(x for x in source['logs'][0]['topic0'] if x.startswith('0xfbde797d'))
MOUT=sel('withdraw((address,address,address,address,uint256),uint256,uint256,address,address)')
URL={1:'https://portal.sqd.dev/datasets/ethereum-mainnet/stream',42161:'https://portal.sqd.dev/datasets/arbitrum-one/stream'}
PORTAL_DELAY={1:1.,42161:1.}
def followup_logs(chain,start,end,vault,owner):
    """Owner-indexed committed logs after the complete initial call scan."""
    lo=start;step=end-start+1;found=[];coverage=[]
    while lo<=end:
        hi=min(end,lo+step-1);query={'address':vault,'fromBlock':hex(lo),'toBlock':hex(hi),'topics':[WITH_TOPIC,None,None,'0x'+owner[2:].zfill(64)]}
        try:logs=rpc(chain,'eth_getLogs',[query],attempts=1)
        except RuntimeError:
            if step<=1000:raise
            step=max(1000,step//2);continue
        coverage.append(dict(chain=chain,vault=vault,owner=owner,from_block=lo,to_block=hi,logs=len(logs)))
        for log in logs:
            assert log['address'].lower()==vault and log['topics'][0]==WITH_TOPIC and ('0x'+log['topics'][3][-40:]).lower()==owner and not log.get('removed',False)
            found.append(dict(block=int(log['blockNumber'],16),txindex=int(log['transactionIndex'],16),log_index=int(log['logIndex'],16),tx=log['transactionHash']))
        if found:break
        lo=hi+1
    if found:
        first=min(found,key=lambda s:(s['block'],s['txindex'],s['log_index']));header=rpc(chain,'eth_getBlockByNumber',[hex(first['block']),False]);first['timestamp']=int(header['timestamp'],16);found=[first]
    return found,coverage
def post(chain,q):
    key=hashlib.sha256(json.dumps([chain,q],sort_keys=True).encode()).hexdigest();p=P/(key+'.json.gz')
    if p.exists():return json.load(gzip.open(p,'rt'))['rows']
    errorfile=P/(key+'.errors.json')
    errs=json.loads(errorfile.read_text()).get('attempts',[]) if errorfile.exists() else []
    for attempt in range(5):
        try:
            time.sleep(PORTAL_DELAY[chain]+attempt);req=urllib.request.Request(URL[chain],json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0','Accept-Encoding':'gzip'})
            with urllib.request.urlopen(req,timeout=45) as f:
                b=f.read();b=gzip.decompress(b) if f.headers.get('Content-Encoding')=='gzip' else b
            rows=[json.loads(l) for l in b.splitlines() if l];assert rows
            with gzip.open(p,'wt') as f:json.dump({'url':URL[chain],'chain':chain,'request':q,'rows':rows},f)
            return rows
        except Exception as e:
            body=e.read().decode(errors='replace') if isinstance(e,urllib.error.HTTPError) else None
            errs.append({'attempt':len(errs)+1,'error':str(e),'body':body,'utc':pd.Timestamp.now(tz='UTC').isoformat()});errorfile.write_text(json.dumps({'chain':chain,'url':URL[chain],'request':q,'attempts':errs},indent=2))
            if isinstance(e,urllib.error.HTTPError) and e.code in [429,529]:
                PORTAL_DELAY[chain]=max(4.,PORTAL_DELAY[chain]);(O/'portal_pacing.json').write_text(json.dumps(PORTAL_DELAY,indent=2))
            time.sleep(min(45,5*2**attempt))
    raise RuntimeError(f'Portal read failed: {key}')
def scan(chain,start,end,addresses,owners=None,with_traces=True,stop_after=None):
    fields=source['fields'];q={'type':'evm','fields':fields,'logs':[{'address':addresses,'topic0':[WITH_TOPIC],'transaction':True}]}
    if owners:q['logs'][0]['topic3']=['0x'+o[2:].zfill(64) for o in owners]
    if with_traces:q['traces']=[{'type':['call'],'callTo':addresses,'callSighash':[WITH,REDEEM],'transaction':True}]
    cur=start;out=[];cert=[]
    while cur<=end:
        cap=min(end,cur+(20000 if chain==1 else 50000)-1);selected=None;full=False
        for original_cap in [end,min(end,cur+(2000 if chain==1 else 100000)-1),min(end,cur+(20000 if chain==1 else 500000)-1),cap]:
            for subtree in ([False,True] if with_traces else [False]):
                probe=json.loads(json.dumps(q));probe.update(fromBlock=cur,toBlock=original_cap)
                if subtree:probe['traces'][0].update(parents=True,subtraces=True)
                key=hashlib.sha256(json.dumps([chain,probe],sort_keys=True).encode()).hexdigest()
                if (P/(key+'.json.gz')).exists():selected=probe;full=subtree;break
            if selected is not None:break
        if selected is None:selected={**q,'fromBlock':cur,'toBlock':cap}
        page=post(chain,selected);last=page[-1]['header']['number'];assert cur<=last<=end
        for b in page:b['_full_subtraces']=full
        out+=page;cert.append(dict(chain=chain,from_block=cur,requested_to=selected['toBlock'],last_block=last,blocks=len(page),traces=sum(len(b.get('traces',[])) for b in page),logs=sum(len(b.get('logs',[])) for b in page),full_subtraces=full));cur=last+1
        print('portal',chain,cur,end,len(out),flush=True)
        if stop_after is not None and any((b['header']['number'],l['transactionIndex'])>stop_after for b in page for l in b.get('logs',[])):break
    return out,cert

def run(chain):
    ts=list(pd.date_range('2025-09-09','2025-11-22',freq='D',tz='UTC'))+[pd.Timestamp('2026-03-31',tz='UTC')];br=blocks(chain,ts);first=br[0]['next_boundary_block'];end=br[-2]['next_boundary_block']-1;observed_end=br[-1]['next_boundary_block']-1
    vs=cohort(chain,int(pd.Timestamp('2025-11-22',tz='UTC').timestamp())-1);addresses=[v['address'].lower() for v in vs];page,cert=scan(chain,first,end,addresses);pd.DataFrame(cert).to_csv(O/f'A4_portal_coverage_{chain}.csv',index=False)
    candidates=[];success=[];known=set();logkeys=set();rawcallrows=[]
    for block in page:
        h=block['header'];b=h['number'];stamp=h['timestamp'];txs={t['transactionIndex']:t for t in block.get('transactions',[])};traces=block.get('traces',[])
        def committed(t):
            path=t['traceAddress'];return not t.get('error') and txs[t['transactionIndex']].get('status',1)==1 and all(not a.get('error') for a in traces if a['transactionIndex']==t['transactionIndex'] and len(a['traceAddress'])<len(path) and path[:len(a['traceAddress'])]==a['traceAddress'])
        for l in block.get('logs',[]):
            if l['topics'][0]!=WITH_TOPIC:continue
            ltx=txs[l['transactionIndex']]['hash'];logkeys.add((ltx,l['address'].lower()));w=[int(l['data'][i:i+64],16) for i in range(2,len(l['data']),64)];success.append(dict(vault=l['address'].lower(),owner='0x'+l['topics'][3][-40:],block=b,txindex=l['transactionIndex'],log_index=l['logIndex'],tx=ltx,timestamp=stamp,amount=w[0]))
        for t in traces:
            a=t.get('action',{});to=a.get('to','').lower();data=a.get('input','')
            if to not in addresses or data[:10] not in [WITH,REDEEM]:continue
            tx=txs[t['transactionIndex']]['hash'];path=t['traceAddress']
            if len(data)<202:continue
            words=[int(data[i:i+64],16) for i in range(10,202,64)]
            known.add((tx,to));owner='0x'+word(words[2])[-40:];rr=reason((t.get('result') or {}).get('output') or '')
            committed_status=committed(t) if block.get('_full_subtraces') else (False if t.get('error') or txs[t['transactionIndex']].get('status',1)!=1 else None)
            rawcallrows.append(dict(chain=chain,block=b,tx=tx,txindex=t['transactionIndex'],trace_address=json.dumps(path),vault=to,owner=owner,method=data[:10],error=t.get('error'),reason=rr,committed=committed_status))
            if not t.get('error') or (rr!='NotEnoughLiquidity()' and 'insufficient liquidity' not in rr.lower()):continue
            detailed=traces
            if not block.get('_full_subtraces'):
                q={'type':'evm','fields':source['fields'],'fromBlock':b,'toBlock':b,'traces':[{'type':['call'],'callTo':[to],'callSighash':[WITH,REDEEM],'transaction':True,'parents':True,'subtraces':True}]}
                detailed=[x for packet in post(chain,q) for x in packet.get('traces',[])]
            sub=[x for x in detailed if x['transactionIndex']==t['transactionIndex'] and len(x['traceAddress'])>len(path) and x['traceAddress'][:len(path)]==path and x.get('error')]
            if any('gas' in x.get('error','').lower() or 'oog' in x.get('error','').lower() for x in sub):continue
            if any(x.get('action',{}).get('to','').lower()==morpho(chain) and x.get('action',{}).get('input','')[:10]==MOUT and 'insufficient liquidity' not in reason((x.get('result') or {}).get('output') or '').lower() for x in sub):continue
            if a.get('callType')=='staticcall':continue
            if a.get('callType') in ['delegatecall','callcode'] and a.get('from')!=to:continue
            same_tx_success=False
            if txs[t['transactionIndex']].get('status')==1:
                for s in detailed:
                    sa=s.get('action',{});si=sa.get('input','');sp=s['traceAddress']
                    if s['transactionIndex']!=t['transactionIndex'] or tuple(sp)<=tuple(path) or s.get('error') or sa.get('to','').lower()!=to or si[:10] not in [WITH,REDEEM] or len(si)<202:continue
                    if ('0x'+si[162:202]).lower()!=owner:continue
                    if all(not parent.get('error') for parent in detailed if parent['transactionIndex']==s['transactionIndex'] and len(parent['traceAddress'])<len(sp) and sp[:len(parent['traceAddress'])]==parent['traceAddress']):same_tx_success=True;break
            candidates.append(dict(chain=chain,vault=to,owner=owner,tx=tx,block=b,timestamp=stamp,date=pd.Timestamp(stamp,unit='s',tz='UTC').strftime('%Y-%m-%d'),txindex=t['transactionIndex'],trace_address=json.dumps(path),method=data[:10],amount_raw=words[0],same_tx_success=same_tx_success))
    pd.DataFrame(rawcallrows).to_parquet(O/f'A4_calls_{chain}.parquet',index=False)
    missing=logkeys-known;(O/f'A4_trace_log_check_{chain}.json').write_text(json.dumps({'withdraw_log_transactions':len(logkeys),'withdraw_call_transactions':len(known),'logs_without_calls':len(missing),'examples':list(missing)[:20]},indent=2));assert not missing,'Portal call coverage fails committed withdrawal log crosscheck'
    pd.DataFrame(candidates).to_csv(O/f'A4_liquidity_candidates_{chain}.csv',index=False)
    print('A4 candidates',chain,len(candidates),flush=True)
    audit=[]
    for index,r in enumerate(candidates):
        v=r['vault'];owner=r['owner'];pre=r['block']-1;val=batches(chain,[(pre,[(v,sel('balanceOf(address)')+owner[2:].zfill(64))])])[0][0]
        if not val:
            assert rpc(chain,'eth_getCode',[v,hex(pre)])=='0x','Holder equity read failed for an existing contract'
            audit.append({**r,'claim':0,'request':r['amount_raw'] if r['method']==WITH else None,'Table11':False,'strict_claim':False,'equity_status':'Vault not yet deployed at the preceding block'});continue
        calls=[(v,sel('convertToAssets(uint256)')+word(val[0]))]
        if r['method']==REDEEM:calls.append((v,sel('previewRedeem(uint256)')+word(r['amount_raw'])))
        vals=batches(chain,[(pre,calls)])[0];assert all(v is not None for v in vals);claim=vals[0][0];amount=r['amount_raw'] if r['method']==WITH else vals[1][0]
        audit.append({**r,'claim':claim,'request':amount,'Table11':claim>=100_000_000 and 100*amount<=101*claim,'strict_claim':claim>=100_000_000 and amount<=claim})
        if index%25==0:print('A4 equity reads',chain,index+1,len(candidates),flush=True)
    audit_columns=['chain','vault','owner','tx','block','timestamp','date','txindex','trace_address','method','amount_raw','same_tx_success','claim','request','Table11','strict_claim','equity_status']
    pd.DataFrame(audit,columns=audit_columns).to_csv(O/f'A4_call_audit_{chain}.csv',index=False);events=[];followup_coverage=[]
    if audit:
        d=pd.DataFrame(audit);d['utc_hour']=pd.to_datetime(d.timestamp,unit='s',utc=True).dt.floor('h').astype(str);d['_path']=d.trace_address.map(lambda s:tuple(json.loads(s)));d=d.sort_values(['block','txindex','_path'])
        for scope in ['Table11','strict_claim']:
            for key,g in d[d[scope]].groupby(['owner','vault','utc_hour']):
                r=g.iloc[0].drop(labels='_path').to_dict();ss=[s for s in success if s['vault']==r['vault'] and s['owner']==r['owner'] and (s['block'],s['txindex'])>(r['block'],r['txindex'])]
                if r['same_tx_success']:ss=[dict(block=r['block'],txindex=r['txindex'],log_index=-1,timestamp=r['timestamp'],tx=r['tx'])]
                if not ss:
                    ss,coverage=followup_logs(chain,end+1,observed_end,r['vault'],r['owner']);followup_coverage+=coverage
                nxt=min(ss,key=lambda s:(s['block'],s['txindex'],s['log_index'])) if ss else None;events.append({**r,'filter':scope,'calls_in_event':len(g),'resolved':nxt is not None,'wait_hours':(nxt['timestamp']-r['timestamp'])/3600 if nxt else None,'next_success_tx':nxt['tx'] if nxt else None})
    pd.DataFrame(followup_coverage,columns=['chain','vault','owner','from_block','to_block','logs']).drop_duplicates().to_csv(O/f'A4_followup_rpc_coverage_{chain}.csv',index=False)
    ev=pd.DataFrame(events,columns=audit_columns+['utc_hour','filter','calls_in_event','resolved','wait_hours','next_success_tx']);ev.to_csv(O/f'A4_events_{chain}.csv',index=False);summaries=[]
    for r in pd.read_csv(O/'periods.csv').itertuples():
        for scope in ['Table11','strict_claim']:
            x=ev[ev['filter'].eq(scope)&ev.date.between(r.start,r.end)] if len(ev) else ev
            if r.exclude_other_window and len(x):x=x[~x.date.between('2025-10-09','2025-10-17')]
            done=x[x.resolved] if len(x) else x;summaries.append(dict(chain={1:'Ethereum',42161:'Arbitrum'}[chain],period=r.period,filter=scope,events=len(x),holders=x.owner.nunique() if len(x) else 0,request_median=x.request.median()/1e6 if len(x) else None,completed_share=len(done)/len(x) if len(x) else None,wait_median_hours=done.wait_hours.median() if len(done) else None))
    pd.DataFrame(summaries).to_csv(O/f'A4_summary_{chain}.csv',index=False)
    failure=O/f'A4_portal_failure_{chain}.json'
    if failure.exists():failure.rename(O/f'A4_portal_recovered_failure_{chain}.json')
    print('A4 complete',chain,len(rawcallrows),len(audit),len(events),flush=True)
def retry_network(chain):
    while True:
        try:return run(chain)
        except RuntimeError as error:
            (O/f'A4_portal_failure_{chain}.json').write_text(json.dumps({'error':str(error),'utc':pd.Timestamp.now(tz='UTC').isoformat()},indent=2))
            if not str(error).startswith('Portal read failed:'):raise
            print('Portal overloaded; retained cache and waiting before retry',chain,flush=True);time.sleep(45)
if __name__=='__main__':
    selected_chains=[int(sys.argv[1])] if len(sys.argv)>1 else [1,42161]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fs={pool.submit(retry_network,c):c for c in selected_chains}
        for f in concurrent.futures.as_completed(fs):
            try:f.result()
            except Exception as e:(O/f'A4_portal_failure_{fs[f]}.json').write_text(json.dumps({'error':str(e)},indent=2));raise
