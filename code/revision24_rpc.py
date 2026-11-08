"""Finite, cached read-only Base archive queries; never sends transactions."""
from pathlib import Path
import json, hashlib, datetime, urllib.request, urllib.error, time
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw/revision24'
URL='https://base.gateway.tenderly.co'
URLS={'tenderly':URL,'drpc':'https://base.drpc.org'}
ALLOWED={'eth_chainId','eth_getBlockByNumber','eth_getLogs','eth_call','debug_traceCall','debug_traceTransaction'}
def selector(sig):
 from Crypto.Hash import keccak
 k=keccak.new(digest_bits=256);k.update(sig.encode());return '0x'+k.hexdigest()[:8]
VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
PWORD=PROXY[2:].rjust(64,'0')
def query(name,method,params,provider='tenderly'):
 assert method in ALLOWED
 url=URLS[provider];stop=RAW/(provider+'.access-stop.json')
 if provider=='drpc':assert method not in {'debug_traceCall','debug_traceTransaction','eth_getLogs'}, 'Paid methods excluded'
 req={'jsonrpc':'2.0','id':1,'method':method,'params':params}
 bodypath=RAW/(name+'.body');metapath=RAW/(name+'.json')
 if metapath.exists():
  meta=json.loads(metapath.read_text());assert meta['request']==req and meta['url']==url
  body=bodypath.read_bytes();assert hashlib.sha256(body).hexdigest()==meta['sha256']
 else:
  if stop.exists():raise RuntimeError('Provider access stopped')
  r=urllib.request.Request(url,data=json.dumps(req).encode(),headers={'Content-Type':'application/json','User-Agent':'Academic read-only historical audit'})
  try:
   with urllib.request.urlopen(r,timeout=35) as response:status=response.status;body=response.read()
  except urllib.error.HTTPError as e:status=e.code;body=e.read()
  except Exception as e:status=None;body=json.dumps({'transport_error':str(e)}).encode()
  bodypath.write_bytes(body)
  meta={'url':url,'request':req,'http_status':status,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':hashlib.sha256(body).hexdigest()}
  metapath.write_text(json.dumps(meta,indent=2)+'\n')
  if status in [401,403,429]:
   stop.write_text(json.dumps(meta,indent=2)+'\n');raise RuntimeError(f'Provider access stopped: {status}')
  time.sleep(1.0)
 obj=json.loads(body)
 if 'error' in obj and any(s in json.dumps(obj['error']).lower() for s in ['unauthorized','authentication required','rate limit','access denied','api key required']):
  stop.write_text(json.dumps(meta,indent=2)+'\n');raise RuntimeError('Provider access stopped by RPC error')
 return obj
def call(data):return {'from':PROXY,'to':VAULT,'data':data,'gas':'0x989680'}
def withdraw(amount):return selector('withdraw(uint256,address,address)')+f'{int(amount):064x}'+PWORD+PWORD


def encode_bytes_array(values):
    """Canonical ABI encoding of one bytes[] argument."""
    word = lambda x: f'{x:064x}'
    parts, offsets, offset = [], [], 32 * len(values)
    for value in values:
        b = bytes.fromhex(value.removeprefix('0x'))
        part = word(len(b)) + b.hex().ljust(((len(b) + 31) // 32) * 64, '0')
        offsets.append(word(offset)); parts.append(part); offset += len(part) // 2
    return word(32) + word(len(values)) + ''.join(offsets + parts)


def decode_bytes_array(value, expected):
    raw = bytes.fromhex(value.removeprefix('0x'))
    def uint(offset):
        assert offset >= 0 and offset + 32 <= len(raw)
        return int.from_bytes(raw[offset:offset+32])
    assert uint(0) == 32 and uint(32) == expected
    values = []
    for i in range(expected):
        start = 64 + uint(64 + 32*i)
        size = uint(start)
        assert start + 32 + size <= len(raw)
        values.append('0x' + raw[start+32:start+32+size].hex())
    assert encode_bytes_array(values) == raw.hex(), 'Noncanonical bytes[] response'
    return values

