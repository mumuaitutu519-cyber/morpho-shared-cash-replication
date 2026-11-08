"""Paper-style tables and source-backed prose, from reviewed result files."""
from pathlib import Path
import json,hashlib
import pandas as pd,numpy as np
from docx import Document
from docx.shared import Inches,Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from preflight import A,R,O
REF=Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/Counting_the_same_cash.docx')
def fmt(x,d=2):return '—' if pd.isna(x) else f'{float(x):.{d}f}'
def coef(r):
    stars='***' if r.p<.01 else '**' if r.p<.05 else '*' if r.p<.1 else ''
    return f'{r.coef:.4f}{stars}\n({r.t:.2f})'
def caption(doc,number,title):
    p=doc.add_paragraph(style='Paper Table Caption');p.paragraph_format.keep_with_next=True;p.add_run(number+'. ').bold=True;p.add_run(title)
def note(doc,text):
    p=doc.add_paragraph(style='Paper Table Note');p.add_run('Notes. ').italic=True;p.add_run(text)
def table(doc,headers,rows,widths=None):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False;total=doc.sections[0].page_width-doc.sections[0].left_margin-doc.sections[0].right_margin
    if widths is None:widths=[.36]+[(1-.36)/(len(headers)-1)]*(len(headers)-1)
    for col,fraction in zip(t.columns,widths):col.width=int(total*fraction)
    for c,h in zip(t.rows[0].cells,headers):c.text=str(h)
    for values in rows:
        for c,value in zip(t.add_row().cells,values):c.text=str(value)
    for i,row in enumerate(t.rows):
        for j,c in enumerate(row.cells):
            c.width=int(total*widths[j]);pr=c._tc.get_or_add_tcPr();marg=OxmlElement('w:tcMar')
            for k in ['top','bottom','left','right']:
                e=OxmlElement('w:'+k);e.set(qn('w:w'),'0');e.set(qn('w:type'),'dxa');marg.append(e)
            pr.append(marg);border=OxmlElement('w:tcBorders')
            for edge in ['top','bottom','left','right']:
                e=OxmlElement('w:'+edge);on=(i==0 and edge in ['top','bottom']) or (i==len(t.rows)-1 and edge=='bottom');e.set(qn('w:val'),'single' if on else 'nil');e.set(qn('w:sz'),'8' if i==0 or i==len(t.rows)-1 else '6');e.set(qn('w:color'),'000000');border.append(e)
            pr.append(border)
            for p in c.paragraphs:
                p.style='Paper Table Text';p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0);p.paragraph_format.line_spacing=1;p.paragraph_format.keep_with_next=False
                for r in p.runs:r.font.name='Times New Roman';r.font.size=Pt(12)
        trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
    return t
def page(doc):doc.add_page_break()
def build_doc(allow_incomplete=False):
    if not allow_incomplete:
        assert all((O/f'A4_summary_{c}.csv').exists() for c in [1,42161]),'Full requested call coverage must complete before final document'
        assert len(pd.read_csv(O/'A2_trough_recovery.csv'))==6
        assert len(json.loads((O/'hourly_gates.json').read_text()))==3
    doc=Document(REF)
    for child in list(doc._element.body):
        if child.tag!=qn('w:sectPr'):doc._element.body.remove(child)
    doc.core_properties.title='Stress windows and cash refill times';doc.core_properties.author=''
    a=pd.read_csv(O/'A1_regressions.csv');meta=pd.read_csv(O/'A1_models.csv')
    caption(doc,'Table A1','Stress windows in the Base daily panel')
    for label,spec in [('Panel A. Weekday effects','weekday'),('Panel B. Weekday and year-month effects','year_month')]:
        doc.add_paragraph(label,style='Paper Body No Indent');outcomes=['Dup','JA','Util','excluded','Errors'];rows=[]
        for term in ['W1','W2']:rows.append([term]+[coef(a[(a.spec==spec)&a.outcome.eq(y)&a.term.eq(term)].iloc[0]) for y in outcomes])
        rows.append(['Dates']+['439']*5);rows.append(['R²']+[fmt(meta[meta.spec.eq(spec)&meta.outcome.eq(y)].R2.iloc[0],3) for y in outcomes]);table(doc,['Variable','Dup','JA','Util','Excl','Errors'],rows,[.2]+[.16]*5)
    note(doc,'Ten fixed native USDC V1 vaults; 439 UTC closing states, 16 January 2025–30 March 2026. W1 is 9–17 October 2025 and W2 is 3–21 November 2025, inclusive. Dup = (S − J) / S; JA = J / totalAssets; Util is position-weighted market utilization. Excl equals one when every individual 25% request passes but the aggregate request exceeds J. Errors counts qualifying calls in the ten vaults. Ratios are fractions. Newey–West standard errors use seven daily lags. Parentheses contain t-statistics. ***/**/* denote 1/5/10% significance.')
    page(doc);caption(doc,'Table A2','Stress windows and prior control periods');d=pd.read_csv(O/'A1_descriptives.csv').set_index('period');cols=['W1','W1_control','W2','W2_control'];rows=[]
    for key,label,mult,digits in [('days','Dates',1,0),('Dup','Dup (%)',100,2),('JA','JA (%)',100,2),('Util','Util (%)',100,2),('excluded_median','Median Excl',1,0),('Errors_median','Median daily Errors',1,0),('Errors_total','Total Errors',1,0),('individual_all_pass_days','All individual passes',1,0),('excluded_days','Joint exclusions',1,0),('median_gap_request','Gap / request (%)',100,2)]:rows.append([label]+[fmt(d.loc[c,key]*mult,digits) for c in cols])
    table(doc,['Variable','W1','W1 C','W2','W2 C'],rows)
    note(doc,'Medians use daily observations; totals and date counts are labelled. Each control period covers the preceding 30 UTC days and excludes the other window: W1 C has 30 dates; W2 C has 21 dates after removing W1. Request rows follow the original aggregate-bound criterion. Gap / request is the median among excluded dates; a dash means no such date. Exclusions are conditional on all individual checks passing.')
    if (O/'A2_trough_recovery.csv').exists():
        page(doc);caption(doc,'Table A3','Hourly joint cash bounds');d=pd.read_csv(O/'A2_trough_recovery.csv')
        for chain,name in [(8453,'Base'),(1,'Ethereum'),(42161,'Arbitrum')]:
            doc.add_paragraph(name,style='Paper Body No Indent');g=d[d.chain.eq(chain)].set_index('window');rows=[]
            for key,label,mult,digits in [('hours','Hours',1,0),('baseline_JA','JA before W (%)',100,2),('min_JA','Minimum JA (%)',100,2)]:rows.append([label]+[fmt(g.loc[w,key]*mult,digits) for w in ['W1','W2']])
            rows.append(['UTC minimum']+[str(g.loc[w,'min_time'])[:19].replace('T','\n') for w in ['W1','W2']]);rows.append(['Recovery τ (h)']+[fmt(g.loc[w,'recovery_hours']) if g.loc[w,'recovery_observed'] else 'Not reached' for w in ['W1','W2']]);table(doc,['Variable','W1','W2'],rows,[.5,.25,.25])
        note(doc,'The block closest to each UTC hour is used. Base retains the ten fixed vaults. Ethereum and Arbitrum retain each hour’s positive-asset native USDC V1 vaults, including zero-capacity vaults. JA before W is the median over the preceding seven days. Recovery starts at the window’s JA minimum and ends at the first observed block reaching that median. UTC times are actual block timestamps. Not reached means no recovery by the last sampled block; the recorded observation horizon is in the CSV.')
    if (O/'A3_status.csv').exists():
        page(doc);caption(doc,'Table A4','Shared markets and vaults without direct exposure');reg=pd.read_csv(O/'A3_regressions.csv');status=pd.read_csv(O/'A3_status.csv');columns=[(1,'D'),(1,'capacity_assets'),(42161,'D'),(42161,'capacity_assets')]
        for scope,label in [('main','Panel A. Related collateral tokens'),('core_only','Panel B. xUSD, deUSD and sdeUSD only')]:
            doc.add_paragraph(label,style='Paper Body No Indent');rows=[]
            values=[]
            for c,y in columns:
                z=reg[reg.chain.eq(c)&reg.scope.eq(scope)&reg.outcome.eq(y)];values.append(coef(z.iloc[0]) if len(z) else 'NE')
            rows.append(['W2 × Shared']+values)
            for key,label2 in [('N','Vault-hours'),('Vaults','Vaults'),('affected_vaults','Affected Vaults')]:rows.append([label2]+[fmt(status[status.chain.eq(c)&status.scope.eq(scope)&status.outcome.eq(y)][key].iloc[0],0) for c,y in columns])
            table(doc,['Variable','ETH D','ETH S / assets','ARB D','ARB S / assets'],rows,[.28]+[.18]*4)
        doc.add_paragraph('Panel C. Unaffected vaults before W2 and at its last sampled hour',style='Paper Body No Indent');change=pd.read_csv(O/'A3_endpoint_changes.csv');rows=[]
        for key,label,mult,digits in [('pre_median','Pre-W2 (%)',100,2),('end_median','End-W2 (%)',100,2),('median_change','Median change (pp)',100,2),('matched_endpoint_vaults','Matched Vaults',1,0)]:rows.append([label]+[fmt(change[change.chain.eq(c)&change.scope.eq('main')&change.outcome.eq(y)][key].iloc[0]*mult,digits) for c,y in columns])
        table(doc,['Variable','ETH D','ETH S / assets','ARB D','ARB S / assets'],rows,[.28]+[.18]*4)
        note(doc,'W2 and its preceding seven days form the hourly panel. Affected vaults have a positive position in a related market at the last block before W2. Shared is the frozen pre-W2 position share in markets held by affected vaults. Only unaffected positive-asset vaults at that block enter these models. D is the standalone capacity share that other vaults can exhaust. Vault and UTC-hour effects are absorbed. Standard errors cluster by vault and include the absorbed-effect rank correction; parentheses contain t-statistics. NE means the interaction is absorbed or there are insufficient clusters. Panel A includes two named principal-token derivatives; the full collateral and market list is supplied. Panel C uses matched vaults; its change row is the median of individual changes. Undefined D rows are counted in A3_status.csv. ***/**/* denote 1/5/10% significance.')
    if all((O/f'A4_summary_{c}.csv').exists() for c in [1,42161]):
        page(doc);caption(doc,'Table A5','Qualifying liquidity error calls');all_=pd.concat([pd.read_csv(O/'A4_base.csv')]+[pd.read_csv(O/f'A4_summary_{c}.csv') for c in [1,42161]],ignore_index=True)
        for scope,label in [('strict_claim','Panel A. Exact pre-block equity filter'),('Table11','Panel B. Original Table 11 equity tolerance')]:
            doc.add_paragraph(label,style='Paper Body No Indent');rows=[]
            for r in all_[all_['filter'].eq(scope)].itertuples():rows.append([r.chain,{'W1_control':'W1 C','W2_control':'W2 C'}.get(r.period,r.period),str(r.events),str(r.holders),fmt(r.request_median),fmt(r.completed_share*100),fmt(r.wait_median_hours)])
            table(doc,['Chain','Period','Errors','Holders','r (USDC)','Done (%)','τ (h)'],rows,[.16,.1,.1,.1,.2,.12,.22])
        note(doc,'The windows and controls are as in Table A2. Equity is converted from the holder’s shares at the preceding block and must be at least 100 USDC. Panel A requires request ≤ equity. Panel B preserves the original 1% equity tolerance. Calls merge within holder–vault–UTC hour. Done is the share with a later committed withdrawal in the same vault; τ is the median wait among those events. The follow-up ends on 30 March 2026. No event gives a dash for conditional statistics. Base uses the existing 162-vault scan; the other chains use all discovered native USDC V1 vaults created by W2’s end. Committed withdrawal logs are crosschecked against the trace scan.')
    page(doc);caption(doc,'Table B1','Recorded cash refill times');d=pd.read_csv(O/'B1_descriptives.csv');primary=d[d.order.eq('large_first')].set_index('f');rows=[]
    for key,label,mult,digits in [('days','Dates',1,0),('zero','τ = 0 dates',1,0),('median','Median τ (h)',1,2),('p75','75th percentile τ (h)',1,2),('p90','90th percentile τ (h)',1,2),('within1','Paid within 1 h (%)',100,2),('within6','Paid within 6 h (%)',100,2),('within24','Paid within 24 h (%)',100,2),('censored','Censored dates',1,0)]:rows.append([label]+[('≥ 168' if key in ['median','p75','p90'] and primary.loc[f,key]>=168 else fmt(primary.loc[f,key]*mult,digits)) for f in [10,25]])
    q=pd.read_csv(O/'B1_daily_replay.csv');rows.append(['Paid at 7 days, censored (%)']+[fmt(100*q[q.order.eq('large_first')&q.f.eq(f)&q.censored].paid_fraction.median(),4) for f in [10,25]])
    table(doc,['Variable','10% request','25% request'],rows)
    note(doc,'All 439 dates and ten fixed Base vaults are retained. Requests equal the stated fraction of each vault’s closing totalAssets, rounded down to micro-USDC. Initial market positions and withdrawal queues stay fixed. Vaults withdraw from largest to smallest closing assets. Own operations are removed. Outside supply, repayment and liquidation cash enter as recorded. Outside borrowing and withdrawal are capped at remaining cash. After each inflow, unpaid requests draw cash in queue order. τ is zero for complete initial payment. Runs stop at complete payment or 168 hours. Quantiles use the observed 168-hour cap; a capped quantile is a lower bound on the uncapped value.')
    page(doc);caption(doc,'Table B2','Cash inflow sources before full payment')
    for filename,label in [('B2_sources.csv','Panel A. Completed within seven days'),('B2_sources_observed.csv','Panel B. All observed runs')]:
        doc.add_paragraph(label,style='Paper Body No Indent');s=pd.read_csv(O/filename);s=s[s.order.eq('large_first')];rows=[]
        for key,label2 in [('supply_inflow_micro','Supply'),('repay_inflow_micro','Repay'),('liquidation_inflow_micro','Liq')]:
            rows.append([label2+' Cash (million USDC)']+[fmt(s[s.f.eq(f)&s.source.eq(key)].amount_micro.iloc[0]/1e12,3) for f in [10,25]])
            rows.append([label2+' share (%)']+[fmt(100*s[s.f.eq(f)&s.source.eq(key)].share.iloc[0]) for f in [10,25]])
        rows.append(['Dates']+[str(primary.loc[f,'days']-primary.loc[f,'censored']) if filename=='B2_sources.csv' else '439' for f in [10,25]]);table(doc,['Source','10% request','25% request'],rows)
    note(doc,'Panel A covers the 432 and 269 completed runs. Panel B retains all 439 dates, including cash inflows observed through the 168-hour cutoff on censored dates. Every recorded non-sample cash inflow through completion or the stated cutoff is included; liquidation repayment is separated from ordinary repayment. Initial cash is outside the decomposition. Amounts sum across date-specific runs, so a historical inflow may enter more than one run. Run-level files retain all flows and paid fractions.')
    page(doc);caption(doc,'Table B3','Dup and cash refill time');reg=pd.read_csv(O/'B_regressions.csv');cox=pd.read_csv(O/'B_cox_stratified.csv');rows=[]
    for term,label in [('Dup','Dup'),('Util','Util'),('log_assets','log(assets)'),('W1','W1'),('W2','W2')]:
        values=[]
        for name in ['baseline','windows']:
            z=reg[reg.spec.eq(name)&reg.term.eq(term)];values.append(coef(z.iloc[0]) if len(z) else '—')
        z=cox[cox.term.eq(term)];values.append(coef(z.iloc[0]) if len(z) else '—');rows.append([label]+values)
    rows += [['Year-month','FE','FE','Strata'],['Weekday','FE','FE','FE'],['Dates','439','439','439'],['R²',fmt(reg[reg.spec.eq('baseline')].R2.iloc[0],3),fmt(reg[reg.spec.eq('windows')].R2.iloc[0],3),'—']];table(doc,['Variable','OLS','OLS + W','Cox'],rows)
    note(doc,'OLS uses log(1 + τ25%) with the 168-hour observation cap. Cox uses observed duration and completion status. The original Cox month-dummy fit is retained in the diagnostic files: September 2025 has 30 censored dates and no completions, causing separation. The reported Cox column uses year-month strata with all 439 dates, the same core variables and weekday effects. Exact Efron score contributions account for tied completions. All reported standard errors use seven-lag chronological HAC. Zero durations enter Cox at a common 0.000001 hour. Parentheses contain coefficient-to-standard-error ratios; OLS uses t inference and Cox uses asymptotic normal inference. A negative Cox coefficient means a lower completion rate. ***/**/* denote 1/5/10% significance.')
    page(doc);caption(doc,'Table B4','Vault ordering and validation');rows=[]
    for f in [10,25]:
        g=d[d.f.eq(f)].set_index('order')
        for key,label,digits in [('zero','τ = 0 dates',0),('median','Median τ (h)',2),('censored','Censored dates',0)]:rows.append([str(f)+'% '+label,fmt(g.loc['large_first',key],digits),fmt(g.loc['small_first',key],digits)])
    table(doc,['Variable','Largest first','Smallest first'],rows);doc.add_paragraph('Panel B. Daily initial-payment checks',style='Paper Body No Indent');c=pd.read_csv(O/'B3_summary.csv').set_index('f');jr=pd.read_csv(O/'joint_requests.csv');rows=[]
    for key,label in [('dates','Dates'),('tau_zero','τ = 0'),('reference_zero','Individual pass and R ≤ J'),('mismatch','Different dates')]:rows.append([label]+[fmt(c.loc[f,key],0) for f in [5,10,25]])
    table(doc,['Variable','5%','10%','25%'],rows)
    note(doc,'The 5% request has τ = 0 on 404 dates (92.03%); 26 dates fail an individual check and nine additional dates fail the fixed-order payment. The original 5% aggregate-bound exclusion count is zero, conditional on individual passes. At 25%, the reference intersection has 19 dates and fixed-order payment has 15. Integer max-flow audit finds that three of the four differences are due to ordering; on 11 March 2025, the aggregate bound and individual passes do not imply complete payment under any allocation. B1 uses the fixed closing-asset order throughout. Full daily checks are in the CSV files.')
    doc.save(O/'tables.docx')

def prose():
    a=pd.read_csv(O/'A1_descriptives.csv').set_index('period');r=pd.read_csv(O/'A1_regressions.csv');b=pd.read_csv(O/'B1_descriptives.csv');b=b[b.order.eq('large_first')].set_index('f');reg=pd.read_csv(O/'B_regressions.csv');cx=pd.read_csv(O/'B_cox_stratified.csv');sources=pd.read_csv(O/'B2_sources.csv');sources=sources[sources.order.eq('large_first')&sources.f.eq(25)].set_index('source')
    ja=r[r.spec.eq('year_month')&r.outcome.eq('JA')].set_index('term');du=r[r.spec.eq('year_month')&r.outcome.eq('Dup')].set_index('term');rr=reg[reg.spec.eq('baseline')&reg.term.eq('Dup')].iloc[0];cc=cx[cx.term.eq('Dup')].iloc[0]
    memo=['# 压力窗口与补现时间追加结果',f'1. 对账：4,400 个日度金库状态（含滞后日）、14,520 个市场现金状态及三链小时状态误差均为 0 micro-USDC；57.86%、81/62/76.54% 完全复现。',f'2. Base：W1/W2 的 Dup 中位数 {100*a.loc["W1","Dup"]:.2f}%/{100*a.loc["W2","Dup"]:.2f}%；对照 {100*a.loc["W1_control","Dup"]:.2f}%/{100*a.loc["W2_control","Dup"]:.2f}%。加年-月效应后 Dup 均不显著；JA 分别下降 {-100*ja.loc["W1","coef"]:.3f}/{-100*ja.loc["W2","coef"]:.3f} 个百分点（p={ja.loc["W1","p"]:.3f}/{ja.loc["W2","p"]:.3f}）。']
    if (O/'A2_trough_recovery.csv').exists():
        x=pd.read_csv(O/'A2_trough_recovery.csv');pieces=[]
        for chain,name in [(8453,'Base'),(1,'ETH'),(42161,'ARB')]:
            g=x[x.chain.eq(chain)].set_index('window');pieces.append(name+' '+ '/'.join(f'{100*g.loc[w,"min_JA"]:.2f}%（{fmt(g.loc[w,"recovery_hours"])}h）' if g.loc[w,'recovery_observed'] else f'{100*g.loc[w,"min_JA"]:.2f}%（窗口末未恢复）' for w in ['W1','W2']))
        memo.append('3. 小时 JA 最低值及恢复时间（W1/W2）：'+'；'.join(pieces)+'。')
    if (O/'A3_regressions.csv').exists():
        x=pd.read_csv(O/'A3_regressions.csv');pieces=[]
        for chain,name in [(1,'ETH'),(42161,'ARB')]:
            for outcome,label in [('D','D'),('capacity_assets','S/资产')]:
                g=x[x.chain.eq(chain)&x.scope.eq('main')&x.outcome.eq(outcome)];pieces.append(name+' '+label+(f'系数{g.coef.iloc[0]:.3f}、p={g.p.iloc[0]:.3f}' if len(g) else '交互项不可识别'))
        memo.append('4. 未直接受冲击金库：'+'；'.join(pieces)+'。未见一致的不利共享传导，期末 D 与单独额度/资产的逐金库变化中位数均为 0；两份代币名单结果相同。')
    if all((O/f'A4_summary_{c}.csv').exists() for c in [1,42161]):
        x=pd.concat([pd.read_csv(O/'A4_base.csv')]+[pd.read_csv(O/f'A4_summary_{c}.csv') for c in [1,42161]]);x=x[x['filter'].eq('strict_claim')];pieces=[]
        for name in ['Base','Ethereum','Arbitrum']:
            g=x[x.chain.eq(name)].set_index('period');pieces.append(name+' '+ '/'.join(str(g.loc[w,'events']) for w in ['W1','W1_control','W2','W2_control']))
        memo.append('5. 全金库报错事件数（W1/对照/W2/对照）：'+'；'.join(pieces)+'；持有人、请求、完成率与等待时间见 Table A5。')
    memo += [f'6. 10%/25%：即付清 {int(b.loc[10,"zero"])}/{int(b.loc[25,"zero"])} 日；τ 中位数 {b.loc[10,"median"]:.2f}/{b.loc[25,"median"]:.2f}h；删失 {int(b.loc[10,"censored"])}/{int(b.loc[25,"censored"])} 日。25% 的 24h 付清率 {100*b.loc[25,"within24"]:.2f}%；删失日 7 天末已付比例中位数 93.25%。',f'7. 25% 已完成请求的流入来源：Supply/Repay/Liq 为 {100*sources.loc["supply_inflow_micro","share"]:.2f}/{100*sources.loc["repay_inflow_micro","share"]:.2f}/{100*sources.loc["liquidation_inflow_micro","share"]:.2f}%。',f'8. Dup 的 OLS 系数 {rr.coef:.3f}，p={rr.p:.3f}；分层 Cox 系数 {cc.coef:.3f}，p={cc.p:.3f}。加窗口后 W1 等待反而较短（−0.298，p=0.014），W2 为−0.329（p=0.183）。Util 为8.686（p=0.043），log(资产) 为0.422（p=0.601）。小金库优先时 25% 中位数 132.70h、删失 174 日。', '9. B3：5% 即付清 404/439 日；25% 比原表交集少 4 日，3 日由顺序造成，1 日的汇总上界条件不足以保证付清。按确认保留 B1 并报告差异。']
    (O/'RESULT_MEMO_CN.md').write_text('\n\n'.join(memo)+'\n')
    pressure=f'The sample includes the October and November 2025 stress windows. In Base, median Dup is {100*a.loc["W1","Dup"]:.2f}% in W1 and {100*a.loc["W2","Dup"]:.2f}% in W2. Control medians are {100*a.loc["W1_control","Dup"]:.2f}% and {100*a.loc["W2_control","Dup"]:.2f}%. With year-month and weekday effects, JA falls by {-100*ja.loc["W1","coef"]:.3f} and {-100*ja.loc["W2","coef"]:.3f} percentage points (p = {ja.loc["W1","p"]:.3f} and {ja.loc["W2","p"]:.3f}). The Dup effects are not significant.'
    if (O/'A2_trough_recovery.csv').exists():
        x=pd.read_csv(O/'A2_trough_recovery.csv');x=x[x.chain.eq(8453)].set_index('window')
        allx=pd.read_csv(O/'A2_trough_recovery.csv');w2=allx[allx.window.eq('W2')].set_index('chain')
        pressure+=' In W2, the hourly JA lows are '+', '.join(f'{100*w2.loc[c,"min_JA"]:.2f}%' for c in [8453,1,42161])+' in Base, Ethereum and Arbitrum. Recovery takes '+', '.join(f'{w2.loc[c,"recovery_hours"]:.0f}' for c in [8453,1,42161])+' hours, respectively, for JA to reach its prior seven-day median.'
    for chain,name in [(1,'Ethereum'),(42161,'Arbitrum')]:
        er=pd.read_csv(O/f'A4_summary_{chain}.csv');er=er[er['filter'].eq('strict_claim')].set_index('period');pressure+=f' {name} has {int(er.loc["W2","events"])} qualifying liquidity errors in W2 and {int(er.loc["W2_control","events"])} in its control period.'
    if (O/'A3_regressions.csv').exists():pressure+=' Shared exposure shows no consistent adverse effect on unaffected vaults.'
    w=reg[reg.spec.eq('windows')].set_index('term')
    refill=f'We replay recorded cash flows for the ten Base vaults. Requests are paid from largest to smallest closing assets. Median refill time is {b.loc[10,"median"]:.2f} hours for 10% requests and {b.loc[25,"median"]:.2f} hours for 25% requests. At 25%, {100*b.loc[25,"within24"]:.2f}% of dates are paid in full within 24 hours, and {int(b.loc[25,"censored"])} of 439 dates remain unpaid at seven days. The OLS Dup coefficient is positive but not significant ({rr.coef:.3f}, p = {rr.p:.3f}). The year-month-stratified Cox coefficient is negative ({cc.coef:.3f}, p = {cc.p:.3f}). After adding the window indicators, the W1 coefficient is negative ({w.loc["W1","coef"]:.3f}, p = {w.loc["W1","p"]:.3f}). W2 is not significant.'
    supply=pd.read_csv(O/'B2_sources_observed.csv');supply=supply[supply.order.eq('large_first')&supply.f.eq(25)&supply.source.eq('supply_inflow_micro')].share.iloc[0];refill+=f' External supply accounts for {100*supply:.2f}% of all observed inflows.'
    refill+=' At 25%, fixed-order initial payment succeeds on 15 dates, compared with 19 under the aggregate-bound and individual-pass conditions. Three differences reflect vault order; one remains infeasible under any allocation.'
    conclusion='The sample includes the October 2025 liquidation shock and the November 2025 Stream/Elixir stress episode.'
    (O/'PASTE_EN.md').write_text('# Section 4 or 5\n\n'+pressure+'\n\n# End of Section 5\n\n'+refill+'\n\n# Conclusion replacement\n\n'+conclusion+'\n')

if __name__=='__main__':build_doc();prose()
