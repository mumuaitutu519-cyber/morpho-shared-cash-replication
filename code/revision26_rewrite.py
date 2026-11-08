from pathlib import Path
T=Path(__file__).resolve().parents[1]/'submission/jifmim26/en';p=T/'body.tex';s=p.read_text()
s=s.replace('A separate daily panel follows the account, its vault and the common lending market. It describes gross and net flows, estimates conditional allocation equations and compares fixed-state capacity with completed withdrawal sequences.', 'An expanded owner panel compares the treasury with other holders of the same vault. It measures how fractional coverage varies with position size and whether completed actions covary with native interest opportunities. This broader participation sample remains distinct from the source-matched cohort.')
s=s.replace('The contribution is a joint measurement application in a named institution.', 'The contribution connects funding provenance with the size and timing of a claim that can be converted back into cash, and evaluates the scope of that comparison across the vault\'s holders.')
mark='\\subsection{Gross turnover, net flows and the size of the position}'
addition=r'''\subsection{Ownership, participation and native interest}
The retained vault ledger contains 145,957 unique transaction-log records from inception on January 15 through November 30, 2025. Deposit and withdrawal ownership follows the beneficiary rather than the sender or router; share transfers update both owners. The reconstruction contains 18,967 addresses, including 18,573 deposit beneficiaries. Addresses are not presumed to be independent people or institutions. No reconstructed closing balance is negative. After retaining Spark's separately documented share residual, non-Spark aggregate shares reconcile exactly on all 320 daily dates. Forty-five independent RPC balances also match in native integer shares: the five largest and ten seeded random positive non-Spark holders on each of three fixed dates. These checks do not claim independent recollection of every record.

The incumbent sample requires an opening claim of at least 1 USDC and includes no-action days. It contains 513,949 owner-days and 13,341 non-Spark addresses. Removing 971 singleton observations for owner fixed effects leaves 512,978 observations, 12,370 addresses and 316 dates. Owners with constant outcomes remain included. New entries without an opening position appear in the participation series but not the incumbent models.
\input{tables/owner_summary}
\paperfig{participation.pdf}{Vault participation outside the Spark treasury}{fig:participation}{Addresses are beneficiaries and withdrawing owners, not transaction routers. The upper panel includes positive opening balances below the regression cutoff. The lower panel includes all completed actions, including entry deposits.}

Native interest is constructed from allocated positions and market supply rates. For allocation weights $w_{vm,t}$, native market APY $a_{m,t}$ and performance fee $f_{v,t}$, define
\begin{equation}
r^n_{v,t}=(1-f_{v,t})\sum_m w_{vm,t}\log(1+a_{m,t}).
\end{equation}
This is a continuously compounded annual native-interest rate after fees. It excludes unmeasured token rewards and Spark's fee-recipient income. Daily allocations reconcile to assets, and every positive position has a rate observation. Historical contract checks support these market-rate inputs; generic vault APY fields with an unresolved different interpretation are excluded. The premium is Spark minus the equal-weighted Moonwell Flagship USDC and Gauntlet USDC Core native rates, in percentage points. Different portfolio risks mean that this is an opportunity comparison, not a risk-free arbitrage spread.
\paperfig{native_yields.pdf}{Native interest opportunities across the three vaults}{fig:nativeyield}{Observed allocation weights and historical performance fees are applied to native market interest. Annual rates are in percent. Unmeasured rewards and treasury fee income are excluded.}

'''
s=s.replace(mark,addition+mark);start=s.index('\\subsection{Conditional daily allocation}');end=s.index('\\subsection{Fixed-state capacity',start)
s=s[:start]+r'''\subsection{Investment opportunities and completed actions}
The expanded panel distinguishes net funding from the occurrence of an investment action. A large treasury can dominate dollars while smaller owners drive event counts. This comparison follows the incentive perspective of \citet{saengchote2023lending}, while retaining the separate measurement of provenance and executable request size.

For daily net deposits $F_{g,t}$ by Spark or other owners, estimate
\begin{equation}
F_{g,t}=\alpha_g+\beta_g p_{t-1}+\gamma_g u_{t-1}+\rho_g F_{g,t-1}
+\theta_g'X_{t-1}+\delta_{g,m(t)}+\eta_{g,w(t)}+\varepsilon_{g,t}.
\end{equation}
$p$ is native yield premium and $u$ utilization, both in percentage points. $X$ contains log vault assets, ETH log return and 30-day daily-return volatility. Net flows are million USDC. Both equations use 319 dates and seven-day HAC covariance.

For non-Spark incumbent $h$, the completed withdrawal or additional-deposit indicator satisfies the linear probability specification
\begin{equation}
A_{h,t}=\alpha_h+\beta p_{t-1}+\gamma u_{t-1}+\lambda\log Q_{h,t-1}
+\kappa\operatorname{age}_{h,t}+\phi'Z_{t-1}+\delta_{m(t)}+\eta_{w(t)}+e_{h,t}.
\end{equation}
$Q$ is opening claim, age is days since the first observed owner event, and $Z$ contains ETH return and volatility. Owner effects absorb time-invariant differences. Month and weekday effects leave daily incentive variation identifiable. Inference clusters by owner and date. Full date effects would absorb the common rate variables; omitted daily shocks and endogenous market conditions therefore remain possible explanations.
\input{tables/behavior}

Neither flow equation has a precise native-premium coefficient. Spark's utilization coefficient is 0.377 million USDC per percentage point: a ten-point difference corresponds to 3.771 million more net deposits, conditional on controls. Its pointwise probability is 0.0029 and its Holm probability is 0.0231 across the eight focal tests. The non-Spark coefficient is smaller and imprecise. This does not identify an exogenous utilization shock or establish liquidity provision on demand.

For completed additional deposits, a one-percentage-point larger premium is associated with a 0.229-percentage-point higher probability. The pointwise probability is 0.0097, but the Holm probability is 0.0677. This is about one tenth of the unconditional eligible deposit frequency of 2.142 percent, a scale comparison rather than a causal baseline. The premium has no precise association with withdrawal probability. Utilization is negatively associated with completed withdrawal probability at the pointwise five-percent level, but its adjusted probability is 0.1331. Completed actions cannot distinguish portfolio choices, deferred intentions and unmet private demand.

The eight premium/utilization tests were grouped before estimation. Table \ref{tab:behavior} reports stars and adjusted probabilities separately. Appendix \ref{app:owners26} retains fixed opening-claim sensitivities and the earlier allocation equations, including weak results. Bandwidth changes do not count as separate economic evidence.

\subsection{Position size and the scope of treasury evidence}
Table \ref{tab:ownersize} groups accounts using opening claims, without future information. Of 513,949 eligible non-Spark owner-days, only 39 have cash benchmarks below the full claim; none has coverage below 25 percent. All 39 belong to one address. Spark's directly tested quarter-claim request, by comparison, is constrained in 247 states. Low fractional coverage thus concerns concentrated large claims in this vault rather than the typical small holder.
\input{tables/owner_size}

The second large address is identified in Ethena Labs' August 2025 asset attestation as Coinbase Web3 Wallet 3 \citep{ethena2025}. The ledger records approximately 200 million USDC of deposits on August 22--27 and withdrawals in October. Its minimum incumbent cash-benchmark coverage is 41.38 percent. This is an independently named ownership comparison within the same vault, not a random institutional sample. None of its 15 deposit receipts contains a same-transaction USDC mint to the owner. The deposits are therefore not relabeled as a second CCTP-funded cohort; their earlier funding path remains outside the verified sample.

This evidence also clarifies the first-use boundary. Another large institution's deposits can be separate wallet-to-vault operations. A bundled-arrival method cannot recover their origin merely by observing the deposit. The owner panel strengthens the claim-size comparison while preserving the source-attribution restriction.

'''+s[end:]
s=s.replace('The daily data place these findings within a conventional empirical description of investment activity: gross turnover, net allocation, account holdings and market conditions. Conditional regressions do not establish systematic replenishment by the vault.', 'The expanded owner panel places the treasury evidence in context. Other holders rarely have cash coverage below their whole claim, and the independently identified Ethena wallet accounts for all such observations outside Spark. Utilization covaries with Spark net deposits; the native premium has a less robust relationship with additional-deposit frequency and no precise net-flow relationship. These are heterogeneous participation patterns within one vault, not representative institutional effects.')
s=s.replace('Extending its institutional implications requires independently identified accounts and their own funding and execution records.', 'The second named holder extends the ownership comparison but does not yet supply a verified independent cross-chain funding path.')
p.write_text(s)
(T/'abstract.tex').write_text('Cross-chain funding and withdrawal capacity describe different dimensions of an investment claim. Evidence from the Spark vault links 94 same-transaction deposits to funding constraints and deposit-sized exit tests, and places the treasury within an expanded owner panel. Feasible arrival funding is 471.788--489.891 million USDC for deposits totaling 490.826 million. All deposit-equivalent simulations succeed at block end, including 68 low account-coverage states. Yet quarter-claim requests are constrained in 247 of 319 treasury states. Among 513,949 eligible non-Spark owner-days, none has cash-benchmark coverage below a quarter; 39 below-full-coverage observations belong to an independently identified Ethena wallet. Conditional regressions distinguish net funding from action frequency: utilization is associated with Spark net deposits, whereas the native premium has a less robust relationship with additional-deposit probability and no precise net-flow relationship. The findings connect provenance, claim size and payment timing within one vault, without equating completed actions with latent withdrawal demand.\n')
a=T/'appendix.tex';a.write_text(a.read_text()+r'''
\section{Expanded Owner Panel and Rate Validation}\label{app:owners26}
The reconstruction uses integer shares. Deposits and withdrawals change the beneficiary's holdings; nonzero-address transfers change both affected owners. The API omits some zero-address fee mints. Exact non-Spark aggregate reconciliation therefore does not classify Spark's remaining discrepancy as fees. The independent 45-owner spot checks match integer balances on March 31, June 30 and November 30. Cash-benchmark predictions differ from queried capacities by at most 0.017944 USDC. The direct/API vault asset comparison differs by at most 2.034 USDC; this boundary difference remains in the audit.

The probability models demean outcomes and regressors by owner. Singleton rows are excluded; constant-outcome owners remain. Covariance equals owner-cluster plus date-cluster score covariance less the intersection term, with degrees-of-freedom factors including absorbed owners. Reference t degrees of freedom equal the smaller cluster count minus one. Main models have 316 date clusters. A deterministic 20-owner explicit-dummy comparison checks the within transformation. All model covariance diagnostics and coefficients are retained.
\input{tables/owner_sensitivity}

Fees are sampled at the actual rate snapshot boundary. Generic APY fields remain archived because they differ from native interest: February 19 generic Spark APY is 62.8171 in decimal units, versus approximately 0.159460 for native common-market APY. The regression neither trims this discrepancy nor interprets it as rewards. Three direct common-market IRM checks agree with market API values within approximately $1.1\times10^{-7}$ decimal APY. Six peer checks select each portfolio's largest market on the same dates; one is an idle zero-rate market. These are bounded checks, not independent recollection of every market-date.

The eight main premium/utilization tests constitute one family. Cutoff and bandwidth sensitivities do not redefine it. Size groups use opening claims and can contain the same owner on different dates. Ethena's identity comes from its dated attestation, not a guess from address size.

\subsection{Retained original allocation benchmark}
The earlier allocation table retains its weak and null findings. Column (3) changes only covariance bandwidth. Its original within-model adjustment is separate from the new eight-test family.
\input{tables/allocation}
''')
r=T/'references.tex';r.write_text(r.read_text().replace('\\end{thebibliography}',r'\bibitem[Ethena Labs(2025)]{ethena2025} Ethena Labs, 2025. Custodian attestations of assets backing USDe: August. August 29. \url{https://paragraph.com/@ethena-labs/custodian-attestations-of-assets-backing-usde-august-2}.'+'\n'+r'\end{thebibliography}'))
