"""Exploratory gross withdrawals: fixed clock-hour shocks and matched random hours."""
from pathlib import Path
import gzip,json
import numpy as np
import pandas as pd
from scipy import stats
from settings import OUT,ADD,R
from statistics_common import cluster_cov


def flow_inputs():
    dest=OUT/'data/withdrawal_hourly_flows.parquet'
    if dest.exists():return pd.read_parquet(dest)
    base=pd.read_parquet(R/'additional_evidence/panel_evidence/raw/vault_committed_flows.parquet')
    base=base[base.event.eq('Withdraw')].copy()
    anchor=pd.read_csv(ADD/'daily.csv').iloc[0]
    base['timestamp']=int(anchor.timestamp)+2*(base.block-int(anchor.block))
    base['chain']=8453
    base=base[['chain','vault','timestamp','assets_raw']].rename(columns={'assets_raw':'withdraw_micro'})
    # Native ERC4626 Withdraw logs also cover redeem calls. Keep each committed log once.
    raw=R.parent/'addon_stress_refill/out/portal_raw'
    rows=[];seen=set()
    for path in raw.glob('*.json.gz'):
        z=json.load(gzip.open(path,'rt'))
        if z['chain']!=1:continue
        for packet in z['rows']:
            txs={t['transactionIndex']:t['hash'] for t in packet.get('transactions',[])}
            for log in packet.get('logs',[]):
                tx=log.get('transactionHash') or txs[log['transactionIndex']]
                key=(tx,log['logIndex'])
                if key in seen:continue
                seen.add(key)
                # The archived portal query requested committed native-vault withdrawal logs.
                rows.append(dict(chain=1,vault=log['address'].lower(),timestamp=int(packet['header']['timestamp']),
                                 withdraw_micro=int(log['data'][2:66],16)))
    eth=pd.DataFrame(rows)
    all_=pd.concat([base,eth],ignore_index=True)
    all_['hour']=(all_.timestamp//3600)*3600
    result=all_.groupby(['chain','vault','hour'],as_index=False).withdraw_micro.sum()
    result.to_parquet(dest,index=False)
    return result


def run():
    flows=flow_inputs()
    rng=np.random.default_rng(20261018)
    rows=[];events=[];coverage=[]
    for chain in [8453,1]:
        states=pd.read_parquet(ADD/f'hourly_vaults_{chain}.parquet')
        positions=pd.read_parquet(ADD/f'hourly_positions_{chain}.parquet')
        states=states[states.assets.gt(0)].copy()
        states['hour']=(pd.to_datetime(states.utc,utc=True).astype('int64')//10**9).astype(np.int64)
        # Reject any purported pre-hour state whose block was actually after the hour.
        states=states[states.timestamp.lt(states.hour)].copy()
        positions=positions[positions.position.gt(0)].copy()
        positions['hour']=(pd.to_datetime(positions.utc,utc=True).astype('int64')//10**9).astype(np.int64)
        scopes=states.vault.unique()
        f=flows[flows.chain.eq(chain)&flows.vault.isin(scopes)]
        flowmap=f.set_index(['vault','hour']).withdraw_micro.to_dict()
        # Prefix sums over the complete observed withdrawal log coverage, including gaps between state windows.
        series={}
        for vault,g in f.groupby('vault'):
            g=g.sort_values('hour');series[vault]=(g.hour.to_numpy(),np.r_[0,g.withdraw_micro.cumsum().to_numpy()])
        def cum(vault,lo,hi):
            if vault not in series:return 0
            t,c=series[vault]
            return int(c[np.searchsorted(t,hi,side='left')]-c[np.searchsorted(t,lo,side='left')])
        state_by_hour={int(k):g.set_index('vault') for k,g in states.groupby('hour')}
        pos_by_hour={int(k):g for k,g in positions.groupby('hour')}
        states['gross_hour_micro']=[flowmap.get((r.vault,int(r.hour)),0) for r in states.itertuples()]
        states['fraction']=states.gross_hour_micro/states.assets
        end=int(pd.Timestamp('2025-11-22',tz='UTC').timestamp()) if chain==1 else int(pd.Timestamp('2026-03-31',tz='UTC').timestamp())
        fractions=states.set_index(['vault','hour']).fraction.to_dict()
        for threshold in [.02,.05,.10]:
            shock=states[states.fraction.ge(threshold)].sort_values(['hour','vault'])
            print('Withdrawal events',chain,threshold,len(shock),flush=True)
            coverage.append(dict(chain=chain,threshold=threshold,events=len(shock),vaults=states.vault.nunique(),
                scope='ten fixed Base vaults only' if chain==8453 else 'all positive-asset native-USDC V1 Ethereum vaults in the hourly windows',
                full_Base_universe_available=False if chain==8453 else True,
                state_hours=states.hour.nunique(),state_start=states.utc.min(),state_end=states.utc.max()))
            pairs=[]
            for number,r in enumerate(shock.itertuples()):
                hour=int(r.hour);window=1 if hour<int(pd.Timestamp('2025-10-18',tz='UTC').timestamp()) else 2
                candidates=states[states.vault.eq(r.vault)&states.fraction.lt(.02)&states.hour.le(end-73*3600)]
                candidates=candidates[candidates.hour.lt(int(pd.Timestamp('2025-10-18',tz='UTC').timestamp()))] if window==1 else candidates[candidates.hour.ge(int(pd.Timestamp('2025-10-27',tz='UTC').timestamp()))]
                if candidates.empty:continue
                placebo=int(rng.choice(candidates.hour.to_numpy()))
                pre=state_by_hour[hour];pre_p=state_by_hour[placebo]
                receivers=(set(pre.index)&set(pre_p.index))-{r.vault}
                event_id=f'{chain}:{threshold}:{r.vault}:{hour}'
                events.append(dict(event_id=event_id,chain=chain,threshold=threshold,vault=r.vault,hour=hour,
                                   gross_withdraw_micro=r.gross_hour_micro,pre_assets_micro=r.assets,fraction=r.fraction,placebo_hour=placebo,matched_receivers=len(receivers)))
                for label,t in [('event',hour),('placebo',placebo)]:
                    sp=pos_by_hour[t]
                    source=set(sp.loc[sp.vault.eq(r.vault),'market'])
                    total=sp.groupby('vault').position.sum()
                    shared=sp[sp.market.isin(source)].groupby('vault').position.sum()
                    for vault in receivers:
                        exposure=float(shared.get(vault,0)/total[vault]) if vault in total.index and total[vault]>0 else 0.
                        asset=int(state_by_hour[t].loc[vault,'assets'])
                        for h in [1,6,24,72]:
                            # Follow-up begins after the trigger hour, not at its first withdrawal.
                            lo=t+3600;hi=lo+h*3600
                            if hi>end:continue
                            amount=cum(vault,lo,hi)
                            pairs.append(dict(event_id=label+':'+event_id,matched_event=event_id,kind=label,chain=chain,threshold=threshold,
                                h=h,calendar_date=pd.Timestamp(t,unit='s',tz='UTC').strftime('%Y-%m-%d'),
                                receiver=vault,source_vault=r.vault,shared=int(exposure>0),exposure_share=exposure,
                                receiver_pre_assets_micro=asset,withdraw_micro=amount,withdraw_share=amount/asset))
                if number%100==0:print('Spillover checkpoint',chain,threshold,number,flush=True)
            pair=pd.DataFrame(pairs)
            pair.to_parquet(OUT/f'data/withdrawal_pairs_{chain}_{int(threshold*100)}.parquet',index=False)
            if pair.empty:continue
            for (kind,h),g in pair.groupby(['kind','h']):
              g=g.copy();g['withdraw_million']=g.withdraw_micro/1e12
              for outcome in ['withdraw_million','withdraw_share']:
                for exposure in ['shared','exposure_share']:
                    xy=g[[outcome,exposure]].copy()
                    xy-=xy.groupby(g.event_id).transform('mean')
                    y=xy.iloc[:,0].to_numpy();x=xy.iloc[:,1].to_numpy()[:,None]
                    if np.linalg.norm(x)<1e-12 or g.calendar_date.nunique()<2:
                        rows.append(dict(chain=chain,threshold=threshold,h=h,kind=kind,exposure=exposure,outcome=outcome,status='not identified: no within-event exposure variation or fewer than two event-date clusters'))
                        continue
                    bread=np.linalg.inv(x.T@x);beta=float((bread@x.T@y)[0]);resid=y-x[:,0]*beta
                    rank=g.event_id.nunique()+1
                    cv=cluster_cov(x*resid[:,None],bread,[g.calendar_date],rank)
                    se=np.sqrt(cv[0,0]) if cv[0,0]>0 else np.nan
                    t=beta/se;df=g.calendar_date.nunique()-1
                    rows.append(dict(chain=chain,threshold=threshold,h=h,kind=kind,exposure=exposure,outcome=outcome,
                        coefficient=beta,se=se,t=t,p=2*stats.t.sf(abs(t),df),N=len(g),events=g.event_id.nunique(),date_clusters=g.calendar_date.nunique(),
                        within_R2=1-resid@resid/(y@y) if y@y else np.nan,outcome_mean=g[outcome].mean(),status='estimated'))
            pd.DataFrame(rows).to_csv(OUT/'tables/withdrawal_spillover_estimates.csv',index=False)
            pd.DataFrame(events).to_csv(OUT/'data/large_withdrawal_events.csv',index=False)
    pd.DataFrame(coverage).to_csv(OUT/'tables/withdrawal_scope_coverage.csv',index=False)
    notes=dict(status='partial scope, exploratory',
        primary_definition='gross committed ERC4626 Withdraw logs in a fixed UTC clock hour >=5% of pre-hour totalAssets; also 2/10%; redeem emits the same event',
        followup='other-vault gross withdrawal over next1/6/24/72h after the shock hour, divided by receiver pre-hour assets',
        exposure='share of receiver positive positions in source-vault markets at the pre-hour state; separate binary shared indicator',
        placebo='one fixed-seed random hour without a >=2% source withdrawal in same W1/W2 state window, same source and paired common receiver vaults',
        FE='event effects; event date effects nest exactly inside event effects and are absorbed rather than counted twice',
        covariance='cluster by actual event date (placebo uses placebo date)',
        seed=20261018,
        gaps=['Base hourly all-vault positions/totalAssets not archived; Base result covers only the fixed ten-vault cohort, not all162 vaults.',
              'Ethereum pre-hour states cover only W1/W2 plus prior7d, not the full439-day interval.',
              'Fixed clock-hour aggregation is used, not every possible sliding60-minute window.',
              'A paired receiver must have a positive-asset snapshot at both event and placebo hours.'])
    (OUT/'logs/step3_status.json').write_text(json.dumps(notes,indent=2))
    print('Step3 complete, explicit limited scopes retained',flush=True)


if __name__=='__main__':run()
