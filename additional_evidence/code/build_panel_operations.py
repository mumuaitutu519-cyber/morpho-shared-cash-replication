"""Join immutable operation sources; exact micro-USDC market cash and opening-network flows."""
from pathlib import Path
import sys,json,gzip,sqlite3,concurrent.futures
import pandas as pd,numpy as np
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';O=P/'outputs';sys.path.insert(0,str(A/'code'));from chain_access import rpc,batch,sel
M='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';start=25098126;end=start+439*43200
markets=json.loads((P/'raw/operation_query.json').read_text())['markets'];vs=[x['address'].lower() for x in json.loads((R/'raw/inherited/selected_vaults.json').read_text())]
def load():
 out=P/'raw/market_operations.parquet'
 if out.exists():return pd.read_parquet(out)
 coverage=json.loads((P/'raw/market_api_coverage.json').read_text());assert all(x['complete'] for x in coverage)
 old=R/'real_consequences/raw/market_flows';cert=[json.loads(f.read_text()) for f in old.glob('*/complete.json') if not f.name.startswith('._')];assert len(cert)==15
 pieces=[]
 for folder in [old,P/'raw/market_api']:
  rows=[]
  for file in sorted(folder.glob('*/*.json.gz')):
   if file.name.startswith('._'):continue
   packet=json.load(gzip.open(file,'rt'))
   for r in packet['response']['data']['marketTransactions']['items']:
    d=r['data'];rows.append(dict(tx=r['txHash'],log_index=r['logIndex'],block=int(r['blockNumber']),timestamp=int(r['timestamp']),market=r['market']['marketId'],kind=r['type'],owner=r['user']['address'].lower(),assets_micro=int(d.get('assets',d.get('repaidAssets',0))),bad_debt_micro=int(d.get('badDebtAssets',0))))
  pieces.append(pd.DataFrame(rows));print('loaded',folder,len(rows),flush=True)
 d=pd.concat(pieces,ignore_index=True);assert not d.duplicated(['tx','log_index']).any();d=d[d.market.isin(markets)&d.block.gt(start)&d.block.le(end)].sort_values(['block','log_index']).reset_index(drop=True);d.to_parquet(out,index=False);return d
if __name__=='__main__':
 d=load();d['date']=pd.to_datetime(d.timestamp,unit='s',utc=True).dt.strftime('%Y-%m-%d');print('operations',len(d),d.kind.value_counts().to_dict(),flush=True)
 cashfile=P/'raw/opening_market_cash.json'
 if cashfile.exists():cash0=json.loads(cashfile.read_text())
 else:
  vals=batch(8453,start,[(M,sel('market(bytes32)')+m[2:]) for m in markets]);cash0={m:int(x[0])-int(x[2]) for m,x in zip(markets,vals)};cashfile.write_text(json.dumps(cash0,indent=2))
 d['supply_flow_micro']=np.select([d.kind.eq('Supply'),d.kind.eq('Withdraw')],[d.assets_micro,-d.assets_micro],default=0)
 d['borrow_flow_micro']=np.select([d.kind.eq('Borrow'),d.kind.eq('Repay')],[d.assets_micro,-d.assets_micro],default=0)
 d['liquidation_repaid_micro']=d.assets_micro.where(d.kind.eq('Liquidation'),0);d['cash_delta_micro']=d.supply_flow_micro-d.borrow_flow_micro+d.liquidation_repaid_micro
 d['cash_after_micro']=d.groupby('market').cash_delta_micro.cumsum()+d.market.map(cash0);assert d.cash_after_micro.ge(0).all()
 # Preceding block cash, not prior log in the same block.
 block=d.groupby(['market','block']).agg(delta=('cash_delta_micro','sum'),timestamp=('timestamp','first'));block['cash_after']=block.groupby(level=0).delta.cumsum()+block.index.get_level_values('market').map(cash0);block['cash_before']=block.cash_after-block.delta
 d['preblock_cash_micro']=pd.MultiIndex.from_frame(d[['market','block']]).map(block.cash_before);d.to_parquet(P/'raw/market_operations_cash.parquet',index=False)
 daily=d.groupby(['date','market']).agg(supply_flow_micro=('supply_flow_micro','sum'),borrow_flow_micro=('borrow_flow_micro','sum'),liquidation_repaid_micro=('liquidation_repaid_micro','sum'),bad_debt_micro=('bad_debt_micro','sum'),cash_delta_micro=('cash_delta_micro','sum'))
 dates=pd.date_range('2025-01-16','2026-03-30').strftime('%Y-%m-%d');daily=daily.reindex(pd.MultiIndex.from_product([dates,markets],names=['date','market']),fill_value=0).reset_index();daily['cash_after_micro']=daily.groupby('market').cash_delta_micro.cumsum()+daily.market.map(cash0)
 pos=pd.read_parquet(R/'outputs/empirical/positions.parquet');pos=pos[pos.date.between('2025-01-15','2026-03-30')];states=pos.groupby(['date','market']).first().reset_index();check=daily.merge(states[['date','market','market_cash','market_supply']],on=['date','market']);check['cash_error_micro']=check.cash_after_micro-check.market_cash;check.to_csv(O/'market_cash_reconciliation.csv',index=False);assert check.cash_error_micro.abs().max()<=1,(check.cash_error_micro.abs().max(),check.loc[check.cash_error_micro.abs().idxmax()].to_dict())
 daily.to_parquet(O/'market_operation_daily.parquet',index=False)
 own=d[d.owner.isin(vs)&d.kind.isin(['Supply','Withdraw'])].copy();own.to_parquet(P/'raw/sample_vault_position_operations.parquet',index=False);of=own.groupby(['date','owner','market']).supply_flow_micro.sum();oc=own.groupby(['date','owner']).size();allown=own.groupby(['date','owner']).supply_flow_micro.sum()
 market_all_sample=own.groupby(['date','market']).supply_flow_micro.sum();flows=daily.set_index(['date','market']);hold={(dt,v):g[g.position>0] for (dt,v),g in pos.groupby(['date','vault'])};p=pd.read_parquet(R/'outputs/empirical/vault_panel.parquet');p=p[p.date.between('2025-01-16','2026-03-30')].sort_values(['vault','date']);rows=[]
 for vault,g in p.groupby('vault'):
  records=list(g.to_dict('records'))
  for prev,cur in zip(records,records[1:]):
   day=cur['date'];h=hold[(prev['date'],vault)];ms=list(h.market);self_open=sum(int(of.get((day,vault,m),0)) for m in ms);ownall=int(allown.get((day,vault),0));peer=sum(int(market_all_sample.get((day,m),0))-int(of.get((day,vault,m),0)) for m in ms);total=sum(int(flows.loc[(day,m),'supply_flow_micro']) for m in ms);outside=total-self_open-peer;borrow=sum(int(flows.loc[(day,m),'borrow_flow_micro']) for m in ms);liq=sum(int(flows.loc[(day,m),'liquidation_repaid_micro']) for m in ms)
   rows.append(dict(vault=vault,date=day,opening_date=prev['date'],dW=(int(cur['capacity'])-int(prev['capacity']))/1e12,dD=cur['D']-prev['D'],OwnFlow=ownall/1e12,OtherVaultFlow=peer/1e12,OutsideFlow=outside/1e12,BorrowFlow=borrow/1e12,ExposureShare=prev['shared_exposure'],OwnFlow_micro=ownall,OwnFlow_opening_micro=self_open,OwnFlow_outside_opening_micro=ownall-self_open,OtherVaultFlow_micro=peer,OutsideFlow_micro=outside,TotalSupplyFlow_micro=total,LiquidationRepayment_micro=liq,own_operation_count=int(oc.get((day,vault),0)),position_set_changed=set(ms)!=set(hold[(day,vault)].market)))
 q=pd.DataFrame(rows);q['Peer_x_exposure']=q.OtherVaultFlow*q.ExposureShare;assert len(q)==4380;assert (q.OwnFlow_opening_micro+q.OtherVaultFlow_micro+q.OutsideFlow_micro==q.TotalSupplyFlow_micro).all();q.to_parquet(O/'spillover_panel.parquet',index=False)
 # Direct raw-ledger verification of ten deterministic randomly drawn vault-days.
 audits=[]
 for r in q.sample(10,random_state=20261003).itertuples():
  ms=set(hold[(r.opening_date,r.vault)].market);raw=d[d.date.eq(r.date)&d.owner.isin(vs)&d.owner.ne(r.vault)&d.market.isin(ms)&d.kind.isin(['Supply','Withdraw'])];value=int(raw.supply_flow_micro.sum());assert value==r.OtherVaultFlow_micro;audits.append(dict(date=r.date,vault=r.vault,ledger_logs=len(raw),direct_micro=value,constructed_micro=r.OtherVaultFlow_micro))
 pd.DataFrame(audits).to_csv(O/'peer_flow_random_audit.csv',index=False)
 # Borrow transactions aggregate multiple logs within the same market and transaction.
 bor=d[d.kind.eq('Borrow')].groupby(['market','tx','block'],as_index=False).agg(timestamp=('timestamp','first'),borrow_micro=('assets_micro','sum'),preblock_cash_micro=('preblock_cash_micro','first'),first_log_index=('log_index','min'));bor['threshold_pass']=bor.borrow_micro*10>bor.preblock_cash_micro;events=bor[bor.threshold_pass].sort_values(['market','timestamp','block','first_log_index']).copy();events['prior_large_timestamp']=events.groupby('market').timestamp.shift();events['keep_24h']=events.prior_large_timestamp.isna()|(events.timestamp-events.prior_large_timestamp>=86400);events.to_csv(O/'borrow_event_candidates.csv',index=False);print('EVENTS',len(events),'retained',int(events.keep_24h.sum()),flush=True)
 (P/'flow_checks.json').write_text(json.dumps({'operations':len(d),'market_cash_checks':len(check),'max_cash_error_micro':int(check.cash_error_micro.abs().max()),'vault_days':len(q),'own_zero_net':int(q.OwnFlow_micro.eq(0).sum()),'own_no_operations':int(q.own_operation_count.eq(0).sum()),'own_flow_outside_opening_nonzero':int(q.OwnFlow_outside_opening_micro.ne(0).sum()),'liquidation_nonzero_days':int(q.LiquidationRepayment_micro.ne(0).sum()),'large_borrow_candidates':len(events),'retained_events':int(events.keep_24h.sum())},indent=2))
