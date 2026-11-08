from pathlib import Path
import json,datetime,requests,concurrent.futures,sys,time
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
from Crypto.Hash import keccak
def selector(signature):
 k=keccak.new(digest_bits=256);k.update(signature.encode());return '0x'+k.hexdigest()[:8]
O=ROOT/'outputs';R=ROOT/'raw'/'history_audit';R.mkdir(exist_ok=True);old=ROOT/'raw/inherited';V=json.loads((old/'selected_vaults.json').read_text());r=pd.read_parquet(old/'shared_positions.parquet');r=r[r.date.le('2025-11-30')];markets=sorted(r.market.unique()); dates=sorted(r.date.unique());blocks=pd.read_csv(old/'withdrawal_capacity.csv').set_index('date');hist={};names={};pvals={}
for vi,v in enumerate(V):
 h=json.loads((old/('history_'+v['address'].lower()+'.json')).read_text())['response']['data']['vaultByAddress']['historicalState']
 for a in h['allocation']:
  m=a['market']['marketId'].lower()
  assert a['market']['loanAsset']['address'].lower() == '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
  if m not in markets:continue
  names[m]=(a['market'].get('collateralAsset') or {}).get('symbol','Idle')+'/USDC'
  for z in a['supplyAssets']:
   if z['y'] is not None:pvals[vi,m,int(z['x'])]=int(z['y'])
  hs=a['market']['historicalState'];bs={z['x']:z['y'] for z in hs['borrowAssets']}
  for z in hs['supplyAssets']:
   if z['y'] is not None and bs.get(z['x']) is not None:
    key=m,int(z['x']);value=int(z['y']),int(bs[z['x']]);assert key not in hist or hist[key]==value;hist[key]=value
M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';MC='0xca11bde05977b3631167028862be2a173976ca11';word=lambda x:f'{x:064x}'
def encode(calls):
 chunks=[]
 for data in calls:
  b=data[2:];chunks.append(M[2:].zfill(64)+word(1)+word(96)+word(len(b)//2)+b.ljust((len(b)+63)//64*64,'0'))
 offset=32*len(chunks);offsets=[]
 for c in chunks:offsets.append(word(offset));offset+=len(c)//2
 return selector('aggregate3((address,bool,bytes)[])')+word(32)+word(len(chunks))+''.join(offsets)+''.join(chunks)
def decode(raw):
 b=bytes.fromhex(raw[2:]);rd=lambda i:int.from_bytes(b[i:i+32],'big');base=rd(0);n=rd(base);start=base+32;result=[]
 for i in range(n):
  t=start+rd(start+32*i);ok=rd(t);loc=t+rd(t+32);sz=rd(loc);result.append((bool(ok),b[loc+32:loc+32+sz].hex()))
 return result
jobs=[]
for day in dates:
 t=int((pd.Timestamp(day,tz='UTC')+pd.Timedelta(days=1)).timestamp());calls=[];meta=[]
 for m in markets:
  if (m,t) not in hist:calls.append(selector('market(bytes32)')+m[2:]);meta.append({'kind':'market','market':m})
  for vi,v in enumerate(V):
   if (vi,m,t) not in pvals:calls.append(selector('position(bytes32,address)')+m[2:]+v['address'][2:].lower().zfill(64));meta.append({'kind':'position','market':m,'vault_index':vi})
 jobs.append((day,t,calls,meta))
(O/'history_audit_plan.json').write_text(json.dumps({'dates':dates,'markets':markets,'vaults':V,'requested_calls':sum(len(j[2]) for j in jobs),'market_missing':sum(x['kind']=='market' for j in jobs for x in j[3]),'position_missing':sum(x['kind']=='position' for j in jobs for x in j[3])},indent=2))
def run(j):
 day,t,calls,meta=j;cache=R/(day+'.json')
 if cache.exists():return json.loads(cache.read_text())
 body={'jsonrpc':'2.0','id':1,'method':'eth_call','params':[{'to':MC,'data':encode(calls)},hex(int(blocks.loc[day,'block']))]};attempts=[];parsed=None
 for n in (1,2):
  a={'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':n,'url':'https://base.drpc.org','request':body}
  try:
   resp=requests.post(a['url'],json=body,timeout=55);a.update(status=resp.status_code,body=resp.text);data=resp.json();a['response']=data
   if resp.status_code!=200 or 'result' not in data:raise ValueError(str(data.get('error',resp.status_code)))
   parsed=decode(data['result']);assert len(parsed)==len(meta)
  except Exception as e:a['error']=str(e)
  attempts.append(a)
  if parsed is not None:break
  time.sleep(1)
 out={'date':day,'timestamp':t,'block':int(blocks.loc[day,'block']),'calls':meta,'attempts':attempts,'decoded':parsed};cache.write_text(json.dumps(out));return out
if __name__=='__main__':
 done=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
  for a in ex.map(run,jobs):
   done+=1
   if done%20==0:print('audited',done,'of',len(jobs),flush=True)
 print('complete',flush=True)
