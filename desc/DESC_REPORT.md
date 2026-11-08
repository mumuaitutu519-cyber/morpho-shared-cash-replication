# Descriptive statistics — Counting the same cash

All six panels use saved regression-ready observations and the corresponding estimator's complete-case filters, before fixed-effect absorption. No raw contract states are read and no regression is re-estimated. SD is the sample standard deviation (ddof=1); P25, P50 and P75 are ordinary sample quantiles with linear interpolation (NumPy default; P25/P75 explicitly use method="linear"). Shares are fractions, not percentages; utilization is in 10-percentage-point units. Natural logs and million-USDC scales retain the exact stored regression convention. No winsorization or additional exclusions are introduced.

`desc_stats.csv` has the requested ten columns, variable order and display precision. `desc_stats_unrounded.csv` preserves full precision. Non-count statistics use three decimals when absolute value is below 10, two when it is at least 10 but below 100, and one when it is at least 100. Count variables (Markets, Vaults) use two decimals for mean/SD and integers for min/P25/P50/P75/max, except fractional P25/P75 retain one decimal. `sample_counts.csv`, `variable_map.csv`, `sample_keys_*.csv`, `input_manifest.json` and `validation.json` provide inspectable sample identities and provenance.

| panel | expected | actual | status |
| --- | --- | --- | --- |
| A | 439 | 439 | MATCH |
| B | 4387 | 4387 | MATCH |
| C | 3167 | 3167 | MATCH |
| D | 2141 | 2141 | MATCH |
| E | 4380 | 4380 | MATCH |
| F | 834 | 834 | MATCH |

## Panel A

Expected observations: 439; selected: 439. **MATCH**.

New Table 3 columns (1)–(2), old Table 3 Panel A. Dup and JA are contemporaneous outcomes; HHI, Size, Util and Flow use the stored L_ regressors (previous day). The two columns have the same 439 dates. Dup's regression omits Flow, but its summary here is on the same common sample. Flow is committed Spark net flow / total ten-vault assets, retaining the regression's sign. This panel uses the ready-made daily_estimation_data.csv; no additional shift is applied.

Source: `additional_evidence/outputs/daily_estimation_data.csv`.

Regression script(s): `code/empirical/estimate.py`, `additional_evidence/code/estimate_additions.py`.

| Variable | Unit | N | Mean | SD | Min | P25 | Median | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dup | share | 439 | 0.584 | 0.071 | 0.347 | 0.540 | 0.579 | 0.644 | 0.752 |
| JA | share | 439 | 0.154 | 0.060 | 0.052 | 0.111 | 0.131 | 0.179 | 0.429 |
| HHI | share | 439 | 0.837 | 0.165 | 0.219 | 0.803 | 0.906 | 0.944 | 0.985 |
| Size | log USDC | 439 | 19.92 | 0.821 | 18.13 | 19.09 | 20.31 | 20.60 | 20.84 |
| Util | per 10 pp | 439 | 8.783 | 0.393 | 6.389 | 8.736 | 8.957 | 9.000 | 9.506 |
| Flow | share | 439 | 0.004 | 0.026 | -0.228 | -0.003 | 0.000 | 0.009 | 0.150 |

## Panel B

Expected observations: 4,387; selected: 4,387. **MATCH**.

New Table 3 column (3). Apply fit_fe('II_B') finite complete-case selection to D, shared_exposure, log_assets, active_markets, vault and date, sorted by vault/date. From 4,390 candidate rows this removes three undefined-D/zero-standalone-capacity rows. No lag is added and no fixed-effect demeaning is applied to descriptive values.

Source: `outputs/empirical/estimation_panel.parquet`.

Regression script(s): `code/empirical/estimate.py`.

| Variable | Unit | N | Mean | SD | Min | P25 | Median | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D | share | 4387 | 0.779 | 0.377 | 0.000 | 0.797 | 0.998 | 1.000 | 1.000 |
| Shared | share | 4387 | 0.756 | 0.383 | 0.000 | 0.615 | 1.000 | 1.000 | 1.000 |
| Size | log USDC | 4387 | 15.03 | 2.957 | 7.951 | 13.64 | 15.26 | 16.98 | 20.43 |
| Markets | count | 4387 | 4.19 | 2.59 | 1 | 2 | 4 | 5 | 12 |

## Panel C

Expected observations: 3,167; selected: 3,167. **MATCH**.

New Table 3 column (4) and Table B2. The saved at-least-two-vault estimation file already enforces positive holdings, at least two holding vaults, finite duplication and all regressors. Reapply complete-case selection to outcome, four terms, market and date; no rows are dropped. Zero idle cash gives undefined log_cash and is excluded upstream. Top is largest selected-vault position / total market supply, not position concentration among the selected vaults. Cash is the stored ln(cash_micro / 1e6), i.e. ln(USDC), even though one archived robustness note loosely calls it log million USDC. The script and stored values govern.

Source: `additional_evidence/outputs/market_estimation_at_least_2.csv`.

Regression script(s): `additional_evidence/code/estimate_additions.py`, `additional_evidence/code/estimate_panel_robustness.py`.

| Variable | Unit | N | Mean | SD | Min | P25 | Median | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MDup | share | 3167 | 0.382 | 0.264 | 0.000 | 0.051 | 0.500 | 0.604 | 0.833 |
| Vaults | count | 3167 | 3.84 | 2.08 | 2 | 2 | 3 | 5 | 9 |
| Util | per 10 pp | 3167 | 8.417 | 1.679 | 0.000 | 8.564 | 8.994 | 9.025 | 10.000 |
| Cash | log USDC | 3167 | 12.18 | 3.078 | -10.01 | 10.09 | 11.78 | 13.35 | 19.62 |
| Top | share | 3167 | 0.527 | 0.297 | 0.000 | 0.293 | 0.521 | 0.789 | 1.000 |

## Panel D

Expected observations: 2,141; selected: 2,141. **MATCH**.

New Table 4 column (2): b_chain_state_FE. Read the saved positive-asset vault-state panel, exclude zero_S, then verify D plus all five regressors are finite as the original script asserts. All seven census dates and four chains are pooled. Retain singleton vault entities as the original estimator does; no singleton removal is introduced. Top is the largest market position / the vault's total positive positions.

Source: `additional_evidence/cross_chain/outputs/vault_state_panel.csv`.

Regression script(s): `additional_evidence/code/estimate_cross_chain.py`.

| Variable | Unit | N | Mean | SD | Min | P25 | Median | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D | share | 2141 | 0.701 | 0.442 | 0.000 | 0.001 | 1.000 | 1.000 | 1.000 |
| Shared | share | 2141 | 0.827 | 0.365 | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Markets | count | 2141 | 2.60 | 2.79 | 1 | 1 | 2 | 3 | 24 |
| Size | log USDC | 2141 | 4.896 | 8.484 | -13.82 | 0.180 | 4.495 | 11.94 | 19.99 |
| Util | per 10 pp | 2141 | 7.044 | 3.341 | 0.000 | 7.394 | 8.665 | 9.018 | 10.00 |
| Top | share | 2141 | 0.869 | 0.216 | 0.149 | 0.787 | 1.000 | 1.000 | 1.000 |

## Panel E

Expected observations: 4,380; selected: 4,380. **MATCH**.

New Table 8, old Table 7. Use the common 4,380-row sample of specifications 1a and 1b from the saved spillover_panel, including their outcome, terms, opening exposure and interaction. Consecutive changes within 439 closes supply 438 dates × ten vaults. ΔS maps to dW: change in standalone withdrawal capacity. All five flow/amount variables are already million USDC; do not divide them again. BorrowFlow retains the original signed net borrower-liquidity-flow definition. Shared is the opening ExposureShare. Column 1c (Own=0) and column 1d (ΔD) have smaller samples and are not substituted for the requested common baseline sample.

Source: `additional_evidence/panel_evidence/outputs/spillover_panel.parquet`.

Regression script(s): `additional_evidence/code/estimate_panel_spillover.py`, `additional_evidence/code/panel_evidence_stats.py`.

| Variable | Unit | N | Mean | SD | Min | P25 | Median | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ΔS | million USDC | 4380 | 0.050 | 7.966 | -111.6 | -0.159 | 0.000 | 0.152 | 191.4 |
| Own | million USDC | 4380 | 0.121 | 4.847 | -102.9 | -0.099 | 0.000 | 0.117 | 102.4 |
| Peer | million USDC | 4380 | 0.796 | 12.85 | -136.8 | -0.866 | 0.253 | 4.048 | 117.9 |
| Outside | million USDC | 4380 | 1.046 | 12.76 | -130.1 | -0.901 | 0.000 | 1.546 | 179.0 |
| Borrow | million USDC | 4380 | 2.449 | 4.249 | -46.52 | 0.027 | 2.046 | 4.444 | 30.81 |
| Shared | share | 4380 | 0.755 | 0.383 | 0.000 | 0.609 | 1.000 | 1.000 | 1.000 |

## Panel F

Expected observations: 834; selected: 834. **MATCH**.

New Table 9, old Table 8. Retain real borrow events only, complete nine-horizon panels separately for delta_market_duplication and joint_million exactly as estimate_borrow_events.py does, then take the event-block row. MDup describes the event-block LEVEL on the 651-event duplication-regression sample, not delta_market_duplication. J describes the event-block LEVEL J_micro / 1e12 on the 834-event cash-regression sample, not joint_million (which is a change). Vaults is the uncentered count at the preceding block carried across all horizon rows, on those 834 events. Event-block MDup alone is defined for 763 events, but using all 763 would violate the regression complete-panel filter. The prior discussant boundary correction is not imposed: this task preserves the existing regression sample.

Source: `additional_evidence/panel_evidence/outputs/event_market_horizons.parquet`.

Regression script(s): `additional_evidence/code/estimate_borrow_events.py`, `additional_evidence/code/panel_evidence_stats.py`.

| Variable | Unit | N | Mean | SD | Min | P25 | Median | P75 | Max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MDup | share | 651 | 0.216 | 0.285 | 0.000 | 0.000 | 0.000 | 0.502 | 0.789 |
| J | million USDC | 834 | 0.425 | 2.671 | 0.000 | 0.002 | 0.014 | 0.105 | 43.12 |
| Vaults | count | 834 | 2.06 | 1.53 | 1 | 1 | 1 | 3 | 8 |

## Previous-output preservation

All previously reported columns (panel, variable, n, mean, sd, min, p50, max) are numerically unchanged in the full-precision output, with the same row order. The estimation-sample key files are byte-identical to the pre-extension baseline. Only P25 and P75 are added. The requested NEW display precision changes some strings in desc_stats.csv (for example, a magnitude of 19.915 is now displayed with two decimals); this formatting change does not change the underlying previously reported statistic. The original CSVs and script are retained in desc/before_percentiles/. Hash checks confirm that none of the ten tracked regression coefficient/metadata files changed, both during this run and relative to the pre-percentile baseline. No regression was rerun.

## Reproduce and preservation check

Run `python code/09_desc_stats.py` from the replication-package root. The package's `run_replication.py` now registers this script as its last job. The original runner is archived as `desc/run_replication.before.py`; the change adds the descriptive stage and makes its final job count dynamic. The upstream regression stages were not rerun during this descriptive-only task.

The script reads only frozen estimation inputs; if a panel raises an error it records the reason and continues to the other panels. The existing inputs support all six requested samples; Panel F's variable-specific 651/834 counts are intentional. `validation.json` checks sample counts, frozen model metadata and byte-for-byte preservation of ten regression coefficient/metadata files. The four daily lags are also independently reconciled against frozen derived daily levels and committed-flow summaries, including the pre-sample 15 January observation. Negative logs in panels C/D are retained: positive balances below one USDC have negative natural logs. Input files and original regression scripts are SHA-256 pinned in `input_manifest.json`.
