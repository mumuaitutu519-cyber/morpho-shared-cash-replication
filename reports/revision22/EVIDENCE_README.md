# R22 anonymous reviewer evidence

Run `python replay_r22.py` after installing `requirements-reproduction.txt`.
The runner disables network access, replays the retained R21 core evidence, then
recomputes R22 joint records, market cash sequences, raw fee pairs and shared cash.
Twenty-one R22 numerical/manifest files must reproduce byte for byte.

## What is included

- Frozen complete common-market and vault event frames; source hashes and monthly census manifests.
- 103 original API pages containing all 96,013 market events on the eight selected withdrawal dates. The portable independent check uses these selected pages; it does not re-download or re-census all historical raw market pages. The primary calculation uses the complete frozen event frame.
- Original 146 vault API pages and retained 704 destination transaction receipts.
- Successful and failed R22 public-log responses with request metadata and hashes.
- Exact transaction/log/share joins, funding bounds, account-wide daily views, per-event common-market cash, all 319 daily residual rows, fee pair identifiers, and market-level shared cash comparisons.
- Earlier core funding, regression, state and execution evidence from R21. The package does not claim to replay every legacy appendix extension.

## Interpretation and unresolved coverage

The funding intervals describe first deposits, not terminal source ownership.
Adjacent daily withdrawal views are not transaction-time limits or bounds on
intraday capacity. Event-time common-market cash is a separate market object.
Account capacity cannot be allocated to the identified cohort.

Only 916 exact fee-mint/AccrueInterest pairs (14,339.723868 shares, 75 dates)
are classified. Three originally nonzero residual days close completely;
1,517,937.278538 shares remain unclassified on 167 dates. Public Blockscout
retrieval stopped at HTTP 429. The SQD probe is partial. Do not retry the archived
collector as part of reproduction. Omission comparisons are bookkeeping examples,
not uncertainty intervals. Observed historical claim/capacity states are unchanged.

Thirteen treasury withdrawal transactions on November 26/28 are not matched to
the common market; no common-market origin is assigned to them. Gauntlet's three
historical checks remain incomplete: R22 reports the predeclared exclusion
sensitivity instead. Joint cash limits are accounting bounds, not jointly executed
contract withdrawals. 2026 Ethereum submitted-call evidence is separate from the
2025 Base account.

The analysis plan was frozen before this revision's calculations; it is not a
preregistration of the original study. Author details and journal submission remain
pending. No public repository deposit has been performed.

## Public API documentation

- Blockscout raw logs and the 1,000-record result cap: https://blockscout.mintlify.app/devs/apis/rpc/logs
- SQD finalized streaming and partial-response handling: https://docs.sqd.dev/en/api/evm/finalized-stream
