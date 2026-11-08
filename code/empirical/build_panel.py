from pathlib import Path
import json,hashlib,itertools
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[2];O=R/'outputs/empirical';O.mkdir(exist_ok=True)

def build(z):
 M={}; WAD=10**18;rows=[];assetchecks=[]
 for m,x in z['market'].items():
  s,ss,b,bs,last,fee=x['state'];elapsed=z['timestamp']-last;interest=0
  if 'borrowRate' in x:
   first=x['borrowRate']*elapsed;second=first*first//(2*WAD);third=second*first//(3*WAD);interest=b*(first+second+third)//WAD;s+=interest;b+=interest
   if fee:
    fa=interest*fee//WAD;ss+=fa*(ss+10**6)//(s-fa+1)
  assert s>=b
  M[m]={'supply':s,'supplyshares':ss,'borrow':b,'cash':s-b}
 for v in z['vaults']:
  total=0;S=0
  for m in v['queue']:
   shares=z['positions'][v['address']][m][0];a=M[m];p=shares*(a['supply']+1)//(a['supplyshares']+10**6);total+=p;cash=min(a['cash'],z['morpho_token_balance']);stand=min(p,cash);S+=stand
   rows.append({'date':z['name'],'block':z['block'],'vault':v['address'],'name':v['name'],'market':m,'position':p,'cash':cash,'market_cash':a['cash'],'market_supply':a['supply'],'market_borrow':a['borrow'],'standalone':stand,'shares':str(shares)})
  loss=max(v['lostAssets'],v['lastTotalAssets']-total) if v['lostAssets'] is not None else 0
  predicted=total+loss;assert predicted==v['totalAssets'],(z['name'],v['name'],predicted,v['totalAssets'])
  assetchecks.append({'date':z['name'],'vault':v['address'],'name':v['name'],'block':z['block'],'timestamp':z['timestamp'],'block_hash':z['block_hash'],'assets':v['totalAssets'],'positions':total,'loss':loss,'capacity':S,'asset_reconciliation_gap':predicted-v['totalAssets']})
 return rows,assetchecks

if __name__=='__main__':
 raws=sorted(p for p in (R/'raw/chain_panel').glob('*_decoded.json') if not p.name.startswith('._'));rows=[];check=[]
 for p in raws:
  a,b=build(json.loads(p.read_text()));rows+=a;check+=b
 pos=pd.DataFrame(rows);v=pd.DataFrame(check);pos.to_parquet(O/'positions.parquet',index=False);daily=[];parts=[]
 for day,g in pos.groupby('date',sort=True):
  mt=g.groupby('market').agg(P=('position','sum'),cash=('cash','first'),supply=('market_supply','first'),borrow=('market_borrow','first'),S=('standalone','sum'));mt['J']=np.minimum(mt.P,mt.cash);mt['dup']=mt.S-mt.J
  assert (mt.dup>=0).all();S=int(mt.S.sum());J=int(mt.J.sum());use=mt[mt.P>0];c=use.cash;hhi=float(((c/c.sum())**2).sum()) if c.sum()>0 else np.nan
  daily.append({'date':day,'S':S/1e6,'J':J/1e6,'duplicate':(S-J)/1e6,'duplication':(S-J)/S if S else np.nan,'cash_hhi':hhi,'assets':v[v.date==day].assets.sum()/1e6,'utilization10':float((use.P*(use.borrow/use.supply.replace(0,np.nan))).sum()/use.P.sum()*10),'positive_markets':len(use)})
  for addr,h in g.groupby('vault'):
   h=h.copy();h['other']=h.market.map(mt.P)-h.position;h['increment']=np.minimum(h.position+h.other,h.cash)-np.minimum(h.other,h.cash);sv=int(h.standalone.sum());dv=(sv-int(h.increment.sum()))/sv if sv else np.nan;assert np.isnan(dv) or -1e-12<=dv<=1+1e-12
   assets=int(v[(v.date==day)&(v.vault==addr)].assets.iloc[0]);own=h[h.position>0];uw=(own.position*(own.market_borrow/own.market_supply.replace(0,np.nan))).sum()/own.position.sum() if own.position.sum()>0 else np.nan
   peerS=mt.S-h.groupby('market').standalone.sum().reindex(mt.index,fill_value=0);peerP=mt.P-h.groupby('market').position.sum().reindex(mt.index,fill_value=0);peerJ=np.minimum(peerP,mt.cash);peerD=(peerS.sum()-peerJ.sum())/peerS.sum() if peerS.sum()>0 else np.nan
   unheld=mt[~mt.index.isin(own.market)];placebo=unheld.dup.sum()/unheld.S.sum() if unheld.S.sum()>0 else np.nan
   parts.append({'date':day,'vault':addr,'name':h.name.iloc[0] if 'name' in h else '', 'D':dv,'D10':dv*10,'coverage10':sv/assets*10 if assets else np.nan,'log_assets':np.log(assets/1e6) if assets else np.nan,'utilization10':uw*10,'active_markets':int((h.position>0).sum()),'shared_exposure':h.loc[(h.other>0)&(h.position>0),'position'].sum()/h.position.sum() if h.position.sum()>0 else np.nan,'own_cash':own.cash.sum()/1e6,'peerD10':peerD*10,'placebo10':placebo*10})
 panel=v.merge(pd.DataFrame(parts),on=['date','vault','name'],validate='one_to_one');panel.to_parquet(O/'vault_panel.parquet',index=False);pd.DataFrame(daily).to_csv(O/'daily.csv',index=False)
 # Direct owner-function validation against archived Spark calls (same historical blocks).
 old=pd.read_csv(R/'reports/revision6/withdrawal_capacity.csv',dtype=str);sp=panel[panel.vault.eq('0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a')];vv=old.merge(sp,on='date');vv['difference']=[min(int(c),int(w))-int(m) for c,w,m in zip(vv.claim_micro,vv.capacity,vv.max_withdraw_micro)]
 vv[['date','block_x','claim_micro','capacity','max_withdraw_micro','difference']].to_csv(O/'owner_function_validation.csv',index=False)
 hist=panel[~panel.date.str.startswith('snapshot')];summary={'days':int(hist.date.nunique()),'vault_days':len(hist),'market_ids_positive':pos[(pos.position>0)&~pos.date.str.startswith('snapshot')].market.nunique(),'asset_reconciliation_max_micro':int(panel.asset_reconciliation_gap.abs().max()),'owner_validation_days':len(vv),'owner_max_gap_micro':int(vv.difference.abs().max()) if len(vv) else None,'zero_capacity_rows':int(hist.capacity.eq(0).sum()),'D_undefined':int(hist.D.isna().sum())}
 (O/'panel_validation.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
