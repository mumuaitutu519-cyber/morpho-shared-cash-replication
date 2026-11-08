# Panel evidence for Counting the same cash

This directory contains the five requested empirical exercises. `Results_report.md` gives sample sizes, coefficient estimates, tests and the accounting interpretation. `outputs/all_estimates.csv`, `all_models.csv`, `all_tests.csv` and `quoteable_values.csv` contain the full numerical record. Manuscript Word/PDF files are unchanged.

## Tables

- Task 1: `task1_numeric.csv`, `task1_paper.csv`, `task1_models.csv`, `task1_tests.csv`, `task1_notes.txt`.
- Task 2: `task2_numeric.csv`, `task2_horizon_paper.csv`, `task2_models.csv`, `task2_notes.txt`; `borrow_event_list.csv` and `event_horizon_grid.csv` identify the observations and blocks. `event_vault_horizons.parquet` and `event_market_horizons.parquet` contain the measured outcomes.
- Task 3: `task3_*` for the ten-vault panel, `task3_cross_*` for the four-chain extension. The two notes files describe timing, inference and observation exclusions.
- Tasks 4–5: `tasks4_5_numeric.csv`, `tasks4_5_paper.csv`, `tasks4_5_models.csv`, `tasks4_5_notes.txt`. `task4_daily_*` also isolates the daily robustness columns.

Coefficients carry stars at 1%, 5% and 10%, with t statistics on separate rows. Logit parentheses contain normal-reference z statistics. Wild p-values are separate rows. Raw amounts are integer micro-USDC; monetary regression variables are million USDC. Data availability and changes in observation counts appear in the status JSON files, not as zero observations.

## Source data and coverage

The ten-vault daily states and position data come from `outputs/empirical/` in the replication root. The market-day sample comes from `additional_evidence/outputs/market_estimation_at_least_2.csv`. The four-chain sample comes from `additional_evidence/cross_chain/outputs/`.

Committed Supply, Repay and Liquidation records use the archived Morpho operation ledger. Withdraw and Borrow records are added through the same Morpho GraphQL operation interface, with saved requests, responses and pagination counts. A separately archived SQD log subset provides an independent source check. `market_operations_cash.parquet` holds the integrated operation ledger, amounts, and cash before each block. `market_cash_reconciliation.csv` compares reconstructed and read balances. Interest implied by the supply stock-flow balance and observed bad debt are kept separate in `supply_stock_flow_reconciliation.csv`.

Event-state RPC reads use the existing collector and paced public archive providers. Every request and response records its source. Event data include block hashes and timestamps; missing states are explicitly listed. Cross-chain net flows use single-vault GraphQL pagination from UTC midnight through the exact census block. `cross_state_flow_validation.csv` compares overlapping Base records against the prior committed chain-log archive.

## Offline reproduction

Run from the `Replication_Package` root with Python 3.12 and numpy, pandas, scipy, statsmodels, pyarrow, requests and pycryptodome installed:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/export_panel_inputs.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/build_panel_operations.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/build_borrow_candidates.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/check_panel_supply_identity.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_panel_spillover.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_panel_prediction.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_cross_state_prediction.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_panel_robustness.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_borrow_events.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/format_panel_evidence.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/report_panel_evidence.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/validate_panel_evidence.py
```

The cached inputs make these commands offline. Online collection scripts are `collect_panel_market_api.py`, `collect_borrow_event_states.py`, `fill_borrow_event_headers.py` and `collect_cross_state_flows.py`. The SQD source-check collector is `collect_panel_operations.py`. Collection scripts resume saved pages/states. `decision.md` fixes variable choices; `log.md` records execution; `checks.md` records validation.
