from pathlib import Path
import pandas as pd,numpy as np,json,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
R=Path(__file__).resolve().parents[1];O=R/'reports/revision26';T=R/'submission/jifmim26/en'
if not T.exists():shutil.copytree(R/'submission/jifmim25a/en',T,ignore=shutil.ignore_patterns('build','._*'))
plt.rcParams.update({'font.family':'serif','font.serif':['Times New Roman'],'font.size':11,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
a=pd.read_csv(O/'regression_results.csv').fillna('');meta={x['model']:x for x in json.loads((O/'regression_models.json').read_text())};v=pd.read_parquet(O/'owner_day_panel.parquet');v['date']=pd.to_datetime(v.date);d=pd.read_csv(O/'estimation_daily_inputs.csv',parse_dates=['date']).set_index('date');g=v[~v.spark & v.risk_set_incumbent].copy()
def table(name,title,label,heads,rows,note,width='5.8cm'):
 text=r'\begin{table}[!htbp]\centering'+'\n'+r'\caption{'+title+r'}\label{'+label+'}\n'+r'\begin{threeparttable}\setstretch{1}\setlength{\tabcolsep}{3pt}'+'\n'+r'\begin{tabular}{@{}p{'+width+'}'+('r'*len(heads))+r'@{}}\toprule'+'\n'+' & '+' & '.join(heads)+r' \\\midrule'+'\n'
 for row in rows:text+=' & '.join(row)+r' \\'+'\n'
 text+=r'\bottomrule\end{tabular}\begin{tablenotes}[flushleft]\item \textit{Notes}. '+note+'\n'+r'\end{tablenotes}\end{threeparttable}\end{table}'+'\n';(T/'tables'/f'{name}.tex').write_text(text)
models=['other_flow_HAC7','spark_flow_HAC7','withdraw_any_cutoff1','deposit_any_cutoff1'];rows=[]
for key,label in [('premium','Native yield premium, $t-1$ (pp)'),('utilization','Utilization, $t-1$ (pp)'),('eth_return_pp','ETH return, $t-1$ (pp)'),('eth_volatility_pp','ETH volatility, $t-1$ (pp)'),('own_lag','Own net deposits, $t-1$'),('log_assets','Log vault assets, $t-1$'),('log_claim','Log opening claim'),('age_days','Account age (days)')]:
 vals=[];stats=[]
 for i,m in enumerate(models):
  k=key if key!='own_lag' else ('other_lag' if i==0 else 'spark_lag' if i==1 else '_');q=a[a.model.eq(m)&a.term.eq(k)]
  if len(q):r=q.iloc[0];scale=100 if i>1 else 1;vals.append(f'{float(r.coefficient)*scale:.3f}'+(r'\textsuperscript{'+str(r.stars)+'}' if r.stars else ''));stats.append(f'({float(r.t):.2f})')
  else:vals.append('--');stats.append('')
 rows.extend([[label]+vals,['']+stats])
rows += [['Month and weekday effects']+['Yes']*4,['Owner effects','No','No','Yes','Yes'],['Observations']+[f'{meta[m]["n"]:,}' for m in models],['Owners','--','--']+[f'{meta[m]["owners"]:,}' for m in models[2:]],['Dates','319','319','316','316'],['$R^2$ / within $R^2$']+[f'{meta[m].get("r2",meta[m].get("within_r2")):.3f}' for m in models]]
for key,label in [('premium','Holm $p$: native premium'),('utilization','Holm $p$: utilization')]:rows.append([label]+[f'{float(a[a.model.eq(m)&a.term.eq(key)].iloc[0].holm_p):.3f}' for m in models])
table('behavior','Native yields, market conditions and completed investment actions','tab:behavior',['(1) Other flow','(2) Spark flow','(3) Withdraw','(4) Deposit'],rows,'Columns (1)--(2) measure net deposits in million USDC and use HAC(7) covariance. Columns (3)--(4) are owner fixed-effect linear probability models; coefficients are percentage points, with two-way owner/date clustering. Their sample excludes Spark and requires an opening claim of at least 1 USDC; 971 singleton rows are excluded. Parentheses are robust t statistics. All four equations include month and weekday indicators. Probability models retain owners with constant outcomes. Stars denote two-sided pointwise probabilities: *** $p<0.01$, ** $p<0.05$, * $p<0.10$. The eight premium/utilization tests form one Holm family. Native rates exclude unmeasured rewards; the premium is Spark minus the equal-weighted Moonwell and Gauntlet APR. These are conditional associations, not causal responses.',width='5.3cm')
rows=[]
for k,label in [('prior_claim_usdc','Opening claim (USDC)'),('deposit_usdc','Daily deposits (USDC)'),('withdraw_usdc','Daily withdrawals (USDC)'),('deposit_any','Additional-deposit indicator'),('withdraw_any','Withdrawal indicator'),('prior_cash_coverage','Cash coverage')]:
 s=g[k];rows.append([label,f'{len(s):,}',f'{s.mean():,.3f}',f'{s.std():,.3f}',f'{s.median():,.3f}',f'{s.quantile(.95):,.3f}'])
table('owner_summary','Non-Spark incumbent accounts: descriptive statistics','tab:ownersummary',['$N$','Mean','SD','Median','P95'],rows,'The opening-claim threshold is 1 USDC. The 513,949 eligible owner-days include no-action days and 13,341 addresses; observations are not independent institutions. This table precedes singleton removal for fixed-effect estimation. Cash coverage is the smaller of one and the selected vault cash benchmark divided by the opening claim. Owner-specific execution is not inferred from this benchmark for the entire sample.',width='4.5cm')
g['size_group']=pd.cut(g.prior_claim_usdc,[1,100,10000,1000000,np.inf],right=False);rows=[]
for label,z in g.groupby('size_group',observed=True):
 rows.append([str(label).replace('[1.0, 100.0)','1--99').replace('[100.0, 10000.0)','100--9,999').replace('[10000.0, 1000000.0)','10,000--999,999').replace('[1000000.0, inf)','$\\geq$1,000,000'),f'{len(z):,}',f'{z.owner.nunique():,}',f'{100*z.withdraw_any.mean():.2f}',f'{100*z.deposit_any.mean():.2f}',str(z.prior_cash_coverage.lt(1).sum())])
table('owner_size','Position size and completed actions among other holders','tab:ownersize',['Owner-days','Addresses','Withdraw (\\%)','Deposit (\\%)','Cash $<Q$'],rows,'Groups use each day\'s opening claim in USDC, without future information. An address may appear in more than one size group; address counts therefore cannot be added. Action percentages use all eligible days, including zero-action days. The final column counts states with cash coverage below one. No non-Spark observation has benchmark coverage below 25 percent. Group differences are descriptive and are not interpreted as causal size effects.',width='3.8cm')
cols=['withdraw_any_cutoff0','withdraw_any_cutoff1','withdraw_any_cutoff100','deposit_any_cutoff0','deposit_any_cutoff1','deposit_any_cutoff100'];rows=[]
for key,label in [('premium','Native premium (pp)'),('utilization','Utilization (pp)')]:
 vals=[];ts=[]
 for m in cols:
  r=a[a.model.eq(m)&a.term.eq(key)].iloc[0];vals.append(f'{100*float(r.coefficient):.3f}'+(r'\textsuperscript{'+r.stars+'}' if r.stars else ''));ts.append(f'({float(r.t):.2f})')
 rows.extend([[label]+vals,['']+ts])
rows+=[['Opening claim cutoff','$>0$','$\\geq1$','$\\geq100$','$>0$','$\\geq1$','$\\geq100$'],['Observations']+[f'{meta[m]["n"]:,}' for m in cols],['Owner effects']+['Yes']*6]
table('owner_sensitivity','Opening-claim thresholds and incumbent actions','tab:ownersensitivity',['W: $>0$','W: 1','W: 100','D: $>0$','D: 1','D: 100'],rows,'W denotes withdrawal and D additional deposit. Coefficients are percentage points. Controls, owner effects and two-way owner/date inference are unchanged. Cutoffs were specified before estimation; these sensitivities are not additional primary tests. Pointwise stars follow the main table. Complete controls and p values accompany the replication files.',width='3.0cm')
# Two substantive plots: participation and native interest rates.
z=v[~v.spark].groupby('date').agg(holders=('opening_shares',lambda s:s.gt(0).sum()),depositors=('deposit_any','sum'),withdrawers=('withdraw_any','sum'))
fig,ax=plt.subplots(2,1,figsize=(7,5.5),sharex=True,layout='constrained');ax[0].plot(z.index,z.holders,color='#263b54');ax[0].set_ylabel('Positive opening balances');ax[1].plot(z.index,z.depositors,label='Deposit beneficiaries',color='#263b54');ax[1].plot(z.index,z.withdrawers,label='Withdrawing owners',color='#aa6944',linestyle='--');ax[1].set_ylabel('Active addresses per day');ax[1].legend(frameon=False);ax[1].xaxis.set_major_locator(mdates.MonthLocator(interval=2));ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%b'));ax[1].set_xlabel('2025');ax[1].set_xlim(pd.Timestamp('2025-01-15'),pd.Timestamp('2025-11-30'));fig.savefig(T/'figures/participation.pdf');fig.savefig(O/'participation.png',dpi=160);plt.close(fig)
y=pd.read_csv(O/'native_yields.csv',parse_dates=['date']);fig,ax=plt.subplots(figsize=(7,3.7),layout='constrained')
for k,label,color,style in [('spark','Spark','#263b54','-'),('moonwell','Moonwell','#aa6944','--'),('gauntlet','Gauntlet','#698377',':')]:ax.plot(y.date,100*y[k+'_net_native_APR'],label=label,color=color,linestyle=style)
ax.set_ylabel('Net native-interest APR (%)');ax.legend(frameon=False,ncol=3);ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'));ax.set_xlabel('2025');ax.set_xlim(pd.Timestamp('2025-01-15'),pd.Timestamp('2025-11-30'));fig.savefig(T/'figures/native_yields.pdf');fig.savefig(O/'native_yields.png',dpi=160);plt.close(fig)
# Descriptive findings usable for source-checked prose.
ethena=g[g.owner.eq('0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c')];facts={'non_spark_eligible_mean_deposit_pct':100*g.deposit_any.mean(),'non_spark_eligible_mean_withdraw_pct':100*g.withdraw_any.mean(),'under_full_coverage_by_owner':g[g.prior_cash_coverage.lt(1)].groupby('owner').size().to_dict(),'ethena_incumbent_days':len(ethena),'ethena_min_coverage':ethena.prior_cash_coverage.min()};(O/'presentation_facts.json').write_text(json.dumps(facts,indent=2));print(facts)
