from pathlib import Path
import pandas as pd,numpy as np,json,requests,time,datetime
from revision24_rpc import selector,encode_bytes_array,decode_bytes_array
R=Path(__file__).resolve().parents[1];O=R/'reports/revision29';RAW=O/'raw';RAW.mkdir(exist_ok=True);V='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a';S='0x2917956eff0b5eaf030abdb4ef4296df775009ca';E='0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c'
q=pd.read_csv(O/'treasury_transaction_links.csv');q=q[q.deposit_exceeds_opening_cash].sort_values('block');m=pd.read_parquet(O/'market_cash_sequence.parquet');v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v.date=pd.to_datetime(v.date);rows=[]
def call(key,block,calls):
 body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':V,'data':selector('multicall(bytes[])')+encode_bytes_array(calls)},hex(block)]};p=RAW/(key+'.json')
 if p.exists():obj=json.loads(p.read_text());assert obj['request']==body
 else:
  for attempt in range(3):
   time.sleep(1.3+attempt*3);r=requests.post('https://base.drpc.org',json=body,timeout=45);obj={'url':'https://base.drpc.org','request':body,'response':r.json(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};p.write_text(json.dumps(obj,indent=2))
   if 'result' in obj['response']:break
   if attempt<2:p.rename(p.with_suffix(f'.attempt{attempt}.json'))
 assert 'result' in obj['response'],obj['response'];return [int(x,16) for x in decode_bytes_array(obj['response']['result'],len(calls))]
for r in q.itertuples():
 top=v[v.date.eq(r.date)&~v.spark].nlargest(5,'prior_claim_usdc').owner.tolist();owners=list(dict.fromkeys([S,E]+top));block=int(r.block);bm=m[m.block.eq(block)];other_delta=int(bm.loc[bm.tx.ne(r.tx),'cash_delta_raw'].sum())
 for phase,b in [('before',block-1),('after',block)]:
  cs=[]
  for a in owners:cs += [selector('balanceOf(address)')+a[2:].zfill(64),selector('maxWithdraw(address)')+a[2:].zfill(64)]
  vals=call(f'{block}_{phase}_views',b,cs);shares=vals[::2];capacity=vals[1::2];claims=call(f'{block}_{phase}_claims',b,[selector('convertToAssets(uint256)')+hex(n)[2:].zfill(64) for n in shares])
  for a,sh,w,c in zip(owners,shares,capacity,claims):rows.append({'date':r.date,'tx':r.tx,'deposit_block':block,'phase':phase,'state_block':b,'owner':a,'named_identity':'Spark' if a==S else 'Ethena' if a==E else 'unidentified top opening position','shares_raw':str(sh),'claim_micro':str(c),'capacity_micro':str(w),'deposit_micro':str(int(r.treasury_Deposit)),'other_market_cash_change_in_block_micro':str(other_delta),'other_market_events_in_block':int(bm.tx.ne(r.tx).sum())})
 print('completed block',block,'owners',len(owners),flush=True)
pd.DataFrame(rows).to_csv(O/'holder_before_after_states.csv',index=False)
