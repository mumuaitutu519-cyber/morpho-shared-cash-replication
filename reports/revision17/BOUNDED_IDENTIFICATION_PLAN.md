# R17 bounded identification extension

2026-09-06. Recorded before historical withdrawal-execution requests.

## User objective and progress audit

Continue filling the lending, withdrawal-risk and fiat-settlement gaps without
unlimited data hunting or making perfection a submission requirement. The prior
R16 turn made progress: it archived failed calls and later executions, independently
reconciled successful events, and delivered a verified offline package. It did not
identify a causal CCTP effect or fiat settlement. Those objects remain on the ledger;
they are not silently replaced by the analysis below.

## Finite new evidence gate

R6 already retains 319 closing Base vault states for January 16–November 30,
2025. They give a named holder's converted claim C and reported maxWithdraw W.
Published MetaMorpho documentation cautions that maxWithdraw can understate
actual withdrawable assets because of conversion rounding. Therefore do not
equate every C > W gap with a submitted or simulated failure.

Use read-only eth_call to attempt an asset withdrawal of floor(C/4) in each of
the same 319 historical states. The sender, owner and receiver are the registered
treasury proxy. No transaction is signed, broadcast or sent; no private key,
wallet authorization, payment or asset movement is involved. The scenario is a
one-quarter holder withdrawal, not an estimated probability or actual request.
No other depositor runs first and no allocator, supplier or borrower adjusts.

Probe the first, middle and last dates (indices 0,159,318), with three independent
calls per state: withdraw one micro-USDC; withdraw floor(C/4); withdraw C + one
USDC. Each eth_call starts afresh; do not sequence them inside one multicall.
If historical execution and response classification pass, retrieve the quarter-
withdrawal scenario for all 319 dates. Reuse probe responses. At most 325
execution requests, plus a chain identity check and a small number of official
documentation reads. Stop on access rejection; no provider switching or sample
substitution. Transport errors and unknown contract errors are not zero risk.

Classify successful execution, exact NotEnoughLiquidity, other contract error,
and provider failure separately. Decode successful shares and compare with
holder balance. Retain raw query, block identifier, response, time and SHA256.
Compare the execution result with the reported-capacity rule; report every
disagreement. Do not vary the 25% scenario after inspecting its results.

## Scope of the advance

Successful first-deposit funding, historical claim value and actual historical
execution states together can identify conditional holder withdrawal constraints.
They cannot establish the effect of CCTP adoption or delay, a realized run,
systemic failure, or forgone equilibrium lending. Historical eth_call changes
the computational request, not investors' economic behavior. Do not label it
quasi-experimental causal identification.

R16 actual Ethereum failed calls are a distinct 2026 cohort. They validate that
failed execution is an observable outcome, not the incidence of stress in the
2025 Base holder states. Never pool the two as independent treatment outcomes.

## Search stopping rules

- Lending: retain observed funding bounds and existing fixed-path diagnostic.
  Do not estimate another IV/DiD without an observed first stage and a justified
  counterfactual. Existing failed candidate shocks are not repeatedly recycled.
- Withdrawal risk: complete this single fixed historical-execution scenario if
  the public endpoint permits it; no new threshold search or broader chain census.
- Fiat redemption: public aggregate/schema checks are already completed in R16.
  No further generic web search for private customer-bank records. Reopen only
  for a concrete public transaction-to-payout crosswalk or user-provided access.

If a target remains unobserved, state that it is unresolved for that claim,
not that zero is estimated. Integration into the manuscript must preserve the
distinction between supported substantive results, conditional stress evidence,
and unestimated causal or bank-settlement objects. No new coefficient/bar plot.
