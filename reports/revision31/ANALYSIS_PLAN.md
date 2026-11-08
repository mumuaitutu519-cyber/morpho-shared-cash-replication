# R31: bounded exploratory interaction test
Written before estimating the new regressions. Prior transaction illustrations have already been inspected, so this is exploratory, not an independent confirmatory study.

Question: Do other vault holders' withdrawals predict greater subsequent Spark treasury replenishment when opening market cash is scarce?

Fixed sample: every UTC hour in the existing 16 January–30 November 2025 period, including zero-event hours. Use a common sample with all six following hours observed. No additional institution, favorable date selection or significance-driven transformation.

Predictors for hour t: other vault beneficiaries' gross withdrawals (million USDC), cash tightness = negative log(1 + opening common-market cash in million USDC), standardized using the common full sample, and their interaction. Opening cash strictly precedes hour t; it is not post-withdrawal cash. Other beneficiaries are onBehalf != the known Spark treasury, not inferred persons. The complete vault ledger includes Ethena and all other observed beneficiaries.

Outcomes: treasury gross deposits and net deposits in the next hour (primary); cumulative values in the next six hours (secondary). Subsequent windows exclude the predictor hour, guaranteeing measured time ordering, but missing responses within that hour. Outcome treasury flows include all beneficiary events, not only strictly matched market supplies; the interpretation is vault funding.

Identical controls: other-beneficiary deposits, market borrowing, repayments including liquidation repayments, and treasury gross deposits and withdrawals during hour t. Include predictor-date and hour-of-day fixed effects. All four outcomes have the same X and sample. OLS in levels preserves cash magnitudes; interactions are associations, not exogenous shocks or behavioral counterfactuals.

Inference: HAC with 24 hourly lags, sensitivity 168 lags, with absorbed-FE degrees of freedom counted. Four focal interaction tests constitute one family, reported with Holm adjustment. Also report adjustment jointly with the 32 recorded earlier exploratory tests; no historical p-values are overwritten. No stars substituted for economic magnitudes. Report withdrawal slopes at tightness quartiles, their joint-covariance uncertainty, and descriptive support of the interaction.

Fixed influence checks for both primary outcomes: exclude October 4–5 predictor and response windows; exclude each calendar month in turn (also windows crossing into it); replace other withdrawals with non-Ethena beneficiaries (Ethena withdrawals separately controlled). These are diagnostics, not replacement main models. Preserve all results even if unsupported.

Admission: a positive point estimate alone does not justify a mechanism claim. Give particular weight to adjusted primary evidence, whether gross replenishment also represents net funding, and stability beyond the illustrated dates. If evidence is weak or driven by a few events, do not add a supportive mechanism regression to the manuscript. Preserve the analysis archive and explain that the broader hypothesis is unestablished. No searching alternative cutoffs or horizons after observing results.
