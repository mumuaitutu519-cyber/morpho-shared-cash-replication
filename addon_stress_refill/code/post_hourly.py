import os,json
import numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats
from hourly import H,A,R,state,collect,rpc,morpho,sel,batches
O=A/'out';os.environ['MPLCONFIGDIR']=str(A/'work/mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def rebuild(chain):
    br=json.loads((H/f'blocks_{chain}.json').read_text());assert len(br)==1008;pd.DataFrame(br).to_csv(O/f'hourly_blocks_{chain}.csv',index=False)
    pp=[];vv=[];mm=[];dd=[]
    for r in br:
        path=H/f"{chain}_{r['target']}.json";assert path.exists(),str(path)
        z=json.loads(path.read_text());assert z['block']==r['block'] and z['block_hash']==r['hash'] and z['timestamp']==r['timestamp'] and z['chain']==chain
        markets,vaults,positions=state(z);assert all(abs(v['gap'])<=1 for v in vaults)
        p=pd.DataFrame(positions);v=pd.DataFrame(vaults);v=v[v.assets.gt(0)];p=p[p.vault.isin(v.vault)]
        mt=p.groupby('market').agg(P=('position','sum'),cash=('cash','first'))
        S=sum(min(int(x.position),int(x.cash)) for x in p.itertuples());J=sum(min(int(x.P),int(x.cash)) for x in mt.itertuples());assets=sum(int(a) for a in v.assets)
        assert J<=z['morpho_token_balance']+1
        for idx,row in v.iterrows():
            g=p[p.vault.eq(row.vault)];ownS=int(row.capacity);increment=sum(min(int(mt.loc[x.market,'P']),int(x.cash))-min(int(mt.loc[x.market,'P'])-int(x.position),int(x.cash)) for x in g.itertuples())
            v.loc[idx,'D']=(ownS-increment)/ownS if ownS else np.nan;v.loc[idx,'capacity_assets']=ownS/int(row.assets)
        stamp=r['utc'];dd.append(dict(chain=chain,utc=stamp,block=r['block'],target=r['target'],timestamp=r['timestamp'],distance_seconds=r['distance_seconds'],Vaults=len(v),assets=assets,S=S,J=J,Dup=(S-J)/S if S else np.nan,JA=J/assets if assets else np.nan))
        pp.append(p.assign(chain=chain,utc=stamp));vv.append(v.assign(chain=chain,utc=stamp));mm.extend(dict(chain=chain,utc=stamp,block=r['block'],target=r['target'],market=m,cash=x['cash']) for m,x in markets.items())
    p=pd.concat(pp,ignore_index=True);v=pd.concat(vv,ignore_index=True);m=pd.DataFrame(mm);d=pd.DataFrame(dd)
    p.to_parquet(O/f'hourly_positions_{chain}.parquet',index=False);v.to_parquet(O/f'hourly_vaults_{chain}.parquet',index=False);m.to_parquet(O/f'hourly_markets_{chain}.parquet',index=False);d.to_csv(O/f'hourly_daily_{chain}.csv',index=False)
    return p,v,m,d

def cash_gate(chain,p,m):
    active=set(p.loc[p.position.gt(0),'market']);m=m[m.market.isin(active)]
    if chain==8453:
        ledger=pd.read_parquet(R/'additional_evidence/panel_evidence/raw/market_operations.parquet');ledger['cash_delta_micro']=ledger.assets_micro.where(ledger.kind.isin(['Supply','Repay','Liquidation']),-ledger.assets_micro)
        covered=set(json.loads((R/'additional_evidence/panel_evidence/raw/operation_query.json').read_text())['markets']);assert active<=covered,('extra positive hourly markets require ledger',active-covered)
        c0=json.loads((R/'additional_evidence/panel_evidence/raw/opening_market_cash.json').read_text());checks=[]
        for market,g in ledger.groupby('market'):
            if market not in active:continue
            g=g.sort_values(['block','log_index']);b=g.block.to_numpy();balances=g.cash_delta_micro.cumsum().to_numpy()+int(c0[market])
            for r in m[m.market.eq(market)].itertuples():
                idx=np.searchsorted(b,r.block,side='right')-1;cash=int(balances[idx]) if idx>=0 else int(c0[market]);checks.append(dict(chain=chain,utc=r.utc,market=market,ledger_cash=cash,observed_cash=r.cash,gap=cash-r.cash))
    else:
        covered=set(json.loads((O/f'hourly_ledger_markets_{chain}.json').read_text()));assert active<=covered,('hourly market universe expanded; recollect ledger',active-covered)
        ledger=pd.read_parquet(O/f'hourly_ledger_{chain}.parquet');checks=[]
        for start,end in [('2025-10-02','2025-10-18'),('2025-10-27','2025-11-22')]:
            z=m[m.utc.ge(start)&m.utc.lt(end)];first=int(z.block.min());mids=sorted(z.market.unique());a=batches(chain,[(first,[(morpho(chain),sel('market(bytes32)')+mid[2:]) for mid in mids])])[0];opening={mid:x[0]-x[2] for mid,x in zip(mids,a)}
            ld=ledger[ledger.block.gt(first)&ledger.block.le(z.block.max())]
            for market,h in z.groupby('market'):
                g=ld[ld.market.eq(market)].sort_values(['block','log_index']);bs=g.block.to_numpy();bal=g.cash_delta_micro.cumsum().to_numpy()+int(opening[market])
                for r in h.itertuples():
                    idx=np.searchsorted(bs,r.block,side='right')-1;cash=int(bal[idx]) if idx>=0 else int(opening[market]);checks.append(dict(chain=chain,utc=r.utc,market=market,ledger_cash=cash,observed_cash=r.cash,gap=cash-r.cash))
    q=pd.DataFrame(checks);q.to_csv(O/f'hourly_cash_gate_{chain}.csv',index=False);assert q.gap.abs().max()<=1,(chain,q.gap.abs().max(),q.loc[q.gap.abs().idxmax()].to_dict())
    return int(q.gap.abs().max())

def a2(d):
    rows=[];names={8453:'Base',1:'Ethereum',42161:'Arbitrum'}
    plt.rcParams.update({'font.family':'serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    for chain,g in d.groupby('chain'):
        fig,axes=plt.subplots(2,2,figsize=(8,4.8),sharex='col',sharey='row')
        for column,(window,start,end) in enumerate([('W1','2025-10-09','2025-10-18'),('W2','2025-11-03','2025-11-22')]):
            start=pd.Timestamp(start,tz='UTC');end=pd.Timestamp(end,tz='UTC');x=g[pd.to_datetime(g.utc).between(start-pd.Timedelta(days=7),end-pd.Timedelta(hours=1))].copy();x['time']=pd.to_datetime(x.utc)
            before=x[x.time.lt(start)];event=x[x.time.ge(start)];baseline=before.JA.median();trough=event.loc[event.JA.idxmin()];later=x[x.time.ge(trough.time)&x.JA.ge(baseline)];recovered=not later.empty;hours=(int(later.timestamp.iloc[0])-int(trough.timestamp))/3600 if recovered else np.nan
            rows.append(dict(chain=chain,window=window,hours=len(x),baseline_JA=baseline,min_JA=trough.JA,min_time=pd.Timestamp(trough.timestamp,unit='s',tz='UTC').isoformat(),min_grid_time=trough.utc,min_block=int(trough.block),recovery_hours=hours,recovery_observed=recovered,last_observed=pd.Timestamp(x.timestamp.iloc[-1],unit='s',tz='UTC').isoformat(),hours_observed_after_min=(int(x.timestamp.iloc[-1])-int(trough.timestamp))/3600))
            axes[0,column].plot(x.time,100*x.Dup,color='#2166ac',lw=1.2);axes[1,column].plot(x.time,100*x.JA,color='#b2182b',lw=1.2);axes[1,column].axhline(100*baseline,color='#555555',ls='--',lw=.8,label='Prior 7-day median');axes[0,column].set_title(window)
            dates=[t for t in pd.date_range(x.time.iloc[0].normalize(),x.time.iloc[-1].normalize(),freq='5D' if window=='W1' else '7D') if x.time.iloc[-1]-t>=pd.Timedelta(days=3)]+[x.time.iloc[-1]]
            for ax in axes[:,column]:ax.axvline(start,color='black',lw=.8);ax.grid(axis='y',alpha=.2);ax.set_xticks(dates);ax.set_xlim(x.time.iloc[0],x.time.iloc[-1]);ax.set_xticklabels([t.strftime('%b %d') for t in dates])
            axes[1,column].set_xlabel('UTC');axes[1,column].legend(frameon=False,loc='best',fontsize=9)
        axes[0,0].set_ylabel('Dup (%)');axes[1,0].set_ylabel('J / assets (%)');fig.suptitle(names[chain]);fig.tight_layout();fig.savefig(O/f'Figure_A2_{names[chain]}.png',dpi=220);fig.savefig(O/f'Figure_A2_{names[chain]}.pdf');plt.close(fig)
    pd.DataFrame(rows).to_csv(O/'A2_trough_recovery.csv',index=False)

def demean(values,vault,time):
    y=values.copy().astype(float)
    for _ in range(1000):
        old=y.copy()
        for g in [vault,time]:
            unique=np.unique(g)
            for k in unique:y[g==k]-=y[g==k].mean(axis=0)
        if np.max(abs(y-old))<1e-12:return y
    raise RuntimeError('fixed effect projection failed')

def a3():
    tokens=pd.read_csv(O/'collateral_symbols.csv');tokens['related']=tokens.symbol.fillna('').isin(['xUSD','deUSD','sdeUSD'])|tokens.symbol.fillna('').str.startswith(('PT-sw-xUSD','PT-sdeUSD'));tokens['core']=tokens.symbol.fillna('').isin(['xUSD','deUSD','sdeUSD']);tokens[tokens.related].to_csv(O/'A3_related_token_list.csv',index=False)
    rows=[];status=[];groups=[];panels=[];changes=[];related_markets=[];eligibility=[]
    for chain in [1,42161]:
        br=json.loads((H/f'blocks_{chain}.json').read_text());r=next(r for r in br if r['utc']=='2025-11-03T00:00:00+00:00');b=r['pre_boundary_block'];h=rpc(chain,'eth_getBlockByNumber',[hex(b),False]);rr=dict(utc='pre_W2',target=r['target']-1,block=b,timestamp=int(h['timestamp'],16),hash=h['hash']);collect(chain,[rr]);z=json.loads((H/f"{chain}_{rr['target']}.json").read_text());_,vs,ps=state(z);pre=pd.DataFrame(ps);pv=pd.DataFrame(vs);pv=pv[pv.assets.gt(0)];pre=pre[pre.vault.isin(pv.vault)]
        assert pv.gap.abs().max()<=1
        first=next(x['block'] for x in br if x['utc']=='2025-10-27T00:00:00+00:00');mids0=sorted(set(pre.loc[pre.position.gt(0),'market']));ledger=pd.read_parquet(O/f'hourly_ledger_{chain}.parquet');covered=set(json.loads((O/f'hourly_ledger_markets_{chain}.json').read_text()));assert set(mids0)<=covered
        opening=batches(chain,[(first,[(morpho(chain),sel('market(bytes32)')+m[2:]) for m in mids0])])[0];cashchecks=[]
        for market,a in zip(mids0,opening):
            observed=int(z['market'][market]['state'][0])-int(z['market'][market]['state'][2]);replayed=int(a[0])-int(a[2])+int(ledger.loc[ledger.market.eq(market)&ledger.block.gt(first)&ledger.block.le(b),'cash_delta_micro'].sum());cashchecks.append(dict(chain=chain,market=market,pre_block=b,opening_block=first,ledger_cash=replayed,observed_cash=observed,gap=replayed-observed))
        pd.DataFrame(cashchecks).to_csv(O/f'A3_pre_cash_gate_{chain}.csv',index=False);assert max(abs(x['gap']) for x in cashchecks)<=1
        universe=dict(z['market'])
        for path in H.glob(f'{chain}_*.json'):universe.update(json.loads(path.read_text())['market'])
        known=set(tokens.loc[tokens.chain.eq(chain),'address'])
        assert {'0x'+f"{a['params'][1]:040x}" for a in universe.values() if a['params'][1]}<=known,'Token list must cover all hourly and pre-W2 collateral contracts'
        p=pd.read_parquet(O/f'hourly_positions_{chain}.parquet');v=pd.read_parquet(O/f'hourly_vaults_{chain}.parquet');p=p[p.utc.ge('2025-10-27')];v=v[v.utc.ge('2025-10-27')]
        for original in vs:eligibility.append(dict(chain=chain,vault=original['vault'],pre_assets=original['assets'],pre_positions=original['positions'],positive_pre_assets=original['assets']>0,pre_block=b))
        for scope,flag in [('main','related'),('core_only','core')]:
            related=set(tokens.loc[tokens.chain.eq(chain)&tokens[flag],'address']);mids={m for m,a in z['market'].items() if ('0x'+f"{a['params'][1]:040x}") in related};hit=set(pre.loc[pre.market.isin(mids)&pre.position.gt(0),'vault']);shared=set(pre.loc[pre.vault.isin(hit)&pre.position.gt(0),'market'])
            for market in sorted(m for m,a in universe.items() if '0x'+f"{a['params'][1]:040x}" in related):
                collateral='0x'+f"{universe[market]['params'][1]:040x}"
                token=tokens[tokens.chain.eq(chain)&tokens.address.eq(collateral)].iloc[0]
                related_markets.append(dict(chain=chain,scope=scope,market=market,collateralToken=collateral,symbol=token.symbol,name=token['name'],pre_block=b,in_pre_queue=market in z['market'],positive_vaults=pre.loc[pre.market.eq(market)&pre.position.gt(0),'vault'].nunique()))
            frozen=[];mt=pre.groupby('market').agg(P=('position','sum'),cash=('cash','first'))
            for address in pv.vault:
                g=pre[pre.vault.eq(address)]
                total=int(g.position.sum());share=int(g.loc[g.market.isin(shared),'position'].sum())/total if total else 0
                initial=pv.set_index('vault').loc[address];stand=int(initial.capacity);marginal=sum(min(int(mt.loc[a.market,'P']),int(a.cash))-min(int(mt.loc[a.market,'P'])-int(a.position),int(a.cash)) for a in g.itertuples())
                frozen.append(dict(chain=chain,scope=scope,vault=address,affected=address in hit,Shared=share,assets=int(initial.assets),pre_D=(stand-marginal)/stand if stand else np.nan,pre_capacity_assets=stand/int(initial.assets)))
            fg=pd.DataFrame(frozen);groups.append(fg);u=v.merge(fg[~fg.affected][['vault','Shared']],on='vault',validate='many_to_one');u['W2']=u.utc.ge('2025-11-03').astype(int);u['interaction']=u.W2*u.Shared;u['scope']=scope;panels.append(u)
            for outcome,initialcol in [('D','pre_D'),('capacity_assets','pre_capacity_assets')]:
                last=u[u.utc.eq(u.utc.max())][['vault',outcome]];end=fg[~fg.affected][['vault',initialcol]].merge(last,on='vault',how='left');end['delta']=end[outcome]-end[initialcol];matched=end.dropna(subset=[initialcol,outcome]);changes.append(dict(chain=chain,scope=scope,outcome=outcome,eligible_vaults=len(end),matched_endpoint_vaults=len(matched),pre_median=matched[initialcol].median(),end_median=matched[outcome].median(),median_change=matched.delta.median()))
            for outcome in ['D','capacity_assets']:
                q=u.dropna(subset=[outcome,'interaction']);vg=q.vault.astype('category').cat.codes.to_numpy();tg=q.utc.astype('category').cat.codes.to_numpy();xy=demean(q[[outcome,'interaction']].to_numpy(),vg,tg);G=q.vault.nunique();identified=np.linalg.matrix_rank(xy[:,1:],tol=1e-10)==1 and G>1
                if identified:
                    model=sm.OLS(xy[:,0],xy[:,1:]).fit(cov_type='cluster',cov_kwds={'groups':vg,'use_correction':True,'df_correction':True},use_t=True);coef=float(model.params[0]);se=float(model.bse[0]);t=coef/se;pv_=2*stats.t.sf(abs(t),G-1)
                    # CR1 correction includes the absorbed vault/time rank.
                    rank=G+q.utc.nunique()-1+1;factor=(len(q)-1)/(len(q)-rank);se=se*np.sqrt(factor);t=coef/se;pv_=2*stats.t.sf(abs(t),G-1)
                    rows.append(dict(chain=chain,scope=scope,outcome=outcome,term='W2_x_Shared',coef=coef,se=se,t=t,p=pv_,N=len(q),Vaults=G))
                status.append(dict(chain=chain,scope=scope,outcome=outcome,affected_vaults=len(hit),unaffected_vaults=fg.loc[~fg.affected,'vault'].nunique(),Vaults=G,N=len(q),undefined_rows=len(u)-len(q),outside_pre_positive_cohort_rows=int((~v.vault.isin(fg.vault)).sum()),pre_zero_asset_vaults=len(vs)-len(pv),identified=identified,cluster_df=G-1))
    pd.concat(groups).to_csv(O/'A3_frozen_groups.csv',index=False);pd.concat(panels).to_parquet(O/'A3_hour_panel.parquet',index=False);pd.DataFrame(rows,columns=['chain','scope','outcome','term','coef','se','t','p','N','Vaults']).to_csv(O/'A3_regressions.csv',index=False);pd.DataFrame(status).to_csv(O/'A3_status.csv',index=False);pd.DataFrame(changes).to_csv(O/'A3_endpoint_changes.csv',index=False);pd.DataFrame(related_markets).to_csv(O/'A3_related_markets.csv',index=False);pd.DataFrame(eligibility).to_csv(O/'A3_baseline_eligibility.csv',index=False)

def bfig():
    plt.rcParams.update({'font.family':'serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    d=pd.read_csv(O/'B1_daily_replay.csv');d=d[d.f.eq(25)&d.order.eq('large_first')];fig,ax=plt.subplots(figsize=(8,3.6));ax.plot(pd.to_datetime(d.date),d.tau,color='#2166ac',lw=1);ax.set_yscale('function',functions=(np.log1p,np.expm1));ax.set_yticks([0,1,6,24,72,168]);ax.set_ylabel('τ 25% (hours; log(1 + τ) scale)');ax.set_xlabel('UTC close date')
    c=d[d.censored];ax.scatter(pd.to_datetime(c.date),c.tau,marker='^',s=12,color='#b2182b',label='Right-censored at 168 h');ax.legend(frameon=False,loc='upper right',bbox_to_anchor=(1,1.14),fontsize=9)
    dates=pd.to_datetime(d.date);ticks=[dates.iloc[0]]+list(pd.date_range('2025-04-01','2026-01-01',freq='QS'))+[dates.iloc[-1]];ax.set_xlim(dates.iloc[0],dates.iloc[-1]);ax.set_xticks(ticks);ax.set_xticklabels([t.strftime('%Y-%m-%d') if i in [0,len(ticks)-1] else t.strftime('%Y-%m') for i,t in enumerate(ticks)])
    for label,(start,end) in zip(['W1','W2'],[('2025-10-09','2025-10-18'),('2025-11-03','2025-11-22')]):ax.axvspan(pd.Timestamp(start),pd.Timestamp(end),color='grey',alpha=.2);ax.text(pd.Timestamp(start)+(pd.Timestamp(end)-pd.Timestamp(start))/2,.65,label,transform=ax.get_xaxis_transform(),ha='center',fontsize=9)
    ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(O/'Figure_B1_tau25.png',dpi=220);fig.savefig(O/'Figure_B1_tau25.pdf');plt.close(fig)

def run():
    dd=[];checks=[]
    for chain in [8453,1,42161]:
        p,v,m,d=rebuild(chain);gap=cash_gate(chain,p,m);dd.append(d);checks.append(dict(chain=chain,hours=len(d),asset_gap_max=int(v.gap.abs().max()),cash_gap_max=gap))
    (O/'hourly_gates.json').write_text(json.dumps(checks,indent=2));a2(pd.concat(dd));a3();bfig()
if __name__=='__main__':run()
