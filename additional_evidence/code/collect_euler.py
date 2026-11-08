from chain_access import *
import pandas as pd
USDC='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48';FAC='0x59709B029B140C853FE28d277f83C3a65e308aF4';CHAIN=1
DATES=['2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31','2026-09-29']
def collect(day):
 outpath=A/'raw'/f'euler_{day}.json'
 if outpath.exists():return json.loads(outpath.read_text())
 h=block_at(CHAIN,int((pd.Timestamp(day,tz='UTC')+pd.Timedelta(days=1)).timestamp()));b=h['block'];n=batch(CHAIN,b,[(FAC,sel('getVaultListLength()'))])[0]
 if not n:return {'day':day,'header':h,'status':'factory_not_deployed'}
 vs=[addr(x[0]) for x in batch(CHAIN,b,[(FAC,sel('vaultList(uint256)')+word(i)) for i in range(n[0])])];az=batch(CHAIN,b,[(v,sel('asset()')) for v in vs]);vs=[v for v,x in zip(vs,az) if x and addr(x[0])==USDC];vals=batch(CHAIN,b,[(v,sel(f)) for v in vs for f in ['totalAssets()','withdrawQueueLength()','lostAssets()','lastTotalAssets()']]);vaults=[];q=[]
 for i,v in enumerate(vs):
  z=vals[4*i:4*i+4];assert z[0] and z[1];vaults.append({'address':v,'totalAssets':z[0][0],'length':z[1][0],'lostAssets':z[2][0] if z[2] else None,'lastTotalAssets':z[3][0] if z[3] else None});q += [(v,sel('withdrawQueue(uint256)')+word(j)) for j in range(z[1][0])]
 qs=iter(batch(CHAIN,b,q));keys=[]
 for v in vaults:
  v['queue']=[addr(next(qs)[0]) for j in range(v['length'])];keys.extend((v['address'],m) for m in v['queue'])
 pos=batch(CHAIN,b,[(v,sel('expectedSupplyAssets(address)')+word(int(m,16))) for v,m in keys]);mids=sorted({m for v,m in keys});zz=batch(CHAIN,b,[(m,sel(f)) for m in mids for f in ['asset()','cash()','totalAssets()','withdrawQueueLength()']]);markets={}
 for i,m in enumerate(mids):
  z=zz[4*i:4*i+4];markets[m]={'asset':addr(z[0][0]) if z[0] else None,'cash':z[1][0] if z[1] else None,'totalAssets':z[2][0] if z[2] else None,'nested_earn_queue_length':z[3][0] if z[3] else None};assert markets[m]['asset']==USDC
 positions=[{'vault':v,'market':m,'position':x[0] if x else None} for (v,m),x in zip(keys,pos)]
 out={'day':day,'header':h,'factory':FAC,'factory_vault_count':n[0],'usdc':USDC,'vaults':vaults,'markets':markets,'positions':positions};outpath.write_text(json.dumps(out,indent=2));return out
if __name__=='__main__':
 for day in [DATES[-1]]+DATES[:-1]:
  try:
   z=collect(day);print(day,len(z.get('vaults',[])),len(z.get('positions',[])),'unsupported',[(m,v) for m,v in z.get('markets',{}).items() if v['cash'] is None],flush=True)
  except Exception as e:(A/'raw'/f'euler_{day}.error.json').write_text(json.dumps({'error':str(e)}));print(day,str(e),flush=True)
