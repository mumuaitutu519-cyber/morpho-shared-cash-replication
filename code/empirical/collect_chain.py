"""Archive-only reads of actual contract states. No state overrides or artificial holders."""
from pathlib import Path
import json,datetime,hashlib,time,sys,concurrent.futures
import requests,pandas as pd
from Crypto.Hash import keccak
ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'raw/chain_panel';RAW.mkdir(parents=True,exist_ok=True)
V=json.loads((ROOT/'raw/inherited/selected_vaults.json').read_text());VA=[x['address'].lower() for x in V]
M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';MC='0xca11bde05977b3631167028862be2a173976ca11';ASSET='0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
word=lambda x:f'{int(x):064x}'
def sel(s):return '0x'+keccak.new(data=s.encode(),digest_bits=256).hexdigest()[:8]
def encode(calls):
 chunks=[]
 for to,data in calls:
  b=data[2:];chunks.append(to[2:].zfill(64)+word(1)+word(96)+word(len(b)//2)+b.ljust((len(b)+63)//64*64,'0'))
 off=32*len(chunks);offsets=[]
 for c in chunks:offsets.append(word(off));off+=len(c)//2
 return sel('aggregate3((address,bool,bytes)[])')+word(32)+word(len(chunks))+''.join(offsets)+''.join(chunks)
def decode(raw):
 b=bytes.fromhex(raw[2:]);rd=lambda i:int.from_bytes(b[i:i+32],'big');base=rd(0);n=rd(base);start=base+32;out=[]
 for i in range(n):
  t=start+rd(start+32*i);loc=t+rd(t+32);sz=rd(loc);s=b[loc+32:loc+32+sz];out.append([int.from_bytes(s[j:j+32],'big') for j in range(0,len(s),32)] if rd(t) else None)
 return out

def rpc(name,method,params):
 p=RAW/(name+'.json')
 if p.exists():
  x=json.loads(p.read_text())
  if 'result' in x.get('response',{}):return x['response']['result']
 attempts=[]
 for url in ['https://base.gateway.tenderly.co','https://base.gateway.tenderly.co']:
  q={'jsonrpc':'2.0','id':1,'method':method,'params':params};x={'url':url,'request':q,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  try:
   time.sleep(.45);r=requests.post(url,json=q,timeout=35);z=r.json();x['response']=z;x['http_status']=r.status_code
   if 'result' in z and z['result'] is not None:p.write_text(json.dumps(x));return z['result']
  except Exception as e:x['error']=str(e)
  attempts.append(x);time.sleep(.3)
 p.write_text(json.dumps({'attempts':attempts}));raise RuntimeError(name+': RPC failed')
def batch(name,block,calls):
 if not calls:return []
 out=decode(rpc(name,'eth_call',[{'to':MC,'data':encode(calls),'gas':'0x1c9c380'},hex(block)]));assert len(out)==len(calls);return out

def collect(job,rebuild=False):
 name,block,boundary=job;path=RAW/(name+'_decoded.json')
 if path.exists() and not rebuild:return json.loads(path.read_text())
 head=rpc(name+'_header','eth_getBlockByNumber',[hex(block),False]);stamp=int(head['timestamp'],16)
 if boundary is not None:assert stamp<boundary<=stamp+2,(name,stamp,boundary)
 fns=['totalAssets()','withdrawQueueLength()','lostAssets()','lastTotalAssets()','MORPHO()','asset()']
 calls=[(v,sel(f)) for v in VA for f in fns]+[(ASSET,sel('balanceOf(address)')+M[2:].zfill(64))]
 z=batch(name+'_vaults',block,calls);vs=[];qcalls=[]
 for i,v in enumerate(VA):
  a=z[i*len(fns):(i+1)*len(fns)];assert all(a[j] for j in [0,1,3,4,5]);assert a[4][0]==int(M,16) and a[5][0]==int(ASSET,16)
  vs.append({'address':v,'name':V[i]['name'],'totalAssets':a[0][0],'length':a[1][0],'lostAssets':a[2][0] if a[2] else None,'lastTotalAssets':a[3][0]});qcalls.extend((v,sel('withdrawQueue(uint256)')+word(j)) for j in range(a[1][0]))
 queues=batch(name+'_queues',block,qcalls);idx=0
 for v in vs:
  v['queue']=['0x'+word(x[0]) for x in queues[idx:idx+v['length']]];idx+=v['length'];assert len(v['queue'])==len(set(v['queue']))
 mids=sorted({m for v in vs for m in v['queue']});calls=[]
 for m in mids:calls.extend([(M,sel('market(bytes32)')+m[2:]),(M,sel('idToMarketParams(bytes32)')+m[2:])])
 keys=[]
 for v in vs:
  for m in v['queue']:calls.append((M,sel('position(bytes32,address)')+m[2:]+v['address'][2:].zfill(64)));keys.append((v['address'],m))
 zs=batch(name+'_markets_positions',block,calls);market={};rates=[];rkeys=[]
 for i,m in enumerate(mids):
  state,params=zs[2*i:2*i+2];assert state is not None and params is not None;assert params[0]==int(ASSET,16);market[m]={'state':state,'params':params}
  if params[3]!=0 and state[2]>0 and stamp>state[4]:
   rates.append(('0x'+f'{params[3]:040x}',sel('borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))')+''.join(word(w) for w in params+state)));rkeys.append(m)
 rz=batch(name+'_rates',block,rates)
 for m,r in zip(rkeys,rz):assert r is not None;market[m]['borrowRate']=r[0]
 positions={v['address']:{} for v in vs}
 for (v,m),x in zip(keys,zs[2*len(mids):]):assert x is not None;positions[v][m]=x
 out={'name':name,'block':block,'block_hash':head['hash'],'timestamp':stamp,'vaults':vs,'market':market,'positions':positions,'morpho_token_balance':z[-1][0]}
 path.write_text(json.dumps(out));return out

def jobs():
 out=[]
 for i,d in enumerate(pd.date_range('2025-01-15','2026-03-30')):
  boundary=int((d.tz_localize('UTC')+pd.Timedelta(days=1)).timestamp());out.append((d.strftime('%Y-%m-%d'),25098126+43200*i,boundary))
 for p in sorted((ROOT/'raw').glob('public_liquidity_*.json')):
  x=json.loads(p.read_text());blocks=[int(z['data']['last_indexed_block']) for k,z in x['responses'].items() if k!='graphql' and z.get('data')];out.append(('snapshot_'+x['date_utc'],max(blocks),None))
 out.append(('snapshot_2026-09-08_0437',51026438,None));return out
if __name__=='__main__':
 todo=jobs();todo=todo[:2]+[todo[-1]] if '--probe' in sys.argv else todo;errs=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
  fut={ex.submit(collect,j):j for j in todo}
  for i,f in enumerate(concurrent.futures.as_completed(fut),1):
   try:a=f.result()
   except Exception as e:errs.append({'job':fut[f],'error':str(e)});print('ERROR',errs[-1],flush=True)
   if i%25==0 or i==len(todo):print('COMPLETE',i,'/',len(todo),'errors',len(errs),flush=True)
 (ROOT/'outputs/empirical/collection_status.json').write_text(json.dumps({'requested':len(todo),'errors':errs},indent=2))
 if errs:sys.exit(1)
