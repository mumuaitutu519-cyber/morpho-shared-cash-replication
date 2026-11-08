# Joint cash budgets and exit capacity

Main Tables I–IX follow the contribution from full-period measurement to joint request assessment, cross-vault states, holder execution and the duration of relief. Tables IV–VI report the complete exposure regressions in main Section 5.2; Table S15 preserves the immediate peer comparison; Table S16 preserves the 319-day historical medians.

## Offline commands

From Replication_Package:

```
python joint_review/code/cross_vault_states.py
python joint_review/code/analyze.py
python joint_review/code/verify_manuscript.py
```

The main runner includes these commands with networking disabled. The first reconstructs exact block-state requests from archived public RPC responses. The second computes every request in integer micro-USDC and verifies all 4,390 comparisons between standalone and queue capacity; it reconstructs the deposit-block vault panel and the fixed 17-position holder paths. The third checks 113 new or expanded table cells and the corresponding narrative magnitudes and references.

## Populations and outcomes

- The request panel contains the same ten selected vaults on all 439 dates. Each request is floor(f * totalAssets), for f = 5%, 10%, 25%. An individual pass requires every request to fit its vault capacity. An exclusion additionally requires the sum to exceed the joint cash upper bound. Dates below the upper bound are labeled not excluded, not executable.
- The cross-vault panel queries all ten vaults at Base blocks 36,399,031 and 36,399,032. Nine have positive supply in the cbBTC/USDC market. Exact integer market shares and vault share supply are retained. Main Table VII displays those nine; the CSV retains Pyth as well.
- The holder-path panel fixes the 17 initially constrained observations selected before inspecting their later paths. Later states include all intervening operations; changed-share observations are identified separately.
- Online collection is optional and explicitly enabled with `--online`; the offline runner never calls an endpoint.

`log.md` records exploration; `decision.md` records placement and interpretation decisions. `checks.md` records delivery validation. No simulated observations are added.

Second-review outputs include excluded/all-date shares, conditional deficit/request medians and exact common-market aggregates in `outputs/common_market_aggregate.csv`. Figure 2 uses the median across same-size subsets within each day, followed by the median across days.
