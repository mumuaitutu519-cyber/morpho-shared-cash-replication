"""Fixed-universe daily collection. Independent source totals; never fill missing values."""
from pathlib import Path
import json,datetime,time,requests,csv,fcntl,concurrent.futures
ROOT=Path(__file__).resolve().parents[2]; O=ROOT/'outputs'; R=ROOT/'raw'; O.mkdir(exist_ok=True);R.mkdir(exist_ok=True)
V=json.loads((ROOT/'raw/inherited/selected_vaults.json').read_text())
def now():return datetime.datetime.now(datetime.timezone.utc)
def append(path,rows,key):
 old=list(csv.DictReader(path.open())) if path.exists() else []
 seen={tuple(x[k] for k in key) for x in old}; rows=[x for x in rows if tuple(str(x[k]) for k in key) not in seen]
 if not rows:return
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(old+rows)
def main():
 lock=(O/'public_liquidity.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
 day=now().date().isoformat(); daily=O/'public_liquidity_daily.csv'
 if daily.exists() and any(x['date_utc']==day for x in csv.DictReader(daily.open())):
  row=next(x for x in csv.DictReader(daily.open()) if x['date_utc']==day)
  print(json.dumps({'date_utc':day,'idempotent_skip':True,'public_sum':row['graphql_public_sum_usdc'],'joint_upper':row['joint_upper_usdc'],'difference_ratio':row['difference_ratio']}),flush=True);return
 q='query{'+''.join(f'v{i}:vaultByAddress(address:"{v["address"]}",chainId:8453)'+'{address name liquidity{underlying usd} state{blockNumber timestamp totalAssets allocation{supplyAssets market{marketId state{supplyAssets borrowAssets liquidityAssets}}}}}' for i,v in enumerate(V))+'}'
 jobs=[('graphql','POST','https://api.morpho.org/graphql',{'query':q})]+[(v['address'].lower(),'GET','https://api.morpho.org/v0/vaults-v1/8453:'+v['address']+'/state',None) for v in V]
 def call(job):
  label,method,url,body=job;attempts=[];result=None
  for n in (1,2):
   a={'attempt':n,'retrieved_utc':now().isoformat(),'method':method,'url':url,'request':body}
   try:
    r=requests.request(method,url,json=body,timeout=45);a.update(status=r.status_code,body=r.text)
    z=r.json();a['response']=z
    if r.status_code!=200 or z.get('errors'):raise ValueError('HTTP/GraphQL response error')
    d=z.get('data');assert d is not None,'missing data'
    if label=='graphql':
     for i in range(10):
      v=d.get('v'+str(i));assert v and v.get('state') and v.get('liquidity'),'missing vault/state/liquidity'
      for k in ('underlying','usd'):assert v['liquidity'].get(k) is not None,'missing liquidity '+k
      for k in ('blockNumber','timestamp','totalAssets','allocation'):assert v['state'].get(k) is not None,'missing state '+k
      assert v['address'].lower()==V[i]['address'].lower(),'vault identity mismatch'
      assert int(v['liquidity']['underlying'])>=0 and int(v['state']['totalAssets'])>=0,'invalid asset amount'
      int(v['state']['blockNumber']);int(v['state']['timestamp']);float(v['liquidity']['usd'])
      for al in v['state']['allocation']:
       assert al.get('supplyAssets') is not None,'missing allocation supplyAssets'
       pos=int(al['supplyAssets']);assert pos>=0,'negative position'
       if pos>0:
        market=al.get('market') or {};state=market.get('state') or {}
        assert market.get('marketId') and state.get('supplyAssets') is not None and state.get('borrowAssets') is not None,'missing positive-position market state'
        assert int(state['supplyAssets'])>=int(state['borrowAssets'])>=0,'invalid market amounts'
    else:
     for k in ('withdrawable_assets','last_indexed_block','total_assets'):assert d.get(k) is not None,'missing REST '+k
     assert str(d.get('chain_id'))=='8453' and str(d.get('address','')).lower()==label,'REST identity mismatch'
     assert int(d['withdrawable_assets'])>=0 and int(d['total_assets'])>=0,'invalid REST amounts'
     int(d['last_indexed_block'])
    result=d
   except Exception as e:a['error']=str(e)
   attempts.append(a)
   if result is not None:break
   if n==1:time.sleep(2)
  return label,{'attempts':attempts,'success':result is not None,'data':result}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex: responses=dict(ex.map(call,jobs))
 stamp=now();rawpath=R/('public_liquidity_'+stamp.strftime('%Y%m%d_%H%M%S')+'.json')
 envelope={'collection_utc':stamp.isoformat(),'date_utc':day,'vault_universe':V,'responses':responses}
 with rawpath.open('x') as f:json.dump(envelope,f)
 errors=[f'{label}: attempt {a["attempt"]}: {a["error"]}' for label,r in responses.items() for a in r['attempts'] if 'error' in a]
 rows=[];markets={};positions={};graph=responses['graphql']['data'];complete=graph is not None
 for i,v in enumerate(V):
  addr=v['address'].lower();g=graph.get('v'+str(i)) if graph else None;rest=responses[addr]['data'];issues=[]
  row=dict(date_utc=day,collection_utc=stamp.isoformat(),vault=addr,name=v['name'],total_assets_usdc=None,graphql_underlying_usdc=None,graphql_liquidity_usd=None,rest_withdrawable_usdc=None,vault_timestamp=None,vault_block=None,rest_block=None,reconstructed_single_usdc=None,graphql_minus_single_usdc=None,positions_residual_usdc=None,positive_market_count=None,positive_positions_json=None,status=None,issues=None,raw_file=str(rawpath.relative_to(ROOT)))
  if rest:row.update(rest_withdrawable_usdc=int(rest['withdrawable_assets'])/1e6,rest_block=rest['last_indexed_block'])
  else:issues.append('REST missing after retry')
  if g:
   s=g['state'];row.update(total_assets_usdc=int(s['totalAssets'])/1e6,graphql_underlying_usdc=int(g['liquidity']['underlying'])/1e6,graphql_liquidity_usd=g['liquidity']['usd'],vault_timestamp=s['timestamp'],vault_block=s['blockNumber'])
   known=0;single=0;positive=[];valid=True
   for a in s['allocation']:
    if a.get('supplyAssets') is None:valid=False;issues.append('null allocation supplyAssets');continue
    p=int(a['supplyAssets']);known+=p
    if p<=0:continue
    m=a.get('market') or {};ms=m.get('state') or {};mid=m.get('marketId')
    positive.append({'market':mid,'supplyAssets':p})
    if not mid or ms.get('supplyAssets') is None or ms.get('borrowAssets') is None:valid=False;issues.append('positive position missing market state');continue
    cash=int(ms['supplyAssets'])-int(ms['borrowAssets'])
    if cash<0:valid=False;issues.append('negative market cash');continue
    if mid in markets and markets[mid]!=cash:valid=False;complete=False;issues.append('cross-vault market-state conflict')
    markets[mid]=cash;positions[mid]=positions.get(mid,0)+p;single+=min(p,cash)
   residual=int(s['totalAssets'])-known;row.update(positions_residual_usdc=residual/1e6,positive_market_count=len(positive),positive_positions_json=json.dumps(positive))
   if abs(residual)>1:valid=False;issues.append('totalAssets not reconciled to allocations; unknown exposure retained')
   if valid:row.update(reconstructed_single_usdc=single/1e6,graphql_minus_single_usdc=(int(g['liquidity']['underlying'])-single)/1e6)
   else:complete=False
  else:complete=False;issues.append('GraphQL missing after retry')
  row.update(status='complete' if not issues else 'incomplete',issues='; '.join(issues));rows.append(row)
 def total(field):
  xs=[r[field] for r in rows];return sum(xs) if all(x is not None for x in xs) else None
 public=total('graphql_underlying_usdc');resttotal=total('rest_withdrawable_usdc');J=sum(min(p,markets[m]) for m,p in positions.items())/1e6 if complete else None
 diff=public-J if public is not None and J is not None else None
 summary=dict(date_utc=day,collection_utc=stamp.isoformat(),n_vaults=10,graphql_public_sum_usdc=public,rest_public_sum_usdc=resttotal,joint_upper_usdc=J,public_minus_joint_usdc=diff,difference_ratio=diff/public if diff is not None and public>0 else None,status='complete' if complete and resttotal is not None else 'incomplete',failed_attempts=len(errors),issues=json.dumps(errors+[r['name']+': '+r['issues'] for r in rows if r['issues']]),raw_file=str(rawpath.relative_to(ROOT)))
 append(O/'public_liquidity_by_vault.csv',rows,['date_utc','vault']);append(daily,[summary],['date_utc'])
 print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
