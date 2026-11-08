# R26 substantive strengthening — active goal, not submission-ready yet

Objective: strengthen the Spark paper to a defensible JIFMIM submission standard, rather than add stars/table counts. No acceptance guarantee, data invention, significant-specification search, or actual submission.

## Completion requirements
1. A unified financial question links source identification, position size and observable investment/exit behavior. Positive contribution relative to Saengchote (2023), rather than generic novelty of on-chain data.
2. Expand evidence beyond the single treasury using validated owner records, without relabeling anonymous addresses as independent institutions. Evaluate whether an independently identified large account can support a second funding path.
3. Ground incentive/risk variables in protocol records. Verify historical rate definitions, fees, native interest and rewards before regression; retain discrepant API fields in audit files.
4. Estimate distinct, economically motivated baseline and heterogeneity analyses, with common samples, explicit inference families and retained null results. Extra covariance columns do not count as separate evidence.
5. Distinguish account liquidity from request-size feasibility and realized exits; validate ownership denominator and shared cash measurements.
6. Rewrite main text, appendix, tables/figures and verified literature; deliver English LaTeX and compiled combined PDF in Ryu format, plus reproducible new inputs/code.
7. Verify current JIFMIM author instructions and prepare a reviewable submission package, then perform a substantive referee-style completion audit. Do not submit, pay, supply unverified author declarations, or declare readiness based merely on compilation.

## Current verified progress
- 145,957 retained vault events reconstructed into 1,012,346 candidate owner-days; 18,967 addresses including transfers; 18,573 deposit beneficiaries.
- No negative end-day balances. Non-Spark aggregate shares reconcile exactly at all 320 direct-state dates after separately retaining the Spark residual.
- 45 independent public-RPC balance checks (5 largest and 10 seeded random positive non-Spark holders on each of March 31, June 30 and November 30) match native integer shares exactly. This is a spot check, not all-address independent recollection.
- Three vaults' daily historical assets, allocations, rates and fee changes collected for the existing window. Native market supply-rate inputs have full funded-position coverage and allocation assets reconcile on every date.
- Generic historical vault `apy/netApy` fields differ greatly from native market-rate reconstruction. At 2025-02-19, API vault APY is 62.8171 versus independently checked common-market native APY about 0.159460; vault allocated entirely there. These generic fields are quarantined from incentive regressions pending interpretation; do not call them native yields or silently winsorize.
- `native_yields.csv` constructs explicit annual continuously compounded native rates by allocation weighting log(1+market supply APY), then applying the recorded performance fee. Net native APR is the core rate unit; do not equate it to fees received by Spark or a separately measured reward APR.
- Within the non-Spark incumbent risk set (prior claim >=1 USDC), 513,949 owner-days and 13,341 addresses; 39 days have cash benchmark below full claim, none below a quarter. This is a cash benchmark, not all-owner execution proof. Owner capacity spot checks differ by at most 0.017944 USDC.

## Next analysis freeze (before estimating new outcome regressions)
Financial comparison: does investment/exit behavior vary with native yield opportunities and liquidity conditions, and is the low fractional coverage of the large treasury representative of ordinary holders?

A. Daily aggregate flow comparison, all 319 original dates: other owners' net vault deposits and Spark net deposits, separately. Main outcome units million USDC. Predictors lagged reconstructed native yield premium over the equally weighted two pre-existing peer vaults, lagged common-market utilization, own lagged net flow, log lagged total assets, ETH return and rolling volatility; calendar controls as declared. Report treasury association with the publicly available depositor opportunity measure, not its all-in fee-inclusive return. HAC(7); HAC(14) only sensitivity. Retain original R25 equation as separate archived benchmark.
B. Incumbent owner-day exit and additional-deposit probabilities, non-Spark, opening claim >=1 USDC, all eligible days including no-action days. Main controls: lagged native premium and utilization, log opening claim, age, market returns/volatility, month/weekday effects and owner effects. Two-way owner/date clustered inference. Outcomes are completed actions, not latent or rejected demand. Account singleton and zero-within-variation handling must be reported. Do not estimate a logistic model for 94 identical successful deposit-equivalent calls.
C. Position-scale comparisons and heterogeneity use observable size, not guessed user identities. Groups are defined from information available before each observation; no classification by future withdrawal outcomes. Show sensitivity at 0 and 100 USDC opening-claim cutoffs, report full selection denominators. Do not select a threshold from significance.
D. Coefficient tests for the premium and utilization across main flow/probability equations form a declared family. Report pointwise stars plus family-adjusted inference and natural-unit magnitudes. No new specifications chosen for stars. Exact model specification and any necessary departures must be recorded before estimation, after checking availability/rank.

## Remaining issues
- Validate native-rate reconstruction beyond three direct common-market snapshots, especially material peer market exposures; clarify reward coverage and API field definitions.
- Build aligned ETH controls, freeze final common estimation samples, and run main models; no new R26 regression has yet been estimated.
- Trace/identify other large holder(s), rather than assume independent institutional identity from address count.
- Complete fee-event ledger if feasible; aggregate localization of the discrepancy is not raw-event classification.
- Refine the theoretical argument and redo literature-to-results comparison after actual estimates; no manuscript-ready claim yet.

## Progress after first R26 estimation and manuscript build
- Four primary equations and two cutoff sensitivities estimated after MODEL_MANIFEST.md. Primary incumbent estimation: 512,978 rows, 12,370 owners, 316 dates after 971 singleton removals. Exact coefficients, covariance and Holm family retained.
- Spark utilization coefficient p=.002889, Holm=.023112. Additional-deposit premium p=.009674, Holm=.067715. Premium net-flow coefficients imprecise. No change to thresholds from significance.
- Six largest-peer-position rate checks complete, including one idle zero-rate market; native inputs validated on these selected dates.
- Ethena Labs' 2025-08-29 attestation identifies wallet b873...313c. Fifteen deposits total about200m; no same-transaction mint in independently collected receipts. Complete earlier funding path not established. SQD bounded scan was stopped for inefficient small pages; Blockscout timed out. Neither is used as a complete ledger.
- All100 eligible Ethena opening states checked for balance/maxWithdraw/convertToAssets. All balances match event records; mincoverage41.3799879%,39belowfull,0belowquarter. Initial asset/share-ratio comparison overcounts tiny belowfull deviations; direct convertToAssets resolves fees and rounding. Use ethena_daily_exact_claims.csv.
- New R26 manuscript + appendix compiled, with owner descriptive table, four-equation main table, size groups, threshold appendix, participation and native yield plots. Earlier allocation table retained in appendix.
- Official guide checked in authenticated institutional browser. Supports LaTeX,250wordabstract,3–5highlights,OptionCdata,125USDsubmissionfee. No submission/payment/public repository publication performed.
- Still active: source path expansion, remaining measurement issues, final evidence/literature integration and portable independent reproduction. REFEREE_AUDIT_CN.md records current limitations. R26 delivery is a substantive revision, not a claim that the active goal is complete.
