from pathlib import Path
import json,csv,collections,hashlib
R=Path(__file__).resolve().parents[1];out=R/'outputs';daily=[];byvault=[];fail=[]
for p in sorted((R/'raw').glob('public_liquidity_*.json')):
 try:z=json.loads(p.read_text())
 except Exception as e:fail.append({'file':p.name,'error':str(e)});continue
 date=z['date_utc'];vlist=z['vault_universe'];rs=z['responses'];g=(rs.get('graphql') or {}).get('data');market={};pos=collections.defaultdict(int);valid=True;pub=[];rest=[];reasons=[]
 for i,v in enumerate(vlist):
  a=v['address'].lower();x=g.get('v'+str(i)) if g else None;rt=(rs.get(a) or {}).get('data');issues=[]
  row={'date':date,'vault':a,'name':v['name'],'raw_file':p.name}
  if rt:row['rest_public_usdc']=int(rt['withdrawable_assets'])/1e6;rest.append(int(rt['withdrawable_assets']))
  if not x:valid=False;issues.append('missing_vault_state');byvault.append(row);continue
  s=x['state'];public=int(x['liquidity']['underlying']);pub.append(public);known=0;own=0
  for alloc in s['allocation']:
   q=alloc.get('supplyAssets')
   if q is None:valid=False;issues.append('missing_position');continue
   q=int(q);known+=q
   if q==0:continue
   m=alloc.get('market') or {};mid=m.get('marketId');state=m.get('state') or {}
   if mid is None or state.get('supplyAssets') is None or state.get('borrowAssets') is None:valid=False;issues.append('missing_market_cash');continue
   cash=int(state['supplyAssets'])-int(state['borrowAssets']);assert cash>=0
   if mid in market and market[mid]!=cash:valid=False;issues.append('conflicting_market_state')
   market[mid]=cash;pos[mid]+=q;own+=min(q,cash)
  residual=int(s['totalAssets'])-known
  if abs(residual)>1:valid=False;issues.append('unreconciled_total_assets')
  row.update(public_usdc=public/1e6,total_assets_usdc=int(s['totalAssets'])/1e6,known_allocations_usdc=known/1e6,allocation_residual_usdc=residual/1e6,benchmark_usdc=own/1e6 if not issues else None,block=s['blockNumber'],issues=';'.join(issues));byvault.append(row)
  if issues:reasons.append(v['name']+': '+','.join(issues))
 assert len(pub)==10
 j=sum(min(pos[m],market[m]) for m in pos) if valid else None
 daily.append({'date':date,'n_vaults':len(vlist),'public_sum_usdc':sum(pub)/1e6,'rest_sum_usdc':sum(rest)/1e6 if len(rest)==10 else None,'joint_cash_usdc':j/1e6 if j is not None else None,'duplication_rate':(sum(pub)-j)/sum(pub) if j is not None else None,'status':'complete' if valid else 'incomplete','issues':' | '.join(reasons),'raw_file':p.name,'raw_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def save(name,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with (out/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
save('updated_public_daily.csv',daily);save('updated_public_by_vault.csv',byvault)
summary={'dates':len(daily),'start':min(r['date'] for r in daily),'end':max(r['date'] for r in daily),'vault_days':len(byvault),'complete_joint_dates':sum(r['status']=='complete' for r in daily),'invalid_raw_files':fail,'latest':daily[-1],'incomplete_vaults':sorted(set(r['name'] for r in byvault if r.get('issues')))}
(out/'updated_public_validation.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
