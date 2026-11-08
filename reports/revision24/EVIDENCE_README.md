# R24 reviewer evidence

Run `python replay_r24.py` after installing `requirements-reproduction.txt` in a fresh extracted directory. The runner disables networking, runs the retained central R21/R22/R23 checks, then audits the R24 funding groups, eight daily denominators, and 94 deposit-block-end calls. No keys, wallet, paid service or network retrieval is required for replay.

## New measurements

- `amount_groups_joint_bounds.csv`: original 94 deposits, grouped by zero lower bound, positive interval width and point identification. Every group uses a joint objective over the original transaction-specific feasible sets. Integer endpoint allocations and 227 transaction endpoint pairs are retained and independently checked for feasibility; LP optimality discrepancies are below one micro-USDC.
- `deposit_post_state_audit.csv`: event funding, acquired shares, direct block-end claim and capacity, independent deposit-equivalent execution and intervening-operation flags. All 94 execute. The raw calls are independently checked against the output fields, exact calldata, receipt/header hash and transaction position. The first, middle and last distinct blocks have six additional request controls.
- `intervening_usdc_transfers.csv`: raw later transfers involving the treasury, vault or Morpho. Raw complete block USDC logs are combined with prepared common-market and vault event frames for the timing audit. These are not full execution traces. Of 94 entries, 83 have no later cash/vault event in these checked records; only one is the last transaction of its block.
- `large_withdrawal_days_gross_net.csv`: the original eight gross-selected days with prior closing claim and both gross/net percentages. Ratios are checked against the account ledger before rounding.

## Raw sources and prepared inputs

The funding analysis starts from prepared transaction frames. The retained central replay validates their balances, source messages, native transfer logs and receipt matches. Historical block-end calls are new raw JSON-RPC responses in `data/raw/revision24`, with request metadata and SHA-256 hashes; no state overrides are used. The calls are simulations at recorded historical states, not submitted demands.

The intervening cash audit uses original full-block USDC logs. Its common-market and vault events are prepared historical frames. The package retains the older verification of all 96,013 events on the eight selected cash dates against 103 raw pages, but does not claim a fresh raw recensus of the entire historical frame.

Raw fee pairing remains the same partial validation: 14,339.724 verified fee shares, 1,517,937.279 unclassified shares, and three fully closed residual dates. Direct historical balances and capacities are a separate source from that incomplete event ledger. Missing Arbitrum funding balances and three Gauntlet contract checks remain missing. Shared cash is a static allocation benchmark, not simultaneous contract execution.

## Interpretation and correction

Point identification covers 53 events and 94.44% of deposit value. Fifty-two deposits are fully arrival-funded; one is precisely partially funded, not zero funded. The 35 zero-lower events are all positive-width events in this sample, totaling 3.05% of deposit value. This corrects the previous manuscript's prose; the underlying event intervals and aggregate bounds are unchanged.

All 94 deposit-equivalent calls execute at the deposit block's final state, including 68 with account coverage below 25%. The public transaction-index trace probe was unavailable and stopped; the block-end test must not be described as universal exact post-transaction replay. The archive retains that provider error separately. dRPC supplies the completed historical tests using its public read-only methods. No rejected endpoint was retried, no subscription purchased, and no transaction broadcast.

Author-side replay tests reproduction of retained inputs and raw payload decoding. It does not certify external independent replication or resolve unavailable source coverage. The PDF's separately labelled exploratory archive preserves other samples and weak/null regressions; not every legacy exploration is rerun by this central evidence package.
