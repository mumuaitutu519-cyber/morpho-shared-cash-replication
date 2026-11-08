"""Frozen R22 transaction links, intraday cash, and market-level accounting.

Only archived observations enter this analysis; no network or regressions.
"""
from pathlib import Path
from collections import defaultdict
import copy, hashlib, json, statistics, sys
import numpy as np
import pandas as pd
from revision6_first_disposition import extrema, lp_check

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/revision22'
PROXY='0x2917956eff0b5eaf030abdb4ef4296df775009ca'
VAULT='0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a'
MARKET='0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836'
DATES=['2025-04-01','2025-04-08','2025-06-02','2025-10-21','2025-11-21','2025-11-25','2025-11-26','2025-11-28']
def read(path):return pd.read_csv(ROOT/path,dtype=str)
def load(path):return json.loads((ROOT/path).read_text())
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def cs(name,rows):pd.DataFrame(rows).to_csv(OUT/name,index=False)
def stats(values):
    a=np.array(list(values),dtype=float)
    return {k:float(np.quantile(a,q)) for k,q in [('min',0),('p25',.25),('median',.5),('p75',.75),('p95',.95),('max',1)]}
def funding():
    operations=read('reports/revision6/domain_6_operations.csv')
    selected=operations[operations.validated_native_transfer.eq('True')&operations.operation.str.endswith('deposit')]
    manifest={x['destination_tx']:x for x in load('reports/revision6/domain_6_first_disposition_manifest.json')['items']}
    matches=read('reports/revision6/domain_6_matches.csv')
    times={tx:int(g.destination_timestamp.iloc[0]) for tx,g in matches.groupby('destination_tx')}
    states=read('reports/revision6/withdrawal_capacity.csv').set_index('date')
    cohort={(x.tx,int(x.log_index)):x for x in read('reports/revision21/cohort_vault_event_join.csv').itertuples()}
    rows=[];maxerr=0
    for op in selected.itertuples():
        item=manifest[op.destination_tx]
        events=[{**x,'target':x['log_index']==int(op.native_transfer_log)} if x['kind']=='out' else x for x in item['events']]
        assert sum(x['kind']=='out' and x['target'] for x in events)==1
        initial=int(item['opening_balance_micro'])
        lo=extrema(initial,events,False)[0];hi=extrema(initial,events,True)[0]
        check=lp_check(initial,events,lo,hi);maxerr=max(maxerr,check['max_error_usdc'])
        amount=int(op.amount_micro_usdc);assert 0<=lo<=hi<=amount
        ts=times[op.destination_tx];date=pd.Timestamp(ts,unit='s',tz='UTC').strftime('%Y-%m-%d')
        row={'tx':op.destination_tx,'block':item['block'],'log_index':int(op.operation_log),'native_transfer_log':int(op.native_transfer_log),
             'timestamp':ts,'date':date,'operation':op.operation,'deposit_micro':str(amount),'shares_raw':op.share_base_units,
             'opening_wallet_cash_micro':str(initial),'matched_arrivals_micro':item['frame_micro'],'other_inflows_micro':str(sum(x['amount'] for x in events if x['kind']=='other_in')),
             'lower_micro':str(lo),'upper_micro':str(hi),'width_micro':str(hi-lo),'width_fraction':(hi-lo)/amount,
             'point_identified':lo==hi,'zero_lower':lo==0,'fully_arrival_funded':lo==hi==amount}
        if op.operation=='Vault deposit':
            source=cohort[(op.destination_tx,int(op.operation_log))]
            assert source.assets_micro==str(amount) and source.shares_raw==op.share_base_units
            previous=(pd.Timestamp(date)-pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            for label,d in [('prior_close',previous),('same_day_close',date)]:
                s=states.loc[d];sample_ts=int(s.block_timestamp)
                row.update({label+'_block':s.block,label+'_timestamp':str(sample_ts),label+'_distance_seconds':str(ts-sample_ts),
                  label+'_claim_micro':s.claim_micro,label+'_capacity_micro':s.max_withdraw_micro,
                  label+'_coverage':int(s.max_withdraw_micro)/int(s.claim_micro)})
            assert int(row['prior_close_distance_seconds'])>0 and int(row['same_day_close_distance_seconds'])<=0
        rows.append(row)
    cs('deposit_event_funding_bounds.csv',rows)
    vault=[x for x in rows if x['operation']=='Vault deposit'];assert len(vault)==94
    cs('vault_deposit_state_connections.csv',vault)
    out={}
    for name,group in [('all_facilities',rows),('vault',vault),('psm',[x for x in rows if x['operation']=='PSM deposit'])]:
        out[name]={'events':len(group),'transactions':len({x['tx'] for x in group}),
          'point_identified':sum(x['point_identified'] for x in group),'zero_lower':sum(x['zero_lower'] for x in group),
          'fully_arrival_funded':sum(x['fully_arrival_funded'] for x in group),
          'width_usdc':stats(int(x['width_micro'])/1e6 for x in group),'width_pct_deposit':stats(100*x['width_fraction'] for x in group),
          'sum_event_lower_micro':str(sum(int(x['lower_micro']) for x in group)),
          'sum_event_upper_micro':str(sum(int(x['upper_micro']) for x in group))}
    out['vault'].update({'prior_close_coverage_pct':stats(100*x['prior_close_coverage'] for x in vault),
      'same_day_close_coverage_pct':stats(100*x['same_day_close_coverage'] for x in vault),
      'prior_close_below_25pct_events':sum(x['prior_close_coverage']<.25 for x in vault),
      'same_day_close_below_25pct_events':sum(x['same_day_close_coverage']<.25 for x in vault),
      'prior_close_lag_hours':stats(int(x['prior_close_distance_seconds'])/3600 for x in vault),
      'same_day_close_lead_hours':stats(-int(x['same_day_close_distance_seconds'])/3600 for x in vault)})
    for label in ['prior_close','same_day_close']:
        joint=[x for x in vault if int(x['lower_micro'])>0 and x[label+'_coverage']<.25]
        out['vault'][label+'_positive_funding_and_subquarter_events']=len(joint)
        out['vault'][label+'_positive_funding_and_subquarter_lower_micro']=str(sum(int(x['lower_micro']) for x in joint))
    # Transparent examples span observed interval shapes: no manual result selection.
    examples=[]
    for label,group in [('earliest_point',[x for x in vault if x['point_identified']]),
                        ('earliest_zero_lower',[x for x in vault if x['zero_lower']]),
                        ('widest_relative_interval',sorted(vault,key=lambda x:(-x['width_fraction'],x['timestamp'],x['log_index']))),
                        ('largest_deposit',sorted(vault,key=lambda x:(-int(x['deposit_micro']),x['timestamp'],x['log_index'])))]:
        if group:
            x=group[0] if label in ['widest_relative_interval','largest_deposit'] else min(group,key=lambda x:(x['timestamp'],x['log_index']))
            examples.append({'selection':label,**x})
    cs('connection_examples.csv',examples)
    out['lp_max_error_usdc']=maxerr
    out['interpretation']='Marginal event intervals, not additive joint endpoints. Adjacent observed UTC closes, not exact transaction-state capacity; account capacity is pooled, not cohort-owned.'
    save('funding_connections_summary.json',out)
    return out

def shared_cash():
    p=read('reports/revision18/funded_positions.csv');rows=[];daily=[]
    for group,names in [('three_vaults',{'spark','moonwell','gauntlet'}),('without_gauntlet',{'spark','moonwell'})]:
        for date,g in p[p.vault.isin(names)].groupby('date',sort=True):
            parts=[]
            for market,h in g.groupby('market',sort=True):
                assert h.market_cash_micro.nunique()==1
                cash=int(h.market_cash_micro.iloc[0]);pos=sum(map(int,h.position_micro))
                I=sum(min(int(x),cash) for x in h.position_micro);J=min(pos,cash)
                x={'group':group,'date':date,'market':market,'vaults':';'.join(sorted(h.vault)),
                   'holders':len(h),'cash_micro':str(cash),'position_sum_micro':str(pos),'separate_micro':str(I),
                   'joint_micro':str(J),'duplicate_micro':str(I-J),'common_cbBTC_market':market==MARKET}
                assert I>=J;parts.append(x);rows.append(x)
            I=sum(int(x['separate_micro']) for x in parts);J=sum(int(x['joint_micro']) for x in parts)
            common=sum(int(x['duplicate_micro']) for x in parts if x['market']==MARKET)
            daily.append({'group':group,'date':date,'separate_micro':str(I),'joint_micro':str(J),'duplicate_micro':str(I-J),
             'duplicate_pct':(I-J)/I*100,'common_duplicate_micro':str(common),'other_duplicate_micro':str(I-J-common),
             'common_share_of_duplicate_pct':common/(I-J)*100 if I>J else None})
    cs('shared_cash_market_decomposition.csv',rows);cs('shared_cash_group_comparison.csv',daily)
    summary={}
    for group in ['three_vaults','without_gauntlet']:
        g=[x for x in daily if x['group']==group]
        summary[group]={'dates':len(g),'positive_duplicate_dates':sum(int(x['duplicate_micro'])>0 for x in g),
          'duplicate_million':stats(int(x['duplicate_micro'])/1e12 for x in g),'duplicate_pct':stats(x['duplicate_pct'] for x in g),
          'common_market_duplicate_million':stats(int(x['common_duplicate_micro'])/1e12 for x in g),
          'other_market_duplicate_million':stats(int(x['other_duplicate_micro'])/1e12 for x in g),
          'common_share_of_duplicate_pct':stats(x['common_share_of_duplicate_pct'] for x in g if x['common_share_of_duplicate_pct'] is not None),
          'separate_million':stats(int(x['separate_micro'])/1e12 for x in g),'joint_million':stats(int(x['joint_micro'])/1e12 for x in g)}
    old=read('reports/revision21/shared_cash_weekly.csv').set_index('date')
    for x in daily:
        if x['group']=='three_vaults':assert x['duplicate_micro']==old.loc[x['date'],'duplicate_cash_micro']
    save('shared_cash_decomposition_summary.json',summary)
    return summary

def intraday():
    market=pd.read_parquet(ROOT/'reports/revision5/market_economic_events.parquet')
    assert not market.duplicated(['block','log_index']).any()
    assert list(zip(market.block,market.log_index))==sorted(zip(market.block,market.log_index))
    sign=market.type.map({'Supply':1,'Withdraw':-1,'Borrow':-1,'Repay':1,'Liquidation':1});assert sign.notna().all()
    delta=sign.astype('int64')*market.assets_raw.astype('int64')
    market['cash_after_micro']=delta.cumsum();market['cash_before_micro']=market.cash_after_micro-delta
    assert market.cash_after_micro.min()>=0
    # Exact event-time common-market cash is distinct from adjacent owner views.
    connections=read('reports/revision22/vault_deposit_state_connections.csv')
    credit=read('reports/revision6/domain_6_market_links.csv')
    linked={(x.destination_tx,int(x.deposit_native_transfer_log)) for x in credit.itertuples() if x.linked_market_supply=='True'}
    keys=market.block.to_numpy(dtype='int64')*1000000+market.log_index.to_numpy(dtype='int64')
    assert market.log_index.max()<1000000
    entries=[]
    for x in connections.itertuples():
        target=int(x.block)*1000000+int(x.log_index)
        i=int(np.searchsorted(keys,target,side='right'))-1
        assert i>=0
        islinked=(x.tx,int(x.native_transfer_log)) in linked
        entries.append({**x._asdict(),'common_market_cash_at_deposit_micro':str(int(market.cash_after_micro.iloc[i])),
          'common_market_last_event_block':int(market.block.iloc[i]),'common_market_last_event_log':int(market.log_index.iloc[i]),
          'verified_same_tx_common_market_supply':islinked})
    assert sum(x['verified_same_tx_common_market_supply'] for x in entries)==92
    cs('vault_entry_joint_records.csv',entries)
    vault=pd.read_parquet(ROOT/'reports/revision5/vault_economic_events.parquet')
    flows=read('reports/revision21/daily_flow_stock_reconciliation.csv').set_index('date')
    actual=[date for date,r in flows.iterrows() if 100*int(r.withdraw_micro)>25*int(r.prior_claim_micro)]
    assert actual==DATES
    states=read('reports/revision6/withdrawal_capacity.csv').set_index('date')
    liquidity=read('reports/revision5/market_liquidity_validation.csv').set_index('timestamp')
    details=[];sums=[];unmatched=[]
    for date in DATES:
        g=market[market.date.eq(date)].copy();assert len(g)>0
        prior=(pd.Timestamp(date)-pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        opening=int(g.cash_before_micro.iloc[0]);closing=int(g.cash_after_micro.iloc[-1])
        assert opening==int(liquidity.loc[states.loc[prior,'boundary_timestamp'],'reconstructed_liquidity_raw'])
        assert closing==int(liquidity.loc[states.loc[date,'boundary_timestamp'],'reconstructed_liquidity_raw'])
        own=vault[vault.date.eq(date)&vault.onBehalf.eq(PROXY)&vault.type.isin(['Deposit','Withdraw'])]
        ownwd={tx:int(x.assets_raw.sum()) for tx,x in own[own.type.eq('Withdraw')].groupby('tx')}
        owndep={tx:int(x.assets_raw.sum()) for tx,x in own[own.type.eq('Deposit')].groupby('tx')}
        vm=g[g.position_owner.eq(VAULT)]
        marketwd={tx:int(x.assets_raw.sum()) for tx,x in vm[vm.type.eq('Withdraw')].groupby('tx')}
        marketdep={tx:int(x.assets_raw.sum()) for tx,x in vm[vm.type.eq('Supply')].groupby('tx')}
        # Match only exact amounts with no other beneficiary's same-action vault event.
        other=vault[vault.date.eq(date)&~vault.onBehalf.eq(PROXY)&vault.type.isin(['Deposit','Withdraw'])]
        ambiguous_wd=set(other.loc[other.type.eq('Withdraw'),'tx'])
        ambiguous_dep=set(other.loc[other.type.eq('Deposit'),'tx'])
        matches={tx for tx,a in ownwd.items() if tx not in ambiguous_wd and marketwd.get(tx)==a}
        depmatches={tx for tx,a in owndep.items() if tx not in ambiguous_dep and marketdep.get(tx)==a}
        for tx,a in ownwd.items():
            if tx not in matches:unmatched.append({'date':date,'tx':tx,'account_withdraw_micro':str(a),
                'common_market_vault_withdraw_micro':str(marketwd.get(tx,0)),'other_beneficiary_same_tx':tx in ambiguous_wd})
        repl=0;outflow=0;daydetails=[]
        for x in g.itertuples():
            positive=x.type in ['Supply','Repay','Liquidation']
            isfocal=x.type=='Withdraw' and x.position_owner==VAULT and x.tx in matches
            row={'date':date,'timestamp':int(x.timestamp),'block':int(x.block),'tx':x.tx,'log_index':int(x.log_index),
              'type':x.type,'position_owner':x.position_owner,'assets_micro':str(int(x.assets_raw)),
              'cash_before_micro':str(int(x.cash_before_micro)),'cash_after_micro':str(int(x.cash_after_micro)),
              'earlier_positive_cash_flows_micro':str(repl),'earlier_negative_cash_flows_micro':str(outflow),
              'cash_before_without_earlier_inflows_micro':str(opening-outflow),
              'matched_account_withdrawal':isfocal,'matched_account_deposit':x.type=='Supply' and x.position_owner==VAULT and x.tx in depmatches}
            if positive:repl+=int(x.assets_raw)
            else:outflow+=int(x.assets_raw)
            daydetails.append(row)
        details.extend(daydetails)
        totals={t:int(g.loc[g.type.eq(t),'assets_raw'].sum()) for t in ['Supply','Withdraw','Borrow','Repay','Liquidation']}
        assert opening+totals['Supply']+totals['Repay']+totals['Liquidation']-totals['Withdraw']-totals['Borrow']==closing
        focal=[x for x in daydetails if x['matched_account_withdrawal']]
        assert focal
        joined=sum(ownwd[tx] for tx in matches)
        sumrow={'date':date,'market_events':len(g),'opening_market_cash_micro':str(opening),'closing_market_cash_micro':str(closing),
           'account_claim_prior_micro':states.loc[prior,'claim_micro'],'account_capacity_prior_micro':states.loc[prior,'max_withdraw_micro'],
           'account_capacity_close_micro':states.loc[date,'max_withdraw_micro'],'account_claim_close_micro':states.loc[date,'claim_micro'],
           'account_deposit_micro':str(sum(owndep.values())),'account_withdraw_micro':str(sum(ownwd.values())),
           'account_withdraw_transactions':len(ownwd),'common_matched_transactions':len(matches),'common_matched_withdraw_micro':str(joined),
           'unmatched_account_withdraw_micro':str(sum(ownwd.values())-joined),
           'common_matched_deposit_micro':str(sum(owndep[t] for t in depmatches)),
           'matched_gross_withdraw_above_opening_cash_micro':str(max(0,joined-opening)),
           'matched_market_withdraw_events':len(focal),
           'matched_events_exceed_opening_cash_less_prior_outflows':sum(int(x['assets_micro'])>int(x['cash_before_without_earlier_inflows_micro']) for x in focal),
           'pre_matched_withdraw_cash_million':stats(int(x['cash_before_micro'])/1e12 for x in focal),
           **{t.lower()+'_micro':str(a) for t,a in totals.items()}}
        assert int(flows.loc[date,'withdraw_micro'])==sum(ownwd.values())
        sums.append(sumrow)
    cs('large_withdrawal_day_market_sequence.csv',details)
    cs('large_withdrawal_unmatched_transactions.csv',unmatched)
    cs('large_withdrawal_day_summary.csv',[{k:v for k,v in x.items() if not isinstance(v,dict)} for x in sums])
    save('large_withdrawal_days.json',{'dates':DATES,'summary':sums,'matched_account_withdraw_micro':str(sum(int(x['common_matched_withdraw_micro']) for x in sums)),
       'all_account_withdraw_micro':str(sum(int(x['account_withdraw_micro']) for x in sums)),
       'unmatched_transactions':len(unmatched),'market_events':len(details),
       'scope':'Common-market realized cash ledger; pooled replenishment, not wallet balances, isolated cohort cash, exact historical maxWithdraw per transaction, or causal counterfactual.'})
    return sums

def main():
    OUT.mkdir(exist_ok=True)
    paths=['reports/revision6/domain_6_operations.csv','reports/revision6/domain_6_first_disposition_manifest.json',
      'reports/revision6/domain_6_matches.csv','reports/revision6/withdrawal_capacity.csv','reports/revision18/funded_positions.csv',
      'reports/revision5/market_economic_events.parquet','reports/revision5/vault_economic_events.parquet',
      'reports/revision5/market_liquidity_validation.csv','reports/revision21/daily_flow_stock_reconciliation.csv',
      'reports/revision21/cohort_vault_event_join.csv','reports/revision21/shared_cash_weekly.csv','reports/revision22/ANALYSIS_PLAN.md']
    save('input_manifest.json',{x:{'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest(),'bytes':(ROOT/x).stat().st_size} for x in paths})
    f=funding();print('Funding',json.dumps(f),flush=True)
    s=shared_cash();print('Shared cash',json.dumps(s),flush=True)
    days=intraday();print('Eight days',json.dumps(days),flush=True)
    save('analysis_validation.json',{'status':'PASS','deposit_event_bounds':231,'vault_event_state_connections':94,
      'large_withdrawal_days':len(days),'market_decomposition_dates':46,'gauntlet_excluded':True,
      'new_regressions':0,'exact_transaction_contract_capacity_identified':False})
if __name__=='__main__':main()
