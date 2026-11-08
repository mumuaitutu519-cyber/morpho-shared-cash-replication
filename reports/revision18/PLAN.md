# R18: bounded liquidity benchmark and contribution revision

This plan is written before new peer-vault outcome collection. The prior R17
withdrawal result is known. The authorized task is a finite comparison table and
a revised contribution, with a new manuscript delivery if the evidence supports
an addition. It is not a promise to identify causal lending or fiat settlement.

## Selection and feasibility

- Keep the original 319 days, 2025-01-16 through 2025-11-30, unchanged.
- Select at most two alternative native-USDC MetaMorpho vaults using their
  positive supply-share positions in the same cbBTC/USDC market at the close of
  2025-01-15, before the analysis window. Rank by those shares, excluding the
  focal Spark vault; ties use address order. Query metadata for at most the
  ten largest remaining positions. No selection on later withdrawal outcomes.
- Require a vault's existence and USDC asset at that date. Preserve candidates
  with missing histories in the selection ledger; do not replace a selected
  candidate because its outcomes are inconvenient or unavailable.
- Compare a fixed weekly grid starting 2025-01-16 (every seven days), using only
  identically timed observations across vaults. Assess API schemas and archived
  coverage before choosing the exact computable liquidity object. A vault-wide
  cash quantity is not an actual holder's withdrawal, and a normalized claim
  scenario must be labelled as such. Do not invent owners or historical balances.
- At most two peers and 46 weekly dates. Use official public metadata and
  historical state, with a small fixed-date contract validation if available.
  Stop a provider on access/rate rejection; do not switch providers to bypass it.
- If a defensible cross-vault comparison is unavailable, report that limitation
  and use the existing market/holder data for an explicit ordinary-liquidity
  benchmark. Do not represent a mechanical benchmark as a peer-vault result.

## Analysis and decision

The question is whether the named holder's constraint is special relative to
ordinary loan utilization and claim size. Report levels, denominators, coverage,
utilization, position concentration and constraint duration where identified.
No new regression, p-value search, selected withdrawal threshold, or causal
cross-chain label. Existing 25% execution results remain unchanged.

Maintain the primary contribution in matched cross-chain execution and
balance-constrained first-deposit funding. A generic stock-versus-liquidity
distinction is not claimed as a new theory. Treat a null or ordinary comparison
as a substantive reason to limit the withdrawal contribution.

Deliver the selection/coverage ledger, reproducible comparison data and code,
one readable table, revised English contribution text, a concise Chinese
decision memo, and source-backed limitations. Preserve R17 deliverables and
all prior empirical results. Verify numerical provenance, the final rendered
table and revised PDF, and a clean source build before handoff.

## Schema-based measurement choice (before peer outcomes)

The two largest eligible alternative baseline positions are Moonwell Flagship
USDC and Gauntlet USDC Core. Official metadata identifies both as USDC vaults
created before the baseline. No later outcome enters selection.

The API exposes historical per-market vault supply assets and each market's
total supply and borrow assets, but no historical vault `maxWithdraw(owner)`
series. Use the ordinary direct-market cash benchmark

`K_vt = sum_j min(P_vjt, S_jt - B_jt)`

where P is the vault's supply position, S is total market supply and B is total
borrowing. This excludes management reallocations, repayments and competing
withdrawals. It is a separately evaluated capacity for each vault, not cash
that all three can withdraw simultaneously. First require nonnegative cash,
complete dates for funded positions, and reconciliation of sum(P) to vault
assets. Missing inactive-market series may be ignored only when the position
is explicitly zero, never when it is missing.

Compare K/assets and portfolio concentration. To hold claim size constant,
also report `min(1, K_vt / (s_t * A_vt))`, where s_t is the focal treasury's
observed claim/assets fraction on the same date. This is a normalized claim
benchmark for peers, not the withdrawal of a fabricated or observed peer owner.
The 25% rule remains the sole request threshold: assess K >= 0.25*s*A using
integer cross-products. Utilization is portfolio-weighted, not a treatment.

The API has calendar daily/weekly bins rather than the chosen Thursday grid.
Download daily series in three vault queries, retaining only the 46 fixed
weekly closes in the analysis; no weekly date is selected from outcomes.
Validate at the first, middle and last selected closes with historical contract
states where possible. Document any valuation/queue/timing differences before
calling a benchmark contract withdrawal capacity. No cross-vault statistical
test or causal interpretation is introduced.

## Missing-series clarification after coverage inspection

The API contains null position observations for some historical allocation
entries. Across each of the 138 selected vault-dates, the sum of the explicitly
reported nonnegative positions equals reported vault total assets exactly.
For the portfolio benchmark, the nonnegative unreported *aggregate* therefore
has zero residual under that accounting identity. Keep individual nulls as
nulls, report their counts, and do not describe them as observed zero balances.
If the identity stops reconciling, withhold that vault-date. Check the historical
withdrawal queue and total assets at the fixed first/middle/last weekly dates
for all three vaults; this limited contract check does not become a claim of
full-period contract execution for the peer owners.
