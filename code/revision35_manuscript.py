from pathlib import Path
import shutil,pandas as pd,json
R=Path(__file__).resolve().parents[1];P=R/'submission/jifmim35/en';O=R/'reports/revision35';P.mkdir(parents=True,exist_ok=True)
for f in (R/'submission/jifmim34/en').rglob('*'):
 if f.is_file() and not f.name.startswith('._') and f.suffix in {'.tex','.bib','.pdf','.png','.json','.md'} and f.name!='manuscript.pdf':
  t=P/f.relative_to(R/'submission/jifmim34/en');t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,t)
st=pd.read_csv(O/'descriptive_statistics.csv');fields=['mean','sd','min','p25','median','p75','max']
def table(name,caption,label,body,notes,columns,header):
 (P/'tables'/name).write_text('\\begin{table}[!htbp]\\centering\n\\caption{'+caption+'}\\label{'+label+'}\n\\begin{threeparttable}\\setstretch{1}\\setlength{\\tabcolsep}{3pt}\n\\begin{tabular}{'+columns+'}\\toprule\n'+header+r' \\'+'\n\\midrule\n'+'\n'.join(body)+'\n\\bottomrule\\end{tabular}\n\\begin{tablenotes}[flushleft]\\item \\textit{Notes}. '+notes+'\n\\end{tablenotes}\\end{threeparttable}\\end{table}\n')
rows=[]
for panel,g in st[st.panel.str.startswith(('A.','B.','C.'))].groupby('panel',sort=False):
 rows.append(r'\multicolumn{9}{@{}l}{\textit{Panel '+panel+r'}} \\')
 for x in g.itertuples():rows.append(x.label+' & '+str(x.N)+' & '+' & '.join(f'{getattr(x,k):.2f}' for k in fields)+r' \\')
 rows.append(r'\addlinespace')
table('summary.tex','Descriptive statistics','tab:summary',rows,'Values describe the untrimmed observations. Panel A contains 94 matched deposits, April--November 2025; Panels B and C contain all 319 days, January 16--November 30, including zero-flow days. Cash and claim amounts are million USDC; received shares are millions; coverage and utilization are percentages. SD is the sample standard deviation. P25, P50 and P75 are linearly interpolated sample quartiles. Net borrowing subtracts repayments, including liquidation repayments, and excludes interest. Other net supply excludes the Spark vault.',r'@{}>{\raggedright\arraybackslash}p{4.0cm}rrrrrrrr@{}','Variable & $N$ & Mean & SD & Min & P25 & P50 & P75 & Max')
def fmt(x):
 if x==0:return '0'
 if abs(x)>=10000 or abs(x)<.001:return f'{x:.2e}'.replace('e+0','e').replace('e-0','e-')
 if abs(x)>=100:return f'{x:.1f}'
 return f'{x:.3f}'
rows=[r'\multicolumn{9}{@{}l}{\textit{Panel A. All eligible owner-days}} \\']
for x in st[st.panel.str.startswith('D.')].itertuples():rows.append(x.label+' & '+f'{x.N:,}'+' & '+' & '.join(fmt(getattr(x,k)) for k in fields)+r' \\')
rows.append(r'\midrule\multicolumn{9}{@{}l}{\textit{Panel B. Conditional on a positive flow}} \\')
for x in st[st.panel.str.startswith('E.')].itertuples():rows.append(x.label+' & '+f'{x.N:,}'+' & '+' & '.join(fmt(getattr(x,k)) for k in fields)+r' \\')
table('owner_summary.tex','Non-Spark incumbent accounts: descriptive statistics','tab:ownersummary',rows,'Amounts are untrimmed USDC. Scientific notation e6 means multiplication by one million. The opening-claim threshold is 1 USDC. All 513,949 eligible owner-days and 13,341 addresses are retained, including no-action days and before singleton removal for estimation. SD is the sample standard deviation; P25, P50 and P75 are linearly interpolated quartiles. Indicators are zero or one. Cash coverage is the smaller of one and the cash benchmark divided by the opening claim. Panel B conditions on strictly positive daily amounts within the same eligible owner sample. In Panel A, flow quartiles can all be zero because completed actions occur on fewer than five percent of owner-days.',r'@{}>{\raggedright\arraybackslash}p{3.2cm}rrrrrrrr@{}','Variable & $N$ & Mean & SD & Min & P25 & P50 & P75 & Max')
a=pd.read_csv(O/'all_coefficients.csv');rows=[]
def star(p):return '***' if p<.01 else '**' if p<.05 else '*' if p<.1 else ''
for var,label in [('raw','A. Original million-USDC flows'),('winsor1','B. Flows winsorized at P1 and P99'),('log_signed','C. Log gross flows and signed net transformation')]:
 rows.append(r'\multicolumn{6}{@{}l}{\textit{'+label+r'}} \\')
 for y,ylab in [('deposits','Gross deposits'),('withdrawals','Gross withdrawals'),('net','Net deposits')]:
  x=a[(a.variant==var)&(a.outcome==y)&a.HAC.eq(7)&a.term.eq('utilization')].iloc[0]
  rows.append(ylab+' & '+f'{x.coefficient:.4f}'+star(x.p)+' & '+f'{x.se:.4f} & {x.p:.4f}'+' & '+('---' if pd.isna(x.holm12) else f'{x.holm12:.4f}')+' & '+('---' if pd.isna(x.holm60) else f'{x.holm60:.4f}')+r' \\')
 rows.append(r'\addlinespace')
table('flow_transformations.tex','Daily funding sensitivity to flow representation','tab:transform35',rows,'The table reports the utilization coefficient, measured per percentage point, on the same 319 dates with the original controls and month and weekday effects. SE uses seven-day HAC with the original finite-sample correction. Stars denote pointwise $p<0.10$, $0.05$ and $0.01$. Panel B caps gross flows separately and rebuilds net flows and their lag. Panel C uses $\\ln(1+x)$ for gross USDC flows and $\\operatorname{asinh}(x)$ for net USDC and its lag. These coefficients have different units across panels. The 12-test family includes utilization and premium in the six new models; the 60-test family also includes the 48 earlier focal tests. Original-model adjustments remain in their original tables. Full coefficients and fourteen-day HAC comparisons accompany the replication files.',r'@{}lrrrrr@{}','Outcome & Coefficient & SE & $p$ & Holm 12 & Holm 60')
b=(P/'body.tex').read_text();b=b.replace('Table \\ref{tab:summary} separates the event, owner-day and market-day units.','Tables \\ref{tab:summary} and \\ref{tab:ownersummary} report the minimum, quartiles and maximum alongside the mean and standard deviation, separating event, owner-day and market-day units.')
needle='The distinction matters because an event-weighted mean gives more weight to active days.'
b=b.replace(needle,needle+' The tables retain raw observations, including verified large transactions and zero-flow days. Descriptive distributions and regression transformations are therefore separately defined.')
needle='This distribution makes aggregate funding shares an inadequate description of the information available for each transaction.'
b=b.replace(needle,needle+' Matched deposit skewness is 4.61; daily gross deposits and withdrawals have skewness of 2.13 and 2.17. Daily net deposits instead include negative amounts and have skewness of $-1.04$. Log assets and log opening claims already enter the relevant regression designs. Appendix \\ref{app:distribution35} adds a fixed winsorization and nonlinear flow comparison; no transformation changes the transaction amounts used in funding or withdrawal tests.')
b=b.replace('For the daily net coefficient, the pointwise probability is 0.0029, the cumulative-family Holm probability is 0.0867, and the BH false-discovery-rate value is 0.0308.','For the daily net coefficient, the pointwise probability is 0.0029. Within the original 32-test daily and owner-panel program, the Holm probability is 0.0867 and the BH false-discovery-rate value is 0.0308.')
b=b.replace('Its pointwise probabilities remain below 0.05 in those checks.','Its pointwise probabilities remain below 0.05 in those checks. Capping gross flows at their first and 99th percentiles and rebuilding net flows gives a coefficient of 0.3578, compared with 0.3771 in raw amounts. The signed nonlinear representation is less precise, so the relation remains specific to dollar net funding rather than a transformation-invariant response (Appendix \\ref{app:distribution35}).')
(P/'body.tex').write_text(b)
a=(P/'appendix.tex').read_text()+r'''
\section{Distribution and Flow Transformations}\label{app:distribution35}
The descriptive tables report untrimmed observations because verified large transactions are part of the institution's recorded funding activity. Quartiles use linear interpolation between ordered observations; the supporting data also report P99, zero frequency and skewness. Deposits in the 94-event cohort have P25 of 0.191 million USDC, median 1.072 million and P75 of 3.094 million. The maximum of 92.641 million represents 18.87 percent of this cohort's value. The owner panel has a different distribution: the median opening claim is 49.853 USDC and the mean is 29,407.945 USDC. Most owner-days contain no completed action, so zero deposit and withdrawal quartiles are expected rather than evidence of a missing-data replacement.

A fixed functional-form comparison keeps the 319 daily observations and the original utilization, premium, log-assets, return, volatility and calendar regressors. The first sensitivity caps deposits and withdrawals at their separate first and 99th percentiles, then recomputes their difference and its lag. This preserves the deposit-minus-withdrawal identity within the transformed estimation sample. The original ledger and all funding and execution amounts remain unchanged. The second uses $\ln(1+x)$ for nonnegative gross flows and $\operatorname{asinh}(x)=\ln(x+\sqrt{x^2+1})$ for signed net flows and their lag, with $x$ measured in USDC. The fixed one-USDC offset/scale retains zero and negative values. Coefficients in that representation are neither million-USDC slopes nor uniform percentage elasticities. Binary actions and bounded coverage measures are not logged or winsorized.
\input{tables/flow_transformations}

The winsorized dollar-net utilization coefficient is 0.3578, with pointwise probability 0.0024, compared with 0.3771 and 0.0029 in the original model. The nonlinear net coefficient is 0.1227 with probability 0.2106. Thus, the dollar association is not removed by this tail cap, but a different weighting of flow size and sign does not yield the same precision. The complete coefficient and covariance files retain premium estimates and the fourteen-day HAC comparisons. Logarithms and winsorization address particular functional-form and tail-influence questions; they are not applied to make the financial flows normally distributed or to select a preferred significance outcome.
'''
(P/'appendix.tex').write_text(a)
(P/'README.md').write_text('''# R35 English manuscript and appendix\nCompile `latexmk -xelatex manuscript.tex` with Times New Roman installed. Main descriptive tables now include N, mean, sample SD, min, P25, P50, P75 and max on unchanged raw samples. The final appendix documents the fixed 1/99-percent flow winsorization and log/signed-flow comparison. Source-attribution and historical execution data are unchanged. Author information, data-sharing statement and journal selection remain pending.\n''')
print(P)
