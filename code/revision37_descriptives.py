from pathlib import Path
import numpy as np,pandas as pd,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/revision37';O.mkdir(exist_ok=True)
d=pd.read_csv(R/'reports/revision28/daily_analysis.csv',parse_dates=['date']).set_index('date');v=pd.read_parquet(R/'reports/revision27/owner_day_panel.parquet');v.date=pd.to_datetime(v.date)
g=v[~v.spark&v.date.ge('2025-01-16')&v.prior_claim_usdc.ge(1)].copy();n0=len(g)
while True:
 keep=g.groupby('owner').owner.transform('size').gt(1)&g.groupby('date').date.transform('size').gt(1)
 if keep.all():break
 g=g[keep].copy()
g=g.merge(d[['utilization','premium','eth_return_pp','eth_volatility_pp']],left_on='date',right_index=True,validate='many_to_one');g['log_claim']=np.log(g.prior_claim_usdc);g['centered_size']=g.log_claim-np.log(1000);g['deposit_pp']=100*g.deposit_any;g['withdraw_pp']=100*g.withdraw_any
g['log_low']=np.minimum(g.log_claim,np.log(100));g['log_high']=np.maximum(g.log_claim-np.log(100),0)
for k in ['utilization','premium','eth_return_pp','eth_volatility_pp']:
 g[k+'_size']=g[k]*g.centered_size
 for seg in ['low','high']:g[k+'_'+seg]=g[k]*g['log_'+seg]
assert (len(g),g.owner.nunique(),g.date.nunique(),n0-len(g))==(512978,12370,316,971)
rows=[]
def stats(sample,key,label,f):
 x=f[key].astype(float);assert x.notna().all() and np.isfinite(x).all();q=x.quantile([.25,.5,.75]);rows.append(dict(sample=sample,variable=key,label=label,N=len(x),mean=x.mean(),sd=x.std(ddof=1),min=x.min(),p25=q.loc[.25],median=q.loc[.5],p75=q.loc[.75],max=x.max()))
D=d.loc['2025-01-16':].copy();assert len(D)==319
labels=[('deposits','Gross deposits'),('withdrawals','Gross withdrawals'),('net','Net deposits'),('utilization','Utilization, lagged'),('premium','Premium, lagged'),('eth_return_pp','ETH return, lagged'),('eth_volatility_pp','ETH volatility, lagged'),('spark_lag','Net deposits, lagged'),('log_assets','Log assets, lagged')]
for k,label in labels:stats('Daily treasury model',k,label,D)
for h in [3,7]:
 z=D.copy();z['cumulative_net']=sum(d.net.shift(-i) for i in range(h)).loc[z.index];z=z[z.cumulative_net.notna()];assert len(z)==319-h+1
 for k,label in [('cumulative_net',f'{h}-day cumulative net')]+labels[3:]:stats(f'{h}-day treasury model',k,label,z)
ownerlabels=[('deposit_pp','Deposit (pp)'),('withdraw_pp','Withdrawal (pp)'),('log_claim',r'Log claim, $\ell$'),('premium_size',r'Premium $\times\widetilde\ell$'),('utilization_size',r'Utilization $\times\widetilde\ell$'),('eth_return_pp_size',r'ETH return $\times\widetilde\ell$'),('eth_volatility_pp_size',r'ETH volatility $\times\widetilde\ell$')]
for k,label in ownerlabels:stats('Owner linear model',k,label,g)
for k,label in [('log_low',r'$\ell_L$'),('log_high',r'$\ell_H$')]+[(k+'_'+seg,label+r' $\times\ell_'+('L' if seg=='low' else 'H')+'$') for k,label in [('premium','Premium'),('utilization','Utilization'),('eth_return_pp','ETH return'),('eth_volatility_pp','ETH volatility')] for seg in ['low','high']]:stats('Owner spline model',k,label,g)
s=pd.DataFrame(rows);s.to_csv(O/'regression_descriptive_statistics.csv',index=False)
# Validate identical original sample sizes and outcome scales against archived model records.
models=json.loads((R/'reports/revision28/models.json').read_text());checks=[]
for model,y,frame in [('deposits_HAC7','deposits',D),('withdrawals_HAC7','withdrawals',D),('net_HAC7','net',D),('sizeFE_deposit','deposit_pp',g),('sizeFE_withdraw','withdraw_pp',g)]:
 m=next(x for x in models if x['model']==model);assert m['n']==len(frame);gap=abs(m['mean']-frame[y].mean());assert gap<1e-10;checks.append({'model':model,'N':len(frame),'outcome_mean_gap':gap})
# Summaries are before fixed-effect absorption; this follows ordinary descriptive-table practice.
keys=g[['date','owner']].sort_values(['date','owner']).to_csv(index=False);(O/'owner_sample_keys.csv').write_text(keys)
validation={'passed':True,'checks':checks,'owner_singletons_removed':n0-len(g),'owner_sample_sha256':hashlib.sha256(keys.encode()).hexdigest(),'statistics_before_FE_absorption':True,'new_regressions':0};(O/'VALIDATION.json').write_text(json.dumps(validation,indent=2))
P=R/'submission/revision37/en';P.mkdir(parents=True,exist_ok=True)
for f in (R/'submission/revision36/en').rglob('*'):
 if f.is_file() and not f.name.startswith('._') and f.suffix in {'.tex','.bib','.pdf','.png','.json','.md'} and f.name!='manuscript.pdf':
  t=P/f.relative_to(R/'submission/revision36/en');t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,t)
fields=['mean','sd','min','p25','median','p75','max']
def make(name,caption,label,groups,notes):
 rr=[]
 for title,z in groups:
  rr.append(r'\multicolumn{9}{@{}l}{\textit{'+title+r'}} \\')
  for x in z.itertuples():rr.append(x.label+' & '+f'{x.N:,}'+' & '+' & '.join(f'{getattr(x,k):.2f}' for k in fields)+r' \\')
  rr.append(r'\addlinespace')
 (P/'tables'/name).write_text('\\begin{table}[!htbp]\\centering\n\\caption{'+caption+'}\\label{'+label+'}\n\\begin{threeparttable}\\setstretch{1}\\setlength{\\tabcolsep}{3pt}\n'+r'\begin{tabular}{@{}>{\raggedright\arraybackslash}p{4.0cm}rrrrrrrr@{}}\toprule'+'\n'+r'Variable & $N$ & Mean & SD & Min & P25 & P50 & P75 & Max \\ \midrule'+'\n'+'\n'.join(rr)+'\n'+r'\bottomrule\end{tabular}'+'\n'+r'\begin{tablenotes}[flushleft]\item \textit{Notes}. '+notes+'\n'+r'\end{tablenotes}\end{threeparttable}\end{table}')
old=(P/'tables/summary.tex').read_text().replace('\\label{tab:summary}','\\label{tab:rawcontexts}').replace('\\caption{Descriptive statistics}','\\caption{Original transaction, account and market distributions}');(P/'tables/raw_context_statistics.tex').write_text(old)
make('summary.tex','Descriptive statistics: treasury regression samples','tab:summary',[('Panel A. Daily models',s[s['sample'].eq('Daily treasury model')]),('Panel B. Complete-horizon outcomes',s[s.variable.eq('cumulative_net')])],r'Panel A uses the exact 319 dates and variable forms of Table \ref{tab:components}. Amounts are million USDC; rates are percentage points; log assets is the natural log of vault assets measured in USDC. Predictors retain their original one-day lag. Panel B uses the 317 and 313 complete observations for the three- and seven-day outcomes in Table \ref{tab:horizons}; horizon-specific predictor summaries accompany the replication data. No winsorization is applied to these baseline models. SD is the sample standard deviation; P25, P50 and P75 are linearly interpolated quartiles.')
make('owner_summary.tex','Descriptive statistics: owner regression sample','tab:ownersummary',[('Linear probability models',s[s['sample'].eq('Owner linear model')])],r'The sample matches columns (1)--(2) of Table \ref{tab:sizeactions}: 512,978 owner-days after removing 971 singleton observations, 12,370 owners and 316 dates. Outcomes equal 100 times the zero--one action indicators, matching the percentage-point regression scale. $\ell=\ln(Q)$ for the opening claim $Q$ measured in USDC, and $\widetilde\ell=\ell-\ln(1000)$. Interactions use the lagged percentage-point predictors and this centered log size. Statistics describe the actual variables before fixed-effect absorption. SD is the sample standard deviation; quartiles use linear interpolation. The spline variables are summarized in Table \ref{tab:splinestats37}.')
make('spline_statistics.tex','Descriptive statistics: spline regressors','tab:splinestats37',[('Owner spline model',s[s['sample'].eq('Owner spline model')])],r'The 512,978 observations match column (3) of Table \ref{tab:sizeactions}. With $\ell=\ln(Q)$ for opening USDC claims, $\ell_L=\min\{\ell,\ln(100)\}$ and $\ell_H=\max\{\ell-\ln(100),0\}$. Each interaction uses its displayed segment and the original lagged percentage-point predictor. Outcome and sample summaries are the same as in Table \ref{tab:ownersummary}. No descriptive-only transformation is added.')
b=(P/'body.tex').read_text();start=b.index('Tables \\ref{tab:summary} and');end=b.index('The matched deposit mean',start)
b=b[:start]+r'''Tables \ref{tab:summary} and \ref{tab:ownersummary} report N, mean, standard deviation, minimum, quartiles and maximum for the variables in the corresponding regressions. The daily model retains dollar flows and logged vault assets; the owner model uses percentage-point action outcomes, log opening claims and the actual centered-size interactions. The owner table uses the estimation sample after singleton removal. Original monetary distributions appear in Tables \ref{tab:rawcontexts} and \ref{tab:ownerraw36}. '''.replace('\\\\','\\')+b[end:]
b=b.replace('Table \\ref{tab:summary} separates','Table \\ref{tab:rawcontexts} separates')
(P/'body.tex').write_text(b)
a=(P/'appendix.tex').read_text().replace('Table \\ref{tab:ownersummary} transforms monetary observations individually into natural-log variables; Table \\ref{tab:ownerraw36} reports their original amounts.','Tables \\ref{tab:summary} and \\ref{tab:ownersummary} use the actual regression variables and estimation samples. Table \\ref{tab:ownerraw36} separately reports original account amounts.')
a+='\n\\section{Original Distributions and Spline Variables}\n\\input{tables/raw_context_statistics}\n\\input{tables/spline_statistics}\n';(P/'appendix.tex').write_text(a)
# Remove obsolete references claiming Table 2 logs deposit/withdrawal amounts.
x=(P/'tables/owner_raw.tex').read_text().replace('These original amounts complement the natural-log variables in Table \\ref{tab:ownersummary}.','The eligible sample here precedes singleton removal; the regression-sample variables appear in Table \\ref{tab:ownersummary}.');(P/'tables/owner_raw.tex').write_text(x)
(P/'README.md').write_text('R37 aligns descriptive statistics with actual regression variables and samples. Table 1 covers the 319-day treasury model and complete-horizon outcomes. Table 2 covers the 512,978-observation owner estimation sample with outcomes multiplied by 100, log claim and exact interaction terms. The appendix preserves original monetary distributions and describes spline regressors. No regression is re-estimated or replaced. Compile using latexmk -xelatex manuscript.tex.\n')
print(json.dumps(validation,indent=2))
