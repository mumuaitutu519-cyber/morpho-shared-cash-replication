# R26 pre-estimation model manifest
Frozen before running revision26_estimate.py, 2026-09-07. Conditional associations, not causal effects.

Main sample: January 16–November 30, 2025 (319 dates). No outcome trimming, winsorizing or significance-driven sample selection.

Four main equations: (1) non-Spark daily net deposits in million USDC; (2) Spark daily net deposits in million USDC; (3) non-Spark incumbent daily withdrawal indicator; (4) non-Spark incumbent daily additional-deposit indicator. The incumbent risk set has opening claim >=1 USDC. Addresses are observational units, not necessarily distinct people or institutions.

Common explanatory variables: previous closing native net-interest APR premium over the equal-weighted two previously selected peer vaults, in percentage points; previous common-market utilization in percentage points; previous ETH log return in percentage points; previous 30-day ETH daily-return standard deviation in percentage points; month and weekday indicators. All incentive information predates outcomes. Native rates exclude unmeasured rewards and do not measure Spark's fee-recipient income.

Daily equations also include the equation's own lagged net deposits and log previous closing vault assets. OLS with HAC 7 days; HAC 14 days is an explicitly labeled covariance sensitivity, not an independent economic model. Report full coefficients and sample.

Incumbent equations additionally include log opening claim and account age in days, owner fixed effects, and two-way owner/date clustered covariance. Owners with only one eligible row are excluded because they provide no within-owner information. Keep multi-day owners with no outcome variation. No full date fixed effects alongside daily incentive regressors. These restrictions leave common omitted time shocks possible.

Eight premium/utilization coefficient tests across the four main equations constitute one Holm family. Pointwise stars use two-sided p values and 10/5/1% thresholds. Do not replace adjusted p values by stars or claim familywise significance from pointwise stars.

Descriptive groups for size: opening claim [1,100), [100,10000), [10000,1000000), >=1000000 USDC; known treasury accounts also shown separately. Cutoff sensitivities >0 and >=100 USDC use the same incumbent model and are reported separately, not added to the primary testing family. No analysis is selected for significance.

Computation: within-owner demeaning for OLS; full absorbed-owner degrees of freedom in small-sample covariance factors. Two-way score covariance = owner + date - owner/date intersection. Reference t degrees of freedom min(number of owners,number of dates)-1. Report covariance diagnostics; do not silently fix negative variance estimates. Check within transformation against explicit owner dummy coefficients on a deterministic subset. Main regressors must have full column rank after transformation. Any departure must be separately logged before interpreting results.
