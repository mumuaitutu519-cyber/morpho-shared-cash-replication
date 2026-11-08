# Counting the same cash: replication package

The package contains the Word manuscript, archived blockchain observations, market and owner panels, executable estimation programs, figures, and verification records. All empirical observations are real contract or public API observations. Tables IV–VI are calculated from the archived same-block states in this package.

## Run

Use Python 3.12 or a compatible environment; the recorded environment is in `verification/environment.json`.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python run_replication.py
```

Keep `Counting_the_same_cash.docx` beside the `Replication_Package` directory, as distributed. The runner executes 23 computations with network connections disabled, including reconstruction from raw RPC responses, all exposure regressions, independent coefficient/covariance checks, all rolling correlations, and manuscript checks. Logs and exit codes are under `verification/run_logs/` and `verification/run_status.json`. `verification/table_map.csv` identifies each table's source. `../SHA256SUMS.txt` records every distributed file hash. Running the package regenerates outputs and verification records.

## Observations and measurement

The main panel covers 10 fixed Base USDC vaults for 439 days, 16 January 2025–30 March 2026, with 33 markets having positive selected-vault positions during this window. The 15 January block supplies one lag. The 319-day descriptive window ends on 30 November 2025 and contains 31 markets. `raw/chain_panel/` contains 456 complete same-block request/response records: 440 daily blocks and 16 September capture blocks. `code/empirical/redecode.py` rebuilds every decoded state from those records without contacting an endpoint. The online collector is provided separately and is not called by the reproduction runner.

Aggregate vault cash capacity W is computed over the withdrawal queue from accrued positions, market cash, and the Morpho token balance. It has no owner argument. An owner's maxWithdraw is the smaller of the converted owner claim and available capacity. The package validates 320 archived Spark owner-day calls against this mapping with zero micro-USDC discrepancy. Asset accounting reconciles exactly after separating the V1.1 lostAssets ledger.

D_v is the fraction of standalone capacity that other selected vaults can exhaust before vault v withdraws: [S_v − (J(V) − J(V excluding v))]/S_v. It is undefined when S_v is zero; three primary rows have this status. It is not an additive allocation of aggregate S−J. Standardized 5%, 10%, and 25% requests compare a fixed fraction of total assets with available capacity; they are not records of submitted transactions.

Tables IV–VI use `code/empirical/estimate.py`. Table V is a linear probability model with vault and date effects, actual model-specific sample sizes, two-way clustered standard errors, and in-sample AUC. The restricted wild-cluster enumeration is an inference calculation on the observed panel. It creates no empirical observations. Common daily ETH volatility is absorbed by date effects and is not estimated as a separate coefficient. Table VI's 30-calendar-day correlations require all 30 valid daily changes. Its full model has 12,538 pair-days, 37 pairs, and 410 dates. Attrition and rank checks are distributed.

## September observations

Fifteen valid daily API files cover 15 collection dates and 150 vault-date observations. A sixteenth file dated 15 September is empty and is preserved under `raw/failed_collections/`; it contributes no observation. `verification/review/public_source_inventory.json` records this distinction.

The 8 September 04:37:23.742381 UTC GraphQL capture and the 05:06:52.494515 UTC capture are separate observations. API objects contain different indexing blocks. Table I uses one synchronized chain state at block 51027334 (05:06:55 UTC). Table S14 separates API totals from synchronized chain cash totals. The 28 September synchronized state is block 51891194 (05:02:15 UTC).

Extrafi's 433,208.022341 USDC asset residual is exactly its lostAssets accounting ledger; its identified positions and idle token balance are zero. The API-only decoder in `code/public_snapshots.py` retains blank joint-cash fields because its mixed-block objects alone do not establish an atomic allocation. The complete synchronized results are generated separately by `code/empirical/snapshot_audit.py` and stored in `outputs/empirical/synchronized_snapshots.csv`. These are different measurements, not zero-filled versions of the same field.

## Files

- `raw/`: frozen RPC and public API responses, timestamps, block hashes, official source code and failed-collection inventory.
- `data/`, `reports/`: prepared market, transaction and owner panels. Owner regressions use the supplied frozen owner-day panel.
- `outputs/empirical/`: same-block panels, model estimates, inference results, synchronized snapshots and attrition checks.
- `code/empirical/`: raw-response reconstruction, panel construction, estimation and independent checks.
- `figures/`, `tables/`: supporting figures and table inputs.
- `verification/`: numerical, manuscript, format and release checks. Review decisions and source provenance are in `verification/review/`.

## Main-text evidence

The manuscript contains six main tables and five main figures. Table I uses all 439 dates in its primary panel. Table II covers the two-chain census and capacity-to-asset ratios. Table III reports individual passes and same-state joint-budget exclusions. Table VII reports actual cross-vault states around the deposit block; Tables VIII–IX report holder execution and persistence. See `joint_review/README.md` and `enrichment/README.md` for inputs and commands. Tables IV–VI retain all exposure estimates and settings, Table S15 the immediate peer comparison, and Table S16 the 319-day case-window cash medians.

The 22-job runner rebuilds chain states, panels, regressions, joint request counts, cross-vault states and holder paths with networking disabled. The Word and PDF beside this directory contain the same manuscript. Author-facing decisions and response notes are separate from the paper.

## Current Table 1: six regression-sample descriptive panels

Run `python code/09_desc_stats.py` to generate `desc/desc_stats.csv` and `desc/DESC_REPORT.md` from the frozen regression-ready panels. This is also the last stage of `run_replication.py`. Samples are 439 days, 4,387 vault-days, 3,167 market-days, 2,141 four-chain vault-states, 4,380 daily changes, and 834 borrow events (651 in the complete duplication-outcome sample). The CSV retains the actual lagged daily regressors and regression units. Existing regression outputs are not modified by the descriptive stage.
