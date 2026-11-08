from pathlib import Path
import sys,json,time,urllib.request,datetime,hashlib
A=Path(__file__).resolve().parents[1];sys.path.insert(0,str(A/'.deps'))
from Crypto.Hash import keccak
word=lambda x:f'{int(x):064x}'
addr=lambda x:'0x'+f'{int(x):040x}'
def sel(s):return '0x'+keccak.new(data=s.encode(),digest_bits=256).hexdigest()[:8]
def signature(s):return '0x'+keccak.new(data=s.encode(),digest_bits=256).hexdigest()
URLS={1:['https://ethereum-rpc.publicnode.com','https://mainnet.gateway.tenderly.co','https://eth.drpc.org'],42161:['https://arbitrum-one-rpc.publicnode.com','https://arbitrum.gateway.tenderly.co','https://arb1.arbitrum.io/rpc'],137:['https://polygon-bor-rpc.publicnode.com','https://polygon.gateway.tenderly.co','https://polygon.drpc.org'],8453:['https://base.gateway.tenderly.co']}
MC='0xca11bde05977b3631167028862be2a173976ca11'
def fetch(url,name):
 p=A/'raw/sources'/name;p.parent.mkdir(exist_ok=True)
 if p.exists():return p.read_text()
 req=urllib.request.Request(url,headers={'User-Agent':'research/1.0'})
 with urllib.request.urlopen(req,timeout=35) as r:b=r.read()
 p.write_bytes(b);(p.with_suffix(p.suffix+'.url')).write_text(url);return b.decode()
def rpc(chain,method,params):
 q={'jsonrpc':'2.0','id':1,'method':method,'params':params};key=hashlib.sha256(json.dumps(q,sort_keys=True).encode()).hexdigest();folder=A/'raw/rpc'/str(chain);folder.mkdir(parents=True,exist_ok=True);p=folder/(key+'.json')
 if p.exists():return json.loads(p.read_text())['response']['result']
 errors=[]
 for url in URLS[chain]:
  try:
   req=urllib.request.Request(url,json.dumps(q).encode(),headers={'Content-Type':'application/json','User-Agent':'research/1.0'})
   with urllib.request.urlopen(req,timeout=25) as r:z=json.loads(r.read())
   if 'result' not in z or z['result'] is None:raise ValueError(z)
   p.write_text(json.dumps({'url':url,'request':q,'response':z,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}));return z['result']
  except Exception as e:errors.append({'url':url,'error':str(e)})
 (folder/(key+'.error.json')).write_text(json.dumps({'request':q,'errors':errors},indent=2));raise RuntimeError(errors)
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

def batch(chain,block,calls):
 out=[]
 for start in range(0,len(calls),80):
  chunk=calls[start:start+80];z=decode(rpc(chain,'eth_call',[{'to':MC,'data':encode(chunk),'gas':'0x1c9c380'},hex(block)]));assert len(z)==len(chunk);out+=z
 return out

def block_at(chain,boundary):
 p=A/'raw'/f'block_{chain}_{boundary}.json'
 if p.exists():return json.loads(p.read_text())
 hihead=rpc(chain,'eth_getBlockByNumber',['finalized',False]);hi=int(hihead['number'],16);hit=int(hihead['timestamp'],16);assert hit>=boundary,(chain,hi,hit,boundary)
 lo=1;lot=int(rpc(chain,'eth_getBlockByNumber',['0x1',False])['timestamp'],16)
 while hi-lo>1:
  ratio=(boundary-lot)/(hit-lot);mid=max(lo+1,min(hi-1,lo+int((hi-lo)*ratio)))
  h=rpc(chain,'eth_getBlockByNumber',[hex(mid),False]);t=int(h['timestamp'],16)
  if t<boundary:lo=mid;lot=t
  else:hi=mid;hit=t
 h=rpc(chain,'eth_getBlockByNumber',[hex(lo),False]);n=rpc(chain,'eth_getBlockByNumber',[hex(hi),False]);assert int(h['timestamp'],16)<boundary<=int(n['timestamp'],16)
 out={'chain':chain,'block':lo,'hash':h['hash'],'timestamp':int(h['timestamp'],16),'boundary':boundary,'next_block':hi,'next_timestamp':int(n['timestamp'],16),'finalized_head':int(hihead['number'],16)};p.write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':
 import concurrent.futures
 def probe(c):
  try:return c,block_at(c,1790726400)
  except Exception as e:return c,str(e)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
  for v in ex.map(probe,[1,42161,137]):print(v,flush=True)
