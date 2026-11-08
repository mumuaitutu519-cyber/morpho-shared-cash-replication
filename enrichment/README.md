# Joint cash scope and peer capacity

Table II, Table S15, Figures 1 and 3, and Figure S8 use observed contract states and archived transactions. No artificial observations are created.

- Base: 162 API-enumerated positive native-USDC V1 vaults, block 51953448, 2026-09-29 15:37:23 UTC.
- Ethereum: 146 API-enumerated positive native-USDC V1 vaults, block 26084069, 2026-09-29 15:37:59 UTC.
- Daily plot: the fixed ten-vault Base cohort, 439 dates, 2025-01-16 through 2026-03-30.
- Peer response: all 495 eligible unchanged-share positive-claim peer observations around the 93 matched transactions in the archived cohort. All 17 initially constrained observations concern Ethena.

From the Replication_Package root:

```bash
python enrichment/code/redecode_census.py
python enrichment/code/analyze.py
python enrichment/code/verify_extension.py
```

The main `run_replication.py` includes these jobs with networking disabled. `redecode_census.py` validates exact archived RPC requests and rebuilds decoded states. `analyze.py` reconciles each vault's assets, recalculates the two chain totals, builds the event comparison from the full archived state panel, and produces figures and plot data. `verify_extension.py` checks table cells, narrative magnitudes, captions, model-setting rows and embedded images.

Online collection is separate:

```bash
python enrichment/code/collect_census.py --chain 1 --destination /absolute/path/new_ethereum_capture
python enrichment/code/collect_census.py --chain 8453 --destination /absolute/path/new_base_capture
```

The destination must be new. API pagination is checked before selecting positive native-USDC vaults. Each chain uses one finalized block. The selection describes the complete returned V1 API enumeration, not all DeFi vault standards or protocols. Raw files preserve RPC payloads, responses, block hashes and retrieval times. Queue markets with zero selected-vault positions are retained in reconstruction; the paper reports only positive-position market counts.

The initial ten-vault Ethereum probe is an exploration record and does not enter Table II or Table S15. `log.md` and `decision.md` distinguish exploration from the evidence selected for the manuscript. `literature_benchmark.md` records the exact primary-source versions used for table and figure comparisons. Third-party paper PDFs are not redistributed.
