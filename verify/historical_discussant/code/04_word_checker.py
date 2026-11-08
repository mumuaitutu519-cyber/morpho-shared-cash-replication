"""Read-only numerical Word checker for the supplied current Arabic-numbered manuscript."""
import re,json,hashlib
from zipfile import ZipFile
from xml.etree import ElementTree as E
import numpy as np
import pandas as pd
from scipy import stats
from settings import OUT,R,PE,ADD,MANUSCRIPT,PROJECT
from statistics_common import star,cluster_cov


def run():
    before=hashlib.sha256(MANUSCRIPT.read_bytes()).hexdigest()
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with ZipFile(MANUSCRIPT) as z:body=E.fromstring(z.read('word/document.xml')).find('w:body',ns)
    caption='';panel='';tables=[]
    for el in body:
        text=re.sub(r'\s+',' ',' '.join(t.text or '' for t in el.findall('.//w:t',ns))).strip()
        match=re.match(r'Table\s+([A-Z]?\d+)\s*\.',text)
        if match:caption=match.group(1);panel=''
        if text.startswith('Panel '):panel=text.split('.')[0].replace(' ','')
        if el.tag.endswith('}tbl'):
            table=[[''.join(t.text or '' for t in c.findall('.//w:t',ns)).strip() for c in row.findall('w:tc',ns)] for row in el.findall('w:tr',ns)]
            if caption:tables.append(dict(number=caption,panel=panel,rows=table))
    results=[]
    def get(number,panel=''):
        candidates=[t for t in tables if t['number']==number and (not panel or t['panel']==panel)]
        if len(candidates)!=1:raise ValueError((number,panel,len(candidates)))
        return candidates[0]['rows']
    def norm(x):
        x=re.sub(r'\s+','',str(x)).replace(',','').replace('−','-').replace('—','-')
        if re.match(r'^-0\.0+(\**)$',x):x=x[1:]
        return x
    def check(label,paper,computed):
        results.append(dict(item=label,paper=paper,reproduced=computed,pass_check=norm(paper)==norm(computed)))
    def row_cell(table,label,col):
        matches=[(i,r[col]) for i,r in enumerate(table) if r and norm(r[0])==norm(label) and len(r)>col and r[col]]
        if len(matches)!=1:raise ValueError(('Missing/ambiguous Word cell',label,col,matches))
        return matches[0]
    def numeric(table,label,col,value,digits,tag=''):
        i,paper=row_cell(table,label,col)
        check(tag+label+f' column{col//2}',paper,f'{value:.{digits}f}')
    def regression(table,label,col,coef,t,p,tag=''):
        i,paper=row_cell(table,label,col)
        check(tag+label+f' column{col//2} coefficient',paper,f'{coef:.3f}'+star(p))
        check(tag+label+f' column{col//2} statistic',table[i+1][col],f'({t:.2f})')

    # Tables 1,2,5,6: source-defined amounts and exact request accounting.
    cash=pd.read_csv(R/'joint_review/outputs/historical_cash_summary.csv')
    t=get('1')
    for r in cash.itertuples():
        numeric(t,r.scope,2,r.median_duplicate_usdc/1e6,3,'T1 ')
        numeric(t,r.scope,4,r.median_duplication_pct,2,'T1 ')
    cross=pd.read_csv(R/'enrichment/outputs/cross_chain.csv').set_index('chain');t=get('2')
    fields=[('Vaults','positive_block_vaults',1,0),('Markets with positive positions','positive_markets',1,0),
            ('Vault assets, million USDC','assets_usdc',1e-6,3),('Standalone capacity, million USDC','S_usdc',1e-6,3),
            ('Joint cash bound, million USDC','J_usdc',1e-6,3),('Duplicated cash, million USDC','duplicate_usdc',1e-6,3),
            ('Duplication, percent','duplication_pct',1,2),('Observation block','block',1,0)]
    for j,chain in [(2,'Base'),(4,'Ethereum')]:
        r=cross.loc[chain]
        for label,key,mult,digits in fields:numeric(t,label,j,r[key]*mult,digits,'T2 ')
        numeric(t,'Standalone capacity / assets, percent',j,100*r.S_usdc/r.assets_usdc,2,'T2 ')
        numeric(t,'Joint cash bound / assets, percent',j,100*r.J_usdc/r.assets_usdc,2,'T2 ')
        check('T2 observation UTC '+chain,row_cell(t,'Observation time, UTC',j)[1],r.utc)
    requests=pd.read_csv(R/'joint_review/outputs/joint_request_summary.csv').set_index('request_pct');t=get('5')
    for j,f in [(2,5),(4,10),(6,25)]:
        r=requests.loc[f]
        for label,key,mult,digits in [('Historical dates','dates',1,0),('All individual checks pass','all_individual_pass',1,0),
            ('Excluded by joint cash bound','joint_budget_excluded',1,0),('Excluded among passing dates (%)','excluded_pct_of_passed',1,2),
            ('Passing dates not excluded','not_excluded',1,0),('Median deficit, million USDC','median_gap_usdc',1e-6,3),
            ('Maximum deficit, million USDC','max_gap_usdc',1e-6,3),('Excluded among all dates (%)','excluded_pct_all_dates',1,2),
            ('Median deficit / joint request (%)','median_gap_request_pct',1,2)]:
            if pd.isna(r[key]):check('T5 '+label+str(f),row_cell(t,label,j)[1],'-')
            else:numeric(t,label,j,r[key]*mult,digits,'T5 ')
    t=get('6');vault=pd.read_csv(R/'joint_review/outputs/cross_vault_capacity.csv')
    for row in t[1:]:
        name=row[0];alias={'Gauntlet Core':'Gauntlet USDC Core','Gauntlet Prime':'Gauntlet USDC Prime'}.get(name,name)
        v=vault[vault.name.str.contains(alias,regex=False)].iloc[0]
        check('T6 '+name+' unchanged shares',row[2],'Yes' if v.market_shares_unchanged else 'No')
        for j,key in [(4,'before_position_usdc'),(6,'after_position_usdc'),(8,'before_capacity_usdc'),(10,'after_capacity_usdc'),(12,'capacity_change_usdc')]:
            check('T6 '+name+' '+key,row[j],f'{v[key]/1e6:.3f}')
    # Tables 3,4,7,B2: coefficients/statistics from canonical, unrounded archives.
    core=pd.read_csv(R/'outputs/empirical/regressions.csv')
    added=pd.read_csv(R/'additional_evidence/outputs/regressions.csv')
    robust=pd.read_csv(PE/'tasks4_5_numeric.csv')
    t=get('3','PanelA')
    for model,col,variables in [('II_A',2,{'HHI':'L_cash_hhi','Size':'L_log_total_assets','Util':'L_utilization10'}),
                                 ('II_B',6,{'Shared':'shared_exposure','Size':'log_assets','Markets':'active_markets'})]:
        for label,var in variables.items():
            r=core[core.model.eq(model)&core.term.eq(var)].iloc[0];regression(t,label,col,r.coef,r.coef/r.se,r.p,'T3A ')
    for model,spec,col,variables in [('joint_budget','J_assets',4,{'HHI':'L_cash_hhi','Size':'L_log_assets','Util':'L_utilization10','Flow':'L_spark_flow_share'}),
        ('market_duplication','at_least_2_vaults',8,{'Vaults':'vault_count','Util':'utilization10','Cash':'log_cash','Top':'largest_position_supply'})]:
        for label,var in variables.items():
            r=added[added.model.eq(model)&added.spec.eq(spec)&added.variable.eq(var)].iloc[0]
            regression(t,label,col,r.coefficient,r.t_statistic,r.p_value,'T3A ')
    t=get('3','PanelB')
    for spec,col in [('interaction',2),('count_le_median',4),('count_gt_median',6)]:
        g=robust[robust.model.eq('task5')&robust.spec.eq(spec)]
        mapping={'Vaults':'vault_count','Util':'utilization10','Cash':'log_cash','Top':'largest_position_supply','Util × Vaults':'utilization_x_vaults'}
        for label,var in mapping.items():
            r=g[g.variable.eq(var)]
            if r.empty:continue
            r=r.iloc[0];regression(t,label,col,r.coefficient,r.t_statistic,r.p_value,'T3B ')
    cc=pd.read_csv(R/'additional_evidence/cross_chain/outputs/cross_chain_regressions.csv')
    mapping={'Shared':'shared_market_share','Markets':'active_markets','Size':'log_assets','Util':'utilization10','Top':'max_market_share'}
    t=get('4')
    for col,spec in [(2,'a_HC1'),(4,'b_chain_state_FE'),(6,'c_vault_chain_state_FE')]:
        g=cc[cc.spec.eq(spec)]
        for label,var in mapping.items():
            r=g[g.variable.eq(var)].iloc[0];regression(t,label,col,r.coefficient,r.t_statistic,r.p_value,'T4 ')
    t=get('B2')
    for col,spec in [(2,'exclude_1'),(4,'exclude_8453'),(6,'exclude_42161'),(8,'exclude_137'),(10,'two_way_entity_date')]:
        g=robust[robust.model.eq('task4_cross_c')&robust.spec.eq(spec)]
        for label,var in mapping.items():
            r=g[g.variable.eq(var)].iloc[0];regression(t,label,col,r.coefficient,r.t_statistic,r.p_value,'TB2 ')
    t=get('7');task1=pd.read_csv(PE/'task1_numeric.csv')
    for col,spec in [(2,'1a'),(4,'1b')]:
        for label,var in {'Own':'OwnFlow','Peer':'OtherVaultFlow','Outside':'OutsideFlow','Borrow':'BorrowFlow','Peer × Shared':'Peer_x_exposure','Shared':'ExposureShare'}.items():
            q=task1[task1.spec.eq(spec)&task1.variable.eq(var)&task1.covariance.eq('cluster:date')]
            if q.empty:continue
            r=q.iloc[0];regression(t,label,col,r.coefficient,r.t_statistic,r.p_value,'T7 ')
    # Independently recover the reported three-coefficient equality at Shared=1.
    flow=pd.read_parquet(PE/'spillover_panel.parquet')
    terms=['OwnFlow','OtherVaultFlow','OutsideFlow','BorrowFlow','Peer_x_exposure','ExposureShare']
    z=flow.dropna(subset=['dW','vault','date']+terms).copy()
    xy=z[['dW']+terms].astype(float);xy-=xy.groupby(z.vault).transform('mean')
    X=xy.iloc[:,1:].to_numpy();y=xy.iloc[:,0].to_numpy();bread=np.linalg.inv(X.T@X);beta=bread@X.T@y
    cv=cluster_cov(X*(y-X@beta)[:,None],bread,[z.date],z.vault.nunique()+len(terms))
    contrast=np.array([0,1,-1,0,1,0]);p=2*stats.t.sf(abs(contrast@beta/np.sqrt(contrast@cv@contrast)),z.date.nunique()-1)
    numeric(t,'p (Peer = Outside)',4,p,3,'T7 ')
    # Table8: all coefficients, statistics, observations, events and within R2.
    table8=pd.read_csv(OUT/'tables/table8_reestimated_unrounded.csv')
    H=['m1','pre','event','p1','p6','p24','p72','p168'];labels=['-1 hour','Block before','Event block','+1 hour','+6 hours','+24 hours','+72 hours','+168 hours']
    for panel in ['A','B']:
        t=get('8','Panel'+panel)
        for col in [1,2,3,4]:
            g=table8[table8.panel.eq(panel)&table8.column.eq(col)&table8['sample'].eq('main')&table8.covariance.eq('event_original')]
            for h,label in zip(H,labels):
                r=g[g.term.eq(('count_' if col==3 else 'h_')+h)].iloc[0]
                regression(t,label,col*2,r.coefficient,r.t,r.p,'T8'+panel+' ')
            numeric(t,'Obs',col*2,g.N.iloc[0],0,'T8'+panel+' ')
            numeric(t,'Events',col*2,g.events.iloc[0],0,'T8'+panel+' ')
            numeric(t,'R²',col*2,g.within_R2.iloc[0],3,'T8'+panel+' ')
    # Tables9,10,A1,B1: holder states, observed requests, funding bounds and protocol censuses.
    t=get('9','PanelA');holders=pd.read_csv(R/'reports/revision29/holder_before_after_states.csv')
    executions=pd.read_csv(R/'reports/revision29/ethena_fixed_request_execution.csv')
    for row in t[1:]:
        block=int(row[0].split('/')[-1]);g=holders[holders.deposit_block.eq(block)&holders.named_identity.eq('Ethena')]
        before_=g[g.phase.eq('before')].iloc[0];after_=g[g.phase.eq('after')].iloc[0]
        for col,val in [(2,before_.deposit_micro),(4,before_.capacity_micro),(6,after_.capacity_micro)]:
            check('T9A '+str(block)+' '+str(col),row[col],f'{val/1e12:.3f}')
        ee=executions[executions.deposit_block.eq(block)].set_index('phase')
        statuses=['Pass' if ee.loc[phase,'status']=='success' else 'Fail' for phase in ['before','after']]
        check('T9A '+str(block)+' execution',row[8],' / '.join(statuses))
    t=get('9','PanelB');holders=pd.read_csv(R/'reports/revision33/state_comparisons.csv')
    h=holders[holders.phase.eq('after')&holders.unchanged_shares&holders.positive_opening_claim&holders.identity.ne('Spark')]
    gains=pd.read_csv(R/'reports/revision33/capacity_gain_events.csv')
    for col,g in [(2,h),(4,h[h.material_initial_shortfall]),(6,h[~h.material_initial_shortfall])]:
        eligible_pairs=pd.MultiIndex.from_frame(g[['owner','tx']])
        count_clean=int((pd.MultiIndex.from_frame(gains[['owner','tx']]).isin(eligible_pairs)&gains.same_block_other_market_operations.eq(0)).sum())
        values={'Owner-event observations':len(g),'Distinct transactions':g.tx.nunique(),'Distinct peer owners':g.owner.nunique(),
                'Capacity gains above 1 USDC':int(g.material_capacity_gain.sum()),'Full-request threshold crossings':int(g.covered_after_shortfall.sum()),
                'Gains in blocks without other operations':count_clean}
        for label,value in values.items():numeric(t,label,col,value,0,'T9B ')
        numeric(t,'Median capacity gain, USDC',col,g.capacity_change_usdc.median(),3,'T9B ')
    t=get('10','PanelA');scenarios=pd.read_csv(R/'reports/revision21/withdrawal_scenarios.csv').set_index('request_pct')
    successful=json.loads((R/'reports/revision21/successful_withdrawal_summary.json').read_text())
    thresholds={r['pct']:r for r in successful['threshold_exceedances']}
    for row in t[1:]:
        f=int(row[0].replace('%',''));g=scenarios.loc[f]
        check('T10A '+str(f)+' capacity',row[2],str(int(g.capacity_exceeded_days))+'/'+str(int(g.days)))
        check('T10A '+str(f)+' transactions',row[4],str(thresholds[f]['transactions'])+'/'+f'{successful["transactions"]:,}')
        check('T10A '+str(f)+' days',row[6],str(thresholds[f]['days'])+'/'+str(successful['all_days']))
    t=get('10','PanelB');owner=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet')
    owner=owner[~owner.spark&owner.risk_set_incumbent&owner.prior_claim_usdc.ge(1)].copy()
    owner['band']=pd.cut(owner.prior_claim_usdc,[1,100,10000,1e6,np.inf],right=False)
    for row,(_,g) in zip(t[1:],owner.groupby('band',observed=True)):
        for col,val,digits in [(2,len(g),0),(4,g.owner.nunique(),0),(6,100*g.withdraw_any.mean(),2),
                               (8,100*g.deposit_any.mean(),2),(10,int(g.prior_cash_coverage.lt(1-1e-12).sum()),0)]:
            check('T10B '+row[0]+' '+str(col),row[col],f'{val:.{digits}f}')
    t=get('A1');bounds=pd.read_csv(R/'reports/revision24/amount_groups_joint_bounds.csv').set_index('group')
    for row,group in zip(t[1:],['all_vault','point_identified','positive_width','zero_lower']):
        r=bounds.loc[group]
        for col,val,digits in [(2,r.deposits,0),(4,r.deposit_micro/1e12,3),(6,r.deposit_value_pct,2),
                               (8,r.joint_lower_micro/1e12,3),(10,r.joint_upper_micro/1e12,3)]:check('TA1 '+group+' '+str(col),row[col],f'{val:.{digits}f}')
    t=get('B1');crossstates=pd.read_csv(R/'additional_evidence/cross_chain/outputs/vault_state_panel.csv')
    pp=pd.read_parquet(R/'additional_evidence/cross_chain/outputs/position_panel.parquet')
    protocols=pd.read_csv(R/'additional_evidence/outputs/cross_protocol_summary.csv')
    for col,chain,protocol in [(2,42161,None),(4,137,None),(6,1,'Euler_Earn'),(8,137,'Yearn_V3')]:
        if protocol is None:
            g=crossstates[crossstates.chain.eq(chain)];latest=g[g.date.eq('2026-09-29')]
            n=len(latest);assets=latest.assets_micro.sum()/1e12
            markets=pp[pp.chain.eq(chain)&pp.date.eq('2026-09-29')&pp.position.gt(0)].market.nunique()
            rates={date:100*(x.S_micro.sum()-x.J_chain_micro.iloc[0])/x.S_micro.sum() for date,x in g.groupby('date')}
        else:
            g=protocols[protocols.protocol.eq(protocol)]
            latest=g[g.date.eq('2026-09-29')].iloc[0];n=latest.positive_asset_vaults;assets=latest.assets_usdc/1e6;markets=latest.positive_markets
            rates={r.date:100*r.duplication_rate for r in g.itertuples()}
        numeric(t,'Vaults with assets',col,n,0,'TB1 ');numeric(t,'Markets with positions',col,markets,0,'TB1 ');numeric(t,'Assets, million USDC',col,assets,1,'TB1 ')
        for row,date in zip(t[6:],['2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31','2026-09-29']):
            check('TB1 '+date+' '+str(col),row[col],f'{rates[date]:.1f}')
    # Table11: recompute exact group summaries from the 252 qualifying events.
    events=pd.read_csv(ADD/'A4_base_strict_events.csv');t=get('11')
    for row in t[1:]:
        label=row[0]
        if label.startswith('Universal'):g=events[events.vault_name.str.contains('Universal')]
        elif label.startswith('Extrafi'):g=events[events.vault_name.str.contains('Extrafi')]
        elif label.startswith('Other eight'):g=events[events.is_primary.eq(1)&~events.vault_name.str.contains('Universal|Extrafi',regex=True)]
        elif label.startswith('152'):g=events[events.is_primary.eq(0)]
        else:g=events
        for j,value in [(2,len(g)),(4,g.date.nunique()),(6,g.owner.nunique())]:check('T11 '+label+str(j),row[j],str(value))
        for j,key,digits in [(8,'requested_USDC',0),(10,'vault_cash_USDC',0),(12,'wait_hours',1)]:
            gg=g[~g.unresolved] if key=='wait_hours' else g
            check('T11 '+label+' '+key,row[j],f'{gg[key].median():.{digits}f}' if len(gg) else '-')
    # C1 data are the already independently checked compact-package outputs.
    for panel in ['A','B']:
        t=get('C1','Panel'+panel)
        expected=pd.read_csv(PROJECT/f'addon_package/output/Table_C1_Panel_{panel}.csv',dtype=str)
        for i,row in expected.iterrows():
            for j in range(1,len(expected.columns)):
                check(f'C1{panel} row{i+1} col{j}',t[i+1][j*2],row.iloc[j])
    result=pd.DataFrame(results)
    result.to_csv(OUT/'tables/word_numeric_checks.csv',index=False)
    result[~result.pass_check].to_csv(OUT/'tables/word_numeric_differences.csv',index=False)
    assert hashlib.sha256(MANUSCRIPT.read_bytes()).hexdigest()==before
    checked=sorted(set(re.findall(r'^T([A-Z]?\d+)',r['item'])[0] for r in results if re.findall(r'^T([A-Z]?\d+)',r['item']))|{'C1'})
    status={'manuscript':MANUSCRIPT.name,'sha256_before':before,'sha256_after':before,
            'checked_numeric_cells':len(result),'differences':int((~result.pass_check).sum()),
            'checked_tables':checked,'not_fully_numeric_checked':[],
            'scope':'All current numbered tables have mapped numeric checks, including all Table8/C1 coefficient or value cells. Table3/4/7/B2 checks target displayed coefficient/statistic cells; categorical FE labels and every ancillary N/R2 cell outside Table8 are not independently re-estimated here.',
            'legacy_checker':'Original check_manuscript.py hard-codes obsolete paths, Roman table counts and the older input document; this read-only adaptation uses current cell coordinates and pinned unrounded sources instead.',
            'source_document_instructions':'Review comments at the front of the supplied file are treated as source content, not execution instructions.'}
    (OUT/'logs/word_checker_status.json').write_text(json.dumps(status,indent=2))
    print(json.dumps(status,indent=2),flush=True)


if __name__=='__main__':run()
