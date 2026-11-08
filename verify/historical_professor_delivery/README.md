# Counting the same cash — Professor review with data

The package contains the supplied Sun_13 Word manuscript, result tables, figure panels, analysis code and underlying analysis datasets.

## Start with the data
- Replication_Package/outputs/empirical/: daily vault and position panels, daily aggregates, regression design panels and model results.
- Replication_Package/additional_evidence/cross_chain/outputs/: four-chain vault-state and position panels, mechanism observations and results.
- Replication_Package/additional_evidence/outputs/: mechanism observations, market-day estimation data, daily controls, Spark flows and cross-protocol positions.
- Replication_Package/additional_evidence/panel_evidence/outputs/: spillover panel, prediction panel, borrow-event list, nine-horizon event data and all estimates.
- Replication_Package/additional_evidence/panel_evidence/raw/event_states/: decoded observed block states used to reconstruct event outcomes.
- Replication_Package/real_consequences/outputs/: actual failure calls, cleaned events, waiting times, market states and descriptive tables.
- Replication_Package/results/figures/panels/: nine PNG and nine PDF figure panels.

DATA_INVENTORY.csv lists the included data files, bytes and tabular row counts. Read each analysis module's notes and README for units, samples and commands. The package includes decoded on-chain states and constructed estimation inputs; bulk API responses and the complete operation-log archive remain in the full replication package. Raw-data collectors and full-ledger rebuilding steps require those omitted files; the included estimation panels are available for inspecting and rerunning the corresponding regressions.

The manuscript comparison file retains 132 matched coefficient/t-statistic pairs. Existing validation records describe the completed full-package runs; this review package preserves their results. No data values or estimates were changed when selecting files. SHA256SUMS.json records every file included here except the manifest itself.
