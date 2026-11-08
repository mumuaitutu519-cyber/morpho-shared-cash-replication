"""Shared per-provider pacing across collectors; batches consume one slot per RPC item."""
import time,fcntl,tempfile,hashlib,re
from pathlib import Path
RATES={'https://portal.sqd.dev/datasets/base-mainnet/stream':8.,'https://rpc.baseazul.dev':70.,'https://mainnet.base.org/':4.,'https://base.gateway.tenderly.co':6.}
def cooldown_path(url):return Path(tempfile.gettempdir())/('jrf_rpc_cooldown_'+hashlib.sha256(url.encode()).hexdigest()[:16])
def backoff(url,message):
 if not any(s in str(message).lower() for s in ['429','rate limit','too many','budget']):return
 match=re.search(r'resets? in (\d+)s',str(message));seconds=int(match.group(1))+3 if match else 60
 p=cooldown_path(url)
 with p.open('a+') as f:
  fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);old=f.read();until=max(float(old) if old else 0,time.time()+seconds);f.seek(0);f.truncate();f.write(str(until));f.flush();fcntl.flock(f,fcntl.LOCK_UN)
def wait(url,count=1):
 rate=RATES.get(url,4.);p=Path(tempfile.gettempdir())/('jrf_rpc_pacing_'+hashlib.sha256(url.encode()).hexdigest()[:16])
 cp=cooldown_path(url)
 while True:
  try:delay=float(cp.read_text())-time.time() if cp.exists() else 0
  except ValueError:delay=.1
  if delay>0:time.sleep(min(delay,30));continue
  with p.open('a+') as f:
   fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);s=f.read();now=time.time();slot=max(now,float(s) if s else now);f.seek(0);f.truncate();f.write(str(slot+count/rate));f.flush();fcntl.flock(f,fcntl.LOCK_UN)
  time.sleep(max(0,slot-time.time()))
  try:delay=float(cp.read_text())-time.time() if cp.exists() else 0
  except ValueError:delay=.1
  if delay<=0:return
