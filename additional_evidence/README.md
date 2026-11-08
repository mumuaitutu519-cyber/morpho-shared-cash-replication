# Counting the same cash: additional empirical results

The package contains three requested regression exercises and four protocol-chain comparisons. Monetary regression variables in the mechanism exercise are in million USDC. Cross-protocol monetary columns are in USDC. Rates and flow shares are fractions, not percentages. No manuscript is included or edited.

## Offline reproduction

From the `Replication_Package` directory, install the packages listed in `additional_evidence/requirements.txt`, then run:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_additions.py
python additional_evidence/code/summarize_cross_protocol.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/validate.py
```

These commands use the included frozen files and require no network access. All reported coefficients and p-values are in `outputs/regressions.csv`; sample sizes, degrees of freedom, FE, cluster counts, R-squared and restriction-test p-values are in `outputs/model_metadata.csv`. Three separate regression CSVs, the 17-point scatter CSV, the cross-protocol summary, vault list, positions and contract/block/hash list are in `outputs/`.

## Definitions and inference

1. Mechanism: 495 holder-events, 93 transactions, unchanged shares and positive opening claims. Exact integer micro-USDC fields construct x=min(deposit,max(opening claim-opening capacity,0)) and y=closing capacity-opening capacity. Seventeen observations have a positive opening gap. All seventeen occur after 2025-04-23, so specifications c and d coincide. Transaction-cluster CR1 covariance; t degrees of freedom are G-1. Transaction FE absorb a common intercept, so the intercept-zero test for b is NA. Its overall and within R-squared are both reported.
2. Daily: 439 UTC dates with preceding-day regressors. Spark flow is committed ERC4626 Deposit minus Withdraw assets, divided by the same day's total assets of the ten vaults, and then lagged once. The complete 439-day log archive covers blocks 25098127–44062926; January 15 logs supply the initial lag. The gap outcomes are signed: gap25=1-4*J/assets and gap10=1-10*J/assets. Thus these two models and J/assets have identical t-tests and R-squared by construction. HAC lag 7, finite-sample correction, year-month and weekday FE, residual t degrees of freedom 414.
3. Market: positive positions in at least two or three sample vaults. Exactly 36 of 3203 and 16 of 2036 eligible market-days have zero cash, giving undefined duplication/log cash; retained N is 3167 and 2020. FE are market and UTC date. Two-way CR1 covariance and t degrees of freedom min(market clusters,date clusters)-1 match the manuscript estimator. Restricted wild bootstrap-t uses market Rademacher weights, reabsorbed FE and one-way market studentization, matching the manuscript's bootstrap implementation. Fifteen market clusters use 9999 draws, seed 20261002, with the plus-one Monte Carlo p-value. Nine market clusters use all 512 sign patterns.

## Cross-protocol state reads

Each observation uses the final block before the UTC date boundary, verifies its immediate successor, and records a finalized-head anchor. The states are 2025-10-31, 2025-11-30, 2025-12-31, 2026-01-31, 2026-02-28, 2026-03-31 and 2026-09-29. Vault count includes empty deployed vaults; `positive_asset_vaults` separately counts funded vaults. The universe changes with factory deployment dates rather than conditioning on positive assets at the September snapshot.

- Euler Earn, Ethereum: enumerate `getVaultListLength()` and `vaultList(i)` from canonical factory 0x59709B029B140C853FE28d277f83C3a65e308aF4 at each block; filter `asset()` to native USDC 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48. Read `withdrawQueue`, Earn `expectedSupplyAssets(strategy)` and underlying EVK `cash()`. Every queued underlying has a readable cash getter and the USDC asset. Reconstructed holdings/lost-assets accounting matches each vault's totalAssets exactly. The current snapshot contains 22 vaults, 11 funded.
- Morpho Vault V1, Arbitrum and Polygon: official API supplies all indexed addresses without a funded-only filter, then factory CreateMetaMorpho events and isMetaMorpho membership confirm a complete match. Arbitrum native USDC is 0xaf88d065e77c8cc2239327c5edb3a432268e5831; Polygon native USDC is 0x3c499c542cef5e3811e1192ce70d8cc03d5c3359. Read withdrawQueue, Morpho position/market/idToMarketParams, and IRM borrowRateView at the same block. Apply the manuscript's integer interest and fee-share arithmetic. Reconstructed assets match totalAssets exactly. Factory universes are 70 and 24 vaults at September 29. Polygon's four bridged-USDC.e vaults use another token, 0x2791bca1f2de4661ed88a30c99a7a9449aa84174, and are listed outside this native-USDC universe.
- Yearn V3, Polygon: enumerate NewVault(asset=USDC) events from the five documented release factories (3.0.1, 3.0.2, 3.0.3, 3.0.4, 3.1.0). StrategyChanged events and strategies(address) recover all current debt, including allocations outside the default queue. The native position measure is current_debt, consistent with totalAssets=totalIdle+totalDebt; convertToAssets(balanceOf(vault)) is also read and is at least current_debt for every positive allocation. Own totalIdle cash is counted once per vault. For the directly funded USDC-WETH shares strategy, reported totalAssets equals its actual USDC balance. For the Fluid Lender strategy, vault() identifies fToken 0x571d456b578fdc34e26e6d636736ed7c0cdb9d89; getData() identifies the common Liquidity contract, whose USDC balance supplies M. The strategy has zero idle USDC and sufficient fToken claims to back its parent allocation. External positive cash-pool counts exclude the vaults' own idle balances. Nine allocator vaults, three funded, appear in the September state.

For each combination, S sums min(position,cash) separately for every vault; J sums min(cash,total selected positions) once per cash pool. Yearn adds each vault's unique idle cash to both. Repeated cash is S-J and the rate is (S-J)/S. Yearn uses its native reported-debt position basis; unreported strategy gains are not added to the allocator's recognized assets. This valuation choice and the convertible-claim audit are explicit in the position table.

## Sources and collection scripts

Historical Base log source: https://portal.sqd.dev/datasets/base-mainnet/stream. Other chain states are public archive eth_call and eth_getLogs responses from PublicNode and Tenderly; every successful and failed request retains its URL, request, response and retrieval time under raw/rpc. Discovery uses https://api.morpho.org/graphql and the official registries/source files saved in raw/sources, with adjacent URL files.

Relevant official interfaces: https://github.com/euler-xyz/euler-earn/blob/master/src/EulerEarn.sol ; https://github.com/morpho-org/sdks/blob/main/packages/morpho-ts/src/addresses.ts ; https://github.com/yearn/yearn-vaults-v3/blob/master/contracts/VaultV3.vy ; https://github.com/Instadapp/fluid-contracts-public/blob/main/contracts/protocols/lending/interfaces/iFToken.sol .

Online entry points: discover_protocols.py, fetch_spark_lag.py, collect_euler.py, collect_morpho.py, check_morpho_factory.py, collect_yearn.py, yearn_polygon_history.py, collect_yearn_cash.py and collect_fluid_mapping.py. export_spark_flows.py freezes the committed Spark log subset from the existing replication database. chain_access.py archives calls and locates UTC-boundary blocks.

Additional Yearn discovery on Ethereum and Arbitrum returned 46 and 16 allocator vaults, with 48 and 5 positive-debt strategies. Their complete underlying-cash adapters were not constructed; those exploratory reads are retained in raw files and additional_chain_coverage.csv. The fully mapped Yearn comparison reported here is Polygon. Ethereum archive log restrictions on PublicNode were resolved using the public Tenderly endpoint. All reported 28 protocol-chain-date states have complete required reads.
