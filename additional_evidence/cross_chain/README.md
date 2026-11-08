# Cross-chain vault exposure and holder mechanism results

The universe is Morpho V1 native-USDC vaults on Ethereum, Base, Arbitrum and Polygon. Each chain has seven observations dates: 2025-10-31, 2025-11-30, 2025-12-31, 2026-01-31, 2026-02-28, 2026-03-31 and 2026-09-29. Base and Ethereum earlier month-end states are fully collected. Vault deployment dates determine entry; current assets do not determine membership at earlier dates.

## Data and definitions

`outputs/vault_state_panel.csv` contains all 2204 positive-assets vault-states. `zero_S` identifies the 63 excluded observations. The regression sample has 2141 observations from 369 entities, identified by chain plus address. Descriptives use the same S-positive sample, while separately reporting all positive-assets vaults and S-zero exclusions. Thirty-four vaults appear only once in the estimation sample; those observations are retained in b and c.

For each chain-state, V includes every discovered vault at that state, including zero-S vaults. Position sums and J are calculated before the regression filter. S_v=sum_m min(P_vm,M_m). J(V)=sum_m min(M_m,sum_v P_vm). D_v=(S_v-[J(V)-J(V-v)])/S_v. The validation script independently deletes every vault and recomputes J(V-v).

All regressors are contemporaneous. Shared-market share uses markets where another vault has a strictly positive position. Active markets counts strictly positive positions. Log assets is the natural logarithm of totalAssets in USDC. Utilization is position-weighted borrow/supply multiplied by ten. Maximum market share is max(P_vm)/sum_m P_vm. Shares and D are fractions, not percentages. There is no minimum dollar-asset threshold beyond totalAssets>0.

Base and Ethereum September 29 states preserve the existing census blocks: Base 51953448 (15:37:23 UTC) and Ethereum 26084069 (15:37:59 UTC). Arbitrum/Polygon September 29 and all six earlier month ends use the last block before the next UTC midnight. Thus September observations share a calendar date but not an identical within-day timestamp.

The complete Base September census read has 165 positive-assets vaults, including three outside the prior 162-vault selected list. These are explicit in `outputs/census_additions.csv`. King RSS USDC Vault (0xf80c0529bd94c773844e459853cd91b9263dd525) and Kingdom Elepan USDC (0x0d96ba80502eb8a08a6d3bd4680134b20c229532) have S=0 and are excluded from regressions. King Elepan USDC Vault (0x61bfd6f7df1f72427f472144d043c25d742d145e) has totalAssets=2 micro-USDC and S=1 micro-USDC and satisfies the specified inclusion rule. Ethereum retains the same 146 positive-assets vaults as its existing census.

## Inference

- a: September 29 cross-section, chain FE, chain-cluster CR1 SE, four clusters, t degrees of freedom 3. `a_HC1` is the same fitted model with HC1 heteroskedasticity-robust SE and residual degrees of freedom 329.
- b: all 28 chain-states, chain-by-state FE, vault-cluster CR1 SE, 369 clusters, t degrees of freedom 368.
- c: vault FE and chain-by-state FE, vault-cluster CR1 SE, 369 clusters, t degrees of freedom 368. The FE incidence graph has four connected components, one per chain. The full design rank is 398, including the five regressors.

Within R-squared in b and c uses y and X residualized against the complete specified FE set. Explicit-dummy OLS independently verifies both panel models' coefficients, clustered covariance and rank. No additional exposure models were fitted.

## Mechanism table

`outputs/mechanism_regressions.csv` contains the numeric a-e estimates. a-d use the existing 495-observation/93-transaction results and the constrained 17-observation subset. e uses all 495 observations, an intercept, and opening gap as the explanatory variable. Its outcome is delta capacity minus min(deposit,opening gap), computed directly from the integer source fields. Both x and y are in million USDC. Standard errors cluster by transaction, with 92 t degrees of freedom in e.

`outputs/mechanism_paper_table.csv` is the paper-facing wide table. Coefficients are followed by parenthesized t statistics, with stars from numeric p-values. It includes intercepts, p(slope=1), Obs, transaction clusters, R-squared and FE. e's slope tests zero; the slope=1 restriction applies only to the formula regressions a-d. A common intercept in the transaction-FE model b is absorbed. The table note is in `mechanism_table_notes.txt`.

## Reproduction and paths

From the root `Replication_Package` directory:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/estimate_cross_chain.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python additional_evidence/code/validate_cross_chain.py
```

Required Python packages: numpy, pandas, scipy, statsmodels and pyarrow. Online collection additionally uses requests and pycryptodome. `additional_evidence/code/collect_cross_chain.py` is the online collector. Frozen decoded states, source manifests and the necessary archived public-node responses are included. Raw amounts are integer micro-USDC; displayed dollar conversions retain the underlying raw values.

Inputs for this task are under `additional_evidence/cross_chain/raw/` (Base/Ethereum), `additional_evidence/raw/morpho_*_YYYY-MM-DD.json` (Arbitrum/Polygon), and `additional_evidence/outputs/` (the mechanism cohort and a-d estimates). Outputs are under `additional_evidence/cross_chain/outputs/`. Every state and vault has its chain, block number and hash. Public API discovery responses retain the original query, URL and retrieval time. Reads use the archived Morpho position, market, interest-rate-model and vault interfaces via PublicNode and Tenderly endpoints, with the existing integer interest/fee-share reconstruction.

The reported universe is native USDC, excluding the separate Polygon USDC.e token, Euler and Yearn. It includes empty deployed vaults for network construction and then applies the requested positive-assets/S-positive regression filter. Word and PDF manuscript files are unchanged.
