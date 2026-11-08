"""Focus the main argument; retain complete explored specifications in the appendix."""
from pathlib import Path
import pandas as pd,json
R=Path(__file__).resolve().parents[1];T=R/'submission/jifmim27/en';O=R/'reports/revision27'
b=(T/'body.tex').read_text();a=(T/'appendix.tex').read_text()
start=b.index('Native interest is constructed');end=b.index('\\subsection{Gross turnover',start);rates=b[start:end];b=b[:start]+b[end:]
start=b.index('\\subsection{Investment opportunities and completed actions}');end=b.index('\\subsection{Position size',start);old=b[start:end]
eqstart=old.index('For non-Spark incumbent');eqend=old.index('\\input{tables/behavior}',eqstart);owner_eq=old[eqstart:eqend]
new=r'''\subsection{Treasury net funding and market utilization}
The realized-funding analysis asks whether the treasury supplies more net funds when a larger fraction of market assets is lent out. This connects the preceding capacity measurements to completed treasury operations. The daily outcome is Spark deposits less withdrawals, rather than gross turnover or the number of transactions. The incentive perspective of \citet{saengchote2023lending} motivates controlling for alternative native interest opportunities.

For daily treasury net deposits $F_t$, estimate
\begin{equation}
F_t=\alpha+\beta u_{t-1}+\rho F_{t-1}+\theta'X_{t-1}
+\delta_{m(t)}+\eta_{w(t)}+\varepsilon_t.
\end{equation}
$u$ is utilization in percentage points. $X$ includes the native-interest premium, log vault assets, ETH log return and 30-day daily-return volatility. Net flows are million USDC. Month and weekday effects control for recurring calendar differences. The 319-date specification uses seven-day HAC covariance; the fourteen-day sensitivity changes inference without changing the fitted coefficients. Appendix \ref{app:owners26} defines the native-interest control and retains the full set of explored equations.
\input{tables/treasury_funding}

A ten-percentage-point higher lagged utilization is associated with 3.771 million USDC more treasury net deposits, conditional on controls. The pointwise probability is 0.0029; the Holm probability is 0.0231 across the original eight premium/utilization tests. The result supports a positive conditional relationship between market utilization and realized treasury funding. It does not identify an exogenous utilization shock or show that the treasury meets all liquidity demand. This focal relation is retained from the broader analysis, whose complete results and unchanged test family are reported in the appendix.

'''
b=b[:start]+new+b[end:]
b=b.replace('It measures how fractional coverage varies with position size and whether completed actions covary with native interest opportunities.','It measures how fractional coverage varies with position size. A daily regression then relates realized treasury net funding to market utilization.')
b=b.replace('A third compares native interest opportunities and utilization with subsequent net funding and completed investment actions.','A third relates utilization to subsequent treasury net funding, conditional on investment opportunities and other market conditions.')
b=b.replace('Utilization covaries with Spark net deposits; the native premium has a less robust relationship with additional-deposit frequency and no precise net-flow relationship. These are heterogeneous participation patterns within one vault, not representative institutional effects.','Higher lagged utilization is associated with larger Spark net deposits after controlling for market conditions and correcting for the broader test family. This relationship describes completed treasury funding within one vault, rather than a representative institutional response.')
(T/'body.tex').write_text(b)
anchor='\\section{Expanded Owner Panel and Rate Validation}\\label{app:owners26}'
a=a.replace(anchor,anchor+'\n\\subsection{Complete exploratory specifications}\nThe full four-equation comparison is retained here, including imprecise results. The main text concentrates on the treasury-utilization relation supported after correction across the original eight tests. No variable is removed from a fitted specification because its coefficient lacks a star. The full family remains the reference for adjusted inference.\n\n'+rates+'\n'+owner_eq+'\n\\input{tables/behavior}\n')
a=a.replace('Pointwise stars follow the main table.','Pointwise stars follow the complete exploratory table.')
(T/'appendix.tex').write_text(a)
x=(T/'abstract.tex').read_text();x=x.replace('Conditional regressions distinguish net funding from action frequency: utilization is associated with Spark net deposits, whereas the native premium has a less robust relationship with additional-deposit probability and no precise net-flow relationship.','Higher lagged utilization is associated with larger Spark net deposits after correction for the full exploratory test family. An independently named Ethena wallet supplies a second funding-to-claim application through 200 million USDC of ordinary wallet transfers.')
(T/'abstract.tex').write_text(x)
d=pd.read_csv(O/'regression_results.csv').fillna('');m='spark_flow_HAC7';z=d[d.model.eq(m)].set_index('term');lines=[]
for key,label in [('utilization','Utilization, $t-1$ (pp)'),('premium','Native yield premium, $t-1$ (pp)'),('eth_return_pp','ETH return, $t-1$ (pp)'),('eth_volatility_pp','ETH volatility, $t-1$ (pp)'),('spark_lag','Own net deposits, $t-1$'),('log_assets','Log vault assets, $t-1$')]:
 r=z.loc[key];stars=(r'\textsuperscript{'+r.stars+'}') if r.stars else '';lines.extend([label+' & '+f'{r.coefficient:.3f}'+stars+r' \\', ' & '+f'({r.t:.2f})'+r' \\'])
lines+=['Month and weekday effects & Yes'+r' \\','Observations & 319'+r' \\','$R^2$ & 0.196'+r' \\','Holm $p$: utilization & 0.023'+r' \\']
text=r'''\begin{table}[!htbp]\centering
\caption{Treasury net funding and market utilization}\label{tab:treasuryfunding}
\begin{threeparttable}\setstretch{1}
\begin{tabular}{@{}p{9cm}r@{}}\toprule
 & Spark net deposits \\\midrule
'''+ '\n'.join(lines)+r'''
\bottomrule\end{tabular}
\begin{tablenotes}[flushleft]\item \textit{Notes}. The outcome is daily deposits less withdrawals in million USDC. Parentheses report HAC(7) statistics. Stars denote two-sided pointwise probabilities: *** $p<0.01$, ** $p<0.05$, * $p<0.10$. The utilization probability is adjusted across the original eight premium/utilization tests, not a new one-test family. Appendix F retains every equation in that comparison, including imprecise estimates. Controls are unchanged from the full specification. The relation is conditional rather than causal.
\end{tablenotes}\end{threeparttable}\end{table}
'''
(T/'tables/treasury_funding.tex').write_text(text)
(O/'MAIN_TEXT_FOCUS.md').write_text('Main text refocused at user request on supported funding, request-scale and treasury-utilization evidence. Full four-equation table and rate/owner-action models moved to Appendix F. All controls and the original eight-test Holm family preserved; no re-estimation or significance-based specification change. Unsupported incentive/participation claims removed from abstract and conclusion.\n')
