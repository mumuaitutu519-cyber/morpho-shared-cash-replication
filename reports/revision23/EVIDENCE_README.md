# R23 anonymous reviewer evidence: raw records, prepared inputs, and replay

Run `python replay_r23.py` in a fresh extracted directory after installing
`requirements-reproduction.txt`. The runner disables networking and runs the
retained R21 and R22 central checks before the R23 calculations and audit.
No credentials, new network requests, or unstated files are required.

## Immediate inputs versus raw origins

| Result | Immediate input | Raw/source validation retained in replay |
| --- | --- | --- |
| First-deposit funding | `reports/revision6/domain_6_first_disposition_manifest.json`: prepared ordered transaction frames and balances; R22 prepared operation records | Raw USDC block logs, balance-call payloads and receipts are retained with hashes. Earlier core checks verify frozen funding constraints; R22 recomputes 231 marginal deposit bounds; R23 jointly solves selected sets over the same transaction frames. |
| 94 entry-state connections | `reports/revision22/vault_entry_joint_records.csv`, prepared join; `reports/revision6/withdrawal_capacity.csv`, prepared historical-state table | R22 checks all 94 deposits against original vault API events. The R23 audit rebuilds four timing cells using the state's exact claim/capacity integers and timestamps, not the rounded ratios. Archived contract state/execution payloads remain included. |
| Eight cash sequences | Complete prepared market/vault event frames and daily account ledger | R22 verifies every one of the 96,013 selected-date market events against 103 original API pages and reconstructs opening-to-closing cash. This portable archive does not include/re-census every raw page of the full historical market; its complete event frame is a frozen derived input. |
| Eight gross/net cash flows | R22 prepared day summary; R21 prepared account ledger | R23 computes withdrawal less deposit from exact integers and checks against the account ledger. R22 source checks retain original vault API pages. Dates remain selected by gross withdrawals. |
| Fee-event pairs | Raw successful Blockscout responses, selected original transaction receipts and a partial SQD response | `revision22_audit_fees.py` reconstructs exact zero-address mint/accrual pairs from raw logs. Pairing is a raw-data step; residuals additionally use the prepared account ledger and observed state table. Complete daily coverage is confined to three originally nonzero residual dates. |
| Shared market cash | Prepared `reports/revision18/funded_positions.csv` and archived states | R22 recalculates each market contribution and the Spark/Moonwell-only group. It does not complete missing Gauntlet calls or execute simultaneous withdrawals. |

Source manifests identify individual files and SHA-256 hashes. Original requests,
responses, failed collection attempts, and coverage flags distinguish raw retained
records from derived inputs. Numerical reproduction of prepared inputs is not a
fresh chain-data census or external-referee replication.

## R23 outputs and checks

- `deposit_timing_classification.csv`: original 94 events, four exclusive states,
  exact before/after amounts and positive marginal lower-bound flags.
- `timing_cross_tab_and_joint_bounds.csv`: four cells, total cohort, and the
  36/43 positive-funding subgroups. Bounds optimize each selected group jointly
  over the same transaction-specific first-departure constraints.
- `joint_endpoint_witnesses.json`: all 265 transaction endpoint pairs with
  ordered allocations. Integer solutions are compared with an independent LP;
  the separate audit checks feasibility and group membership.
- `large_withdrawal_days_gross_net.csv`: original eight dates plus net cash
  withdrawal, computed before rounding. Negative means net deposit into this vault.
- All R22 raw-evidence and CSV files remain in their original directories,
  including all 319 fee-residual dates and the 170 originally nonzero dates.

Nine R23 result/manifest files are hashed for byte-for-byte reproduction.
The earlier R22/R21 output-hash checks also run. The analysis plan records the
bounded minor revision; it is not a preregistration of the original study.

## Limits that remain

Verified fees explain 0.935844% of the original gap, not most of it:
1,517,937.278538 shares remain unclassified on 167 dates. No new collection is
attempted. Original stopped providers are not retried. Daily agreement cannot
establish unobserved transaction-time withdrawal capacity. Account capacity is
not allocated to the arrival cohort, and ending source ownership is unknown.
Thirteen common-market withdrawal matches and three Gauntlet historical checks
remain unavailable. The exclusion sensitivity addresses reliance on Gauntlet.
2026 Ethereum submitted calls remain separate from the 2025 Base account.

The replay covers central retained funding, state and execution evidence plus
R21–R23 account analysis; it does not promise to rebuild every legacy appendix
extension. Code checks are author-side verification, not independent external
replication. No journal submission, public repository deposit or author identity
confirmation is implied.
