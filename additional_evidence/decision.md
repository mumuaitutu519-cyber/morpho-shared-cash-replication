# Analysis specification

Use the supplied 495-holder cohort and exact integer opening claims/capacities/deposits. Preserve all archived changes, including interest and other same-block activity. Transaction fixed effects absorb the common intercept; its zero test is NA. Constrained observations have strictly positive opening gaps. The April 23 cutoff is 2025-04-23.

Use the 439 UTC dates and the prior day's ten-vault asset denominator for Spark net committed Deposit minus Withdraw flows. Fetch January 15 logs for the initial lag. The requested gap outcomes are signed ratios, including negative observations. Use year-month and weekday effects and manuscript HAC7 correction and residual degrees of freedom.

Use positive sample positions in the market-day analysis. Undefined zero-cash duplication/log observations are excluded and counted. Market/date effects and manuscript two-way finite-sample covariance apply. Wild restricted bootstrap-t uses market weights, reabsorbed fixed effects and one-way market studentization as in the manuscript code. Enumerate up to 12 clusters; otherwise use 9999 Rademacher draws with seed 20261002. No model changes based on significance.

For protocol comparisons, identify contracts from canonical factory lists/events and obtain all positions and idle cash at identical finalized blocks. Distinguish chain/token/protocol combinations, active and empty vaults, and nested allocations. Report missing states or unsupported underlying interfaces as missing rather than replacing them with total assets.
