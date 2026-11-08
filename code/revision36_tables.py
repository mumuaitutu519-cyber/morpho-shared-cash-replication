from pathlib import Path
import shutil,numpy as np,pandas as pd,json
R=Path(__file__).resolve().parents[1];P=R/'submission/revision36/en';O=R/'reports/revision36';P.mkdir(parents=True,exist_ok=True);O.mkdir(exist_ok=True)
for f in (R/'submission/jifmim35/en').rglob('*'):
 if f.is_file() and not f.name.startswith('._') and f.suffix in {'.tex','.bib','.pdf','.png','.json','.md'} and f.name!='manuscript.pdf':
  t=P/f.relative_to(R/'submission/jifmim35/en');t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,t)
v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');g=v[v.risk_set_incumbent&~v.spark];assert len(g)==513949
rows=[]
def calc(panel,label,x,kind):
 x=pd.Series(np.asarray(x,dtype=float));assert x.notna().all() and np.isfinite(x).all();q=x.quantile([.25,.5,.75]);rec=dict(panel=panel,label=label,kind=kind,N=len(x),mean=x.mean(),sd=x.std(ddof=1),min=x.min(),p25=q.loc[.25],median=q.loc[.5],p75=q.loc[.75],max=x.max());rows.append(rec)
calc('A. Natural-log monetary variables',r'$\ln(\mathrm{claim})$',np.log(g.prior_claim_usdc),'main')
calc('A. Natural-log monetary variables',r'$\ln(1+\mathrm{deposits})$',np.log1p(g.deposit_usdc),'main')
calc('A. Natural-log monetary variables',r'$\ln(1+\mathrm{withdrawals})$',np.log1p(g.withdraw_usdc),'main')
for key,label in [('deposit_any','Deposit indicator'),('withdraw_any','Withdrawal indicator'),('prior_cash_coverage','Cash coverage')]:calc('B. Indicators and cash coverage',label,g[key],'main')
for key,label in [('deposit_usdc',r'$\ln(1+\mathrm{deposits})$'),('withdraw_usdc',r'$\ln(1+\mathrm{withdrawals})$')]:calc('C. Natural logs conditional on a positive flow',label,np.log1p(g.loc[g[key]>0,key]),'main')
for key,label in [('prior_claim_usdc','Opening claim'),('deposit_usdc','Daily deposits'),('withdraw_usdc','Daily withdrawals')]:calc('A. All eligible owner-days',label,g[key]/1000,'raw')
for key,label in [('deposit_usdc','Positive deposits'),('withdraw_usdc','Positive withdrawals')]:calc('B. Conditional on a positive flow',label,g.loc[g[key]>0,key]/1000,'raw')
s=pd.DataFrame(rows);s.to_csv(O/'descriptive_statistics.csv',index=False);fields=['mean','sd','min','p25','median','p75','max']
def fmt(x,kind):
 if x==0:return '0.000'
 if kind=='raw' and 0<abs(x)<.001:return '$<0.001$'
 return f'{x:.3f}' if abs(x)<1 else f'{x:.2f}'
def table(kind,name,caption,label,notes):
 rr=[]
 for panel,z in s[s.kind==kind].groupby('panel',sort=False):
  rr.append(r'\multicolumn{9}{@{}l}{\textit{Panel '+panel+r'}} \\')
  for x in z.itertuples():rr.append(x.label+' & '+f'{x.N:,}'+' & '+' & '.join(fmt(getattr(x,k),kind) for k in fields)+r' \\')
  rr.append(r'\addlinespace')
 (P/'tables'/name).write_text('\\begin{table}[!htbp]\\centering\n\\caption{'+caption+'}\\label{'+label+'}\n\\begin{threeparttable}\\setstretch{1}\\setlength{\\tabcolsep}{3pt}\n'+r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{4.0cm}rrrrrrrr@{}}\toprule'+'\n'+r'Variable & $N$ & Mean & SD & Min & P25 & P50 & P75 & Max \\ \midrule'+'\n'+'\n'.join(rr)+'\n'+r'\bottomrule\end{tabular}'+'\n'+r'\begin{tablenotes}[flushleft]\item \textit{Notes}. '+notes+'\n'+r'\end{tablenotes}\end{threeparttable}\end{table}'+'\n')
table('main','owner_summary.tex','Non-Spark accounts: log amounts and participation','tab:ownersummary',r'Claim, deposits and withdrawals are measured in USDC before taking natural logarithms. Opening claims are at least one USDC, so $\ln(\mathrm{claim})$ is defined. Adding one retains zero-flow days in the gross-flow variables. Statistics are computed after transforming each observation, not by taking logs of raw summary statistics. Panel B retains the original zero--one indicators and coverage ratio. Panel C conditions on a positive flow. SD is the sample standard deviation; P25, P50 and P75 are linearly interpolated quartiles. The sample contains 513,949 eligible owner-days before singleton removal; raw monetary statistics appear in Table \ref{tab:ownerraw36}.')
table('raw','owner_raw.tex','Non-Spark monetary amounts in original units','tab:ownerraw36',r'All monetary values are thousands of USDC, with no logarithm or winsorization. Values shown as $<0.001$ are strictly positive and smaller than one USDC; zeros remain zero. Panel B conditions on a strictly positive daily flow within the same eligible owner sample. SD is the sample standard deviation; P25, P50 and P75 are linearly interpolated quartiles. These original amounts complement the natural-log variables in Table \ref{tab:ownersummary}.')
b=(P/'body.tex').read_text().replace('The tables retain raw observations, including verified large transactions and zero-flow days. Descriptive distributions and regression transformations are therefore separately defined.','Table \\ref{tab:summary} retains original monetary units. Table \\ref{tab:ownersummary} reports natural-log account amounts alongside untransformed indicators and coverage. Table \\ref{tab:ownerraw36} provides the corresponding raw account amounts. Verified large transactions and zero-flow days remain in the samples.')
(P/'body.tex').write_text(b)
a=(P/'appendix.tex').read_text().replace('The descriptive tables report untrimmed observations because verified large transactions are part of the institution\'s recorded funding activity.','The descriptive samples retain verified large transactions as part of the institution\'s recorded funding activity. Table \\ref{tab:ownersummary} transforms monetary observations individually into natural-log variables; Table \\ref{tab:ownerraw36} reports their original amounts.')
a+='\n\\section{Original Account Amounts}\\label{app:raw36}\n\\input{tables/owner_raw}\n';(P/'appendix.tex').write_text(a)
(P/'README.md').write_text('R36: Table 2 uses ln(claim) and ln(1+gross flow), with each amount measured in USDC. Indicators and coverage retain their original scale. Original monetary statistics are in an appendix table in thousands of USDC, without scientific notation. This is a descriptive-variable presentation revision; all regression estimates, funding bounds and historical execution amounts are unchanged. Compile with latexmk -xelatex manuscript.tex.\n')
assert np.allclose(np.expm1(np.log1p(g.deposit_usdc)),g.deposit_usdc,rtol=1e-12,atol=1e-12)
(O/'VALIDATION.json').write_text(json.dumps({'owner_days':len(g),'statistic_rows':len(s),'log_computed_observation_by_observation':True,'zero_days_retained':True,'natural_log_inverse_check':True,'regressions_reestimated':False},indent=2));print(s[s.kind=='main'][['label','mean','median','max']].to_string(index=False))
