# R32: user-requested transformations after R31
This is a disclosed post-result robustness extension. R31's four interactions are negative and the exclusion diagnostics have been seen. Do not describe this extension as preregistered confirmation.

Keep R31's 7,650-hour sample, outcomes (following 1/6-hour gross and net deposits), controls, date/hour fixed effects and temporal ordering unchanged. Compare exactly three additional variants, with no search for further cutoffs:

1. Two-sided 0.5/99.5-percent winsorization.
2. Two-sided 1/99-percent winsorization.
3. asinh(x) on each flow in fixed units of million USDC, including signed net outcomes; cash keeps the original log tightness measure.

Winsorize each primitive regression flow, hour-opening cash and each constructed horizon outcome using the same full common sample. Retain all rows. Compute cash tightness from capped opening cash with the original full-sample centering/scaling constants. Construct withdrawal × tightness only AFTER transformation. Do not separately cap the product. Aggregate withdrawals are transformed after beneficiary aggregation; alternative non-Ethena withdrawals receive the same stated rule. Transforming outcomes means these specifications target capped/transformed outcomes, not raw dollar totals; their coefficients must not replace level coefficients without explanation.

Use HAC24 and HAC168 as before. Report all 12 new focal interaction tests, Holm12 and combined adjustment across the 16 original+new transformation-family tests; also retain combined historical48 adjustment. Report the amount/number of observations affected, especially the share of withdrawal dollars above each cap. No additional data-dependent cutoffs.

For every transformation, retain fixed diagnostics excluding October4–5, excluding all October, and using non-Ethena withdrawals with Ethena separately controlled. No diagnostic becomes the replacement main result. A positive significant isolated transformed coefficient is not enough to assert a general dollar liquidity support mechanism, especially if the transformation removes economically central large flows.
