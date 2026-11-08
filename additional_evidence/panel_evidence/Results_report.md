# Panel evidence for Counting the same cash

All monetary regression variables are million USDC unless the variable is a fraction, utilization per 10 percentage points, or a logarithm. Raw event amounts and states retain integer micro-USDC. All fitted specifications and numerical inference results are reported below.

## Task 1. Cross-vault spillover

The first-difference panel contains 4380 vault-days. Net OwnFlow is zero in 480 observations; 452 contain no own Supply or Withdraw operations. Column 1c follows the specified net-zero criterion. Opening-market reconciliation includes a separately recorded own-flow adjustment on 588 days.

| spec | variable | coefficient | t_statistic | p_value | covariance |
|---|---|---|---|---|---|
| 1a | OtherVaultFlow | 0.185079027687795 | 7.62409481011323 | 1.54570028716783e-13 | cluster:date |
| 1a | OutsideFlow | 0.227719241272975 | 33.9351334804285 | 1.49570949104068e-124 | cluster:date |
| 1a | BorrowFlow | -0.39448761058721 | -3.52105197817879 | 0.0004750213325713 | cluster:date |
| 1a | OtherVaultFlow | 0.185079027687795 | 7.99874395778274 | 1.13836821881189e-14 | Driscoll-Kraay5 |
| 1a | OutsideFlow | 0.227719241272975 | 30.1687429135337 | 6.81901084778934e-109 | Driscoll-Kraay5 |
| 1a | BorrowFlow | -0.39448761058721 | -3.49208204351573 | 0.0005280616075459 | Driscoll-Kraay5 |
| 1b | OtherVaultFlow | -0.0291001386451888 | -0.375173080460312 | 0.70771376890989 | cluster:date |
| 1b | OutsideFlow | 0.226440486613275 | 41.36785867632 | 3.25871966326533e-153 | cluster:date |
| 1b | BorrowFlow | -0.386665958324842 | -3.46706433633554 | 0.0005782717314531 | cluster:date |
| 1b | Peer_x_exposure | 0.240747003900453 | 2.62529131323654 | 0.0089611173419982 | cluster:date |
| 1b | OtherVaultFlow | -0.0291001386451888 | -0.388028716243174 | 0.698183729095001 | Driscoll-Kraay5 |
| 1b | OutsideFlow | 0.226440486613275 | 36.9838302516064 | 1.13915663850932e-136 | Driscoll-Kraay5 |
| 1b | BorrowFlow | -0.386665958324842 | -3.45657108134468 | 0.0006006310989011 | Driscoll-Kraay5 |
| 1b | Peer_x_exposure | 0.240747003900453 | 2.84779733790925 | 0.0046099358141803 | Driscoll-Kraay5 |
| 1c | OtherVaultFlow | -3.78028878150997e-06 | -1.56522051905893 | 0.118395385986157 | cluster:date |
| 1c | OutsideFlow | 6.3814838153861e-06 | 0.975535438883136 | 0.329939055116616 | cluster:date |
| 1c | BorrowFlow | 1.63871840965809e-06 | 0.0824389486551641 | 0.93434273075431 | cluster:date |
| 1c | OtherVaultFlow | -3.78028878150997e-06 | -1.42048520212879 | 0.156317788155793 | Driscoll-Kraay5 |
| 1c | OutsideFlow | 6.3814838153861e-06 | 0.937170662555069 | 0.349288763960776 | Driscoll-Kraay5 |
| 1c | BorrowFlow | 1.63871840965809e-06 | 0.0851027611520649 | 0.932226227478508 | Driscoll-Kraay5 |
| 1d | OtherVaultFlow | -8.85103406283858e-05 | -0.524142054906123 | 0.600445476182254 | cluster:date |
| 1d | OutsideFlow | -0.0002002447439333 | -1.35982428387591 | 0.174586684860216 | cluster:date |
| 1d | BorrowFlow | 0.0004254503302351 | 0.793823448492912 | 0.427729050951191 | cluster:date |
| 1d | OtherVaultFlow | -8.85103406283858e-05 | -0.493304656165321 | 0.622045144604053 | Driscoll-Kraay5 |
| 1d | OutsideFlow | -0.0002002447439333 | -1.78889865568403 | 0.0743236353335357 | Driscoll-Kraay5 |
| 1d | BorrowFlow | 0.0004254503302351 | 0.769190478298948 | 0.442195772051634 | Driscoll-Kraay5 |

| spec | test | difference | t_statistic | p_value | covariance |
|---|---|---|---|---|---|
| 1a | OtherVaultFlow = OutsideFlow | -0.0426402135851802 | -1.57362786382363 | 0.116297182023557 | cluster |
| 1a | OtherVaultFlow = OutsideFlow | -0.0426402135851802 | -1.57936276617111 | 0.114976398210785 | Driscoll-Kraay5 |
| 1b | OtherVaultFlow = OutsideFlow | -0.255540625258464 | -3.19456878594981 | 0.0015017903025881 | cluster |
| 1b | OtherVaultFlow = OutsideFlow | -0.255540625258464 | -3.26069689484253 | 0.001198356287987 | Driscoll-Kraay5 |
| 1c | OtherVaultFlow = OutsideFlow | -1.01617725968961e-05 | -1.19663073892983 | 0.232225067057814 | cluster |
| 1c | OtherVaultFlow = OutsideFlow | -1.01617725968961e-05 | -1.12616035254248 | 0.26083551821031 | Driscoll-Kraay5 |
| 1d | OtherVaultFlow = OutsideFlow | 0.0001117344033049 | 0.572217899641848 | 0.567468605622202 | cluster |
| 1d | OtherVaultFlow = OutsideFlow | 0.0001117344033049 | 0.634218944547975 | 0.526269793094939 | Driscoll-Kraay5 |

In 1a, peer inflows and outside inflows are positively associated with capacity changes and borrowing is negatively associated, matching the cash-budget direction; the net-zero-own-flow and exposure-change columns have small, statistically insignificant peer-flow estimates.

## Task 2. Large borrow events

The operation ledger contains 2995 above-threshold market-transactions; the preceding-24-hour rule retains 967.

| kind | outcome | status | Obs | events | pairs | sharing_center |
|---|---|---|---|---|---|---|
| borrow | capacity_million | estimated | 15444 | 834 | 1716 | 2.05755395683453 |
| borrow | capacity_share | estimated | 15444 | 834 | 1716 | 2.05755395683453 |
| borrow | delta_D | estimated | 15300 | 820 | 1700 | 2.07560975609756 |
| borrow | delta_market_duplication | estimated | 5859 | 651 | 651 | 2.24731182795699 |
| borrow | joint_million | estimated | 7506 | 834 | 834 | 2.05755395683453 |
| placebo | capacity_million | estimated | 6201 | 513 | 689 | 1.34307992202729 |
| placebo | capacity_share | estimated | 6201 | 513 | 689 | 1.34307992202729 |
| placebo | delta_D | estimated | 6129 | 506 | 681 | 1.34782608695652 |
| placebo | delta_market_duplication | estimated | 3924 | 436 | 436 | 1.36009174311927 |
| placebo | joint_million | estimated | 4617 | 513 | 513 | 1.34307992202729 |

| model | coefficient | t_statistic | p_value |
|---|---|---|---|
| task2_borrow_capacity_million | 0.0469857629321878 | 0.169800101728051 | 0.86520857471688 |
| task2_borrow_capacity_share | -0.380535738479053 | -2.4593733375152 | 0.0141202297892188 |
| task2_borrow_delta_D | 0.0037706269327651 | 1.28573451554495 | 0.198899138586309 |
| task2_borrow_delta_market_duplication | 0.0162065941147805 | 3.61913276760342 | 0.0003185668768338 |
| task2_borrow_joint_million | -0.225050874339082 | -3.42691865949733 | 0.0006403815507171 |
| task2_placebo_capacity_million | 0.257892112838635 | 1.01134939453645 | 0.31232692942034 |
| task2_placebo_capacity_share | -1568.24627098708 | -0.943455707053733 | 0.345892830168514 |
| task2_placebo_delta_D | -0.0069048259442772 | -1.0043950962323 | 0.315669224916723 |
| task2_placebo_delta_market_duplication | -0.0043119587058765 | -1.41824509821259 | 0.156835205430688 |
| task2_placebo_joint_million | 0.148144666050351 | 1.1904745468271 | 0.234411589424697 |

Event-time coefficients above compare the event block with the −24-hour reference, with event-pair fixed effects. The following descriptive changes instead compare the event block with its immediately preceding block; available-pair counts can exceed the complete-nine-horizon estimation samples.

| event_type | outcome | count | mean | median |
|---|---|---|---|---|
| borrow | capacity_million | 1716 | -0.133879810894573 | -0.0004706028625 |
| placebo | capacity_million | 689 | -0.0005237814863222 | 7.22e-10 |
| borrow | capacity_share | 1716 | 0.0739739027785919 | -0.0002138349303707 |
| placebo | capacity_share | 689 | -0.0109347409967575 | 1.5963561049313e-09 |
| borrow | delta_D | 1713 | 0.0008888867407398 | 0 |
| placebo | delta_D | 688 | -0.0002476309923551 | 2.13681849992042e-11 |
| borrow | delta_market_duplication | 735 | 0.0156621359158647 | 0 |
| placebo | delta_market_duplication | 488 | -8.98773763221796e-06 | 0 |
| borrow | joint_million | 834 | -0.15505507323462 | -0.0015059851845 |
| placebo | joint_million | 513 | -0.0012564859674035 | 0 |

Borrow-event mean immediate changes are −0.133880 million USDC in individual capacity and −0.155055 million USDC in market joint cash, while market duplication increases by 0.015662. These average level directions agree with cash-budget tightening. Relative to −24 hours, the capacity-level coefficient is positive and insignificant; market joint cash declines and market duplication rises significantly. All signs and horizons are retained.

Capacity-share changes are raw ratios using the opening capacity denominator. Small positive denominators generate extreme ratios, including the placebo path; these values are retained without trimming. Subsequent horizons include intervening operations.

## Task 3. Next-state refused requests

| model | spec | coefficient | t_statistic | p_value | wild_cluster_p |
|---|---|---|---|---|---|
| task3_25 | LPM_lag | 0.0809433841797816 | 1.26681142486375 | 0.237022541908747 | 0.3823 |
| task3_25 | LPM_no_lag | -0.329776838235406 | -2.82179418426504 | 0.0199883706349657 | 0.0568 |
| task3_25 | FE_logit | 1.08687714530268 | 1.40843006690129 | 0.1590037613184 | 0.3285 |
| task3_10 | LPM_lag | -0.0234127528324731 | -0.671347388850014 | 0.51885705517653 | 0.5393 |
| task3_10 | LPM_no_lag | -0.101096133687307 | -2.43076840250309 | 0.0379347161021351 | 0.0722 |
| task3_10 | FE_logit | 0.504985042376995 | 0.405899085627912 | 0.684816749925443 | 0.6277 |
| task3_cross_25 | LPM_lag | -0.0880102769655242 | -1.70578265341294 | 0.0889699418429757 | NA |
| task3_cross_25 | LPM_no_lag | -0.319820937963787 | -4.21243573793668 | 3.24659778565626e-05 | NA |
| task3_cross_25 | FE_logit | -1.02048684801014 | -1.9442288409371 | 0.0518678613205234 | NA |

With the lagged refusal indicator, D is positive for the 25% request and negative for the 10% request, with both wild-bootstrap p-values above 0.10. Without that indicator, both D coefficients are negative; these dynamic estimates differ from a positive-shortage prediction.

Cross-chain regressions use committed net inflow during the UTC day through the current snapshot block. Next-state outcomes include observed zero-capacity next states; current zero-S predictors remain excluded. The cross-chain lagged-outcome LPM uses 1,799 transitions and 338 vaults; its D coefficient is −0.088010, t = −1.705783, p = 0.088970. Exact transition counts and intervals are recorded in task3_cross_status.json.

## Task 4. Robustness

| model | spec | Obs | FE | clusters | within_R2 | R2 |
|---|---|---|---|---|---|---|
| task4_duplication | asset_weighted | 436 | month + weekday | none | 0.0183140607115784 | 0.432628735272829 |
| task4_duplication | exclude_Spark | 439 | month + weekday | none | 0.121218049894151 | 0.885414754363864 |
| task4_duplication | HAC14_no_calendar_FE | 439 | none | none | NA | 0.102918249215124 |
| task4_duplication | lagged_outcome | 439 | month + weekday | none | 0.642286196307396 | 0.902177486698491 |
| task4_J_assets | asset_weighted | 436 | month + weekday | none | 0.0195296599423357 | 0.433331298124504 |
| task4_J_assets | exclude_Spark | 439 | month + weekday | none | 0.12476883057163 | 0.901984469248593 |
| task4_J_assets | HAC14_no_calendar_FE | 439 | none | none | NA | 0.538378922289427 |
| task4_J_assets | lagged_outcome | 439 | month + weekday | none | 0.569298710454473 | 0.782911835794563 |
| task4_cross_a | exclude_1 | 208 | chain | chain:3 | 0.521711841323169 | NA |
| task4_cross_a | exclude_8453 | 181 | chain | chain:3 | 0.56486640032233 | NA |
| task4_cross_a | exclude_42161 | 302 | chain | chain:3 | 0.572707732117937 | NA |
| task4_cross_a | exclude_137 | 323 | chain | chain:3 | 0.580647482241712 | NA |
| task4_cross_b | exclude_1 | 1287 | chain_state | entity:222 | 0.709386018822953 | NA |
| task4_cross_b | exclude_8453 | 1184 | chain_state | entity:204 | 0.693032667649143 | NA |
| task4_cross_b | exclude_42161 | 1905 | chain_state | entity:327 | 0.712619111280294 | NA |
| task4_cross_b | exclude_137 | 2047 | chain_state | entity:354 | 0.709611858510377 | NA |
| task4_cross_b | two_way_entity_date | 2141 | chain_state | entity:369;date:7 | 0.70613908782658 | NA |
| task4_cross_c | exclude_1 | 1287 | entity + chain_state | entity:222 | 0.366508252955553 | NA |
| task4_cross_c | exclude_8453 | 1184 | entity + chain_state | entity:204 | 0.446891706306384 | NA |
| task4_cross_c | exclude_42161 | 1905 | entity + chain_state | entity:327 | 0.406461153555829 | NA |
| task4_cross_c | exclude_137 | 2047 | entity + chain_state | entity:354 | 0.400072749674583 | NA |
| task4_cross_c | two_way_entity_date | 2141 | entity + chain_state | entity:369;date:7 | 0.406158874132526 | NA |

The asset-weighted outcome is sum(assets_v × D_v)/sum(assets_v); three dates with undefined D at positive assets are excluded from this outcome, leaving 436 days. Spark exclusion recomputes the nine-vault network and aggregate controls. HAC14 removes the calendar effects as specified. All-version network exposure requires V2 adapter positions and token-conversion states absent from the archive. The September-only cross-section contains one date cluster, so its entity/date two-way covariance is undefined.

Shared-market exposure coefficients remain positive in every leave-chain-out column; all estimates and covariance choices are retained in the complete table below.

## Task 5. Market-day heterogeneity

The median sample-vault count is 3. Low-count observations have count ≤ the median; high-count observations have count > the median.

| spec | variable | coefficient | t_statistic | p_value |
|---|---|---|---|---|
| interaction | vault_count | 0.0016568637789779 | 0.0520343382501092 | 0.959236499898596 |
| interaction | utilization10 | 0.0115036529528581 | 0.72568073956872 | 0.479990533899157 |
| interaction | log_cash | -0.0044675113746339 | -0.603680656260701 | 0.555711722000703 |
| interaction | largest_position_supply | -0.0217856244468038 | -0.255228078428874 | 0.802258272528615 |
| interaction | utilization_x_vaults | 0.0096294797321563 | 2.48266203793553 | 0.0263335194818018 |
| count_le_median | vault_count | 0.121014359918205 | 4.87434753807608 | 0.0003036634248511 |
| count_le_median | utilization10 | 0.0308998179309628 | 2.08497604448494 | 0.0573539748457764 |
| count_le_median | log_cash | -0.0077656160877575 | -0.975074512388938 | 0.347319242580988 |
| count_le_median | largest_position_supply | 0.012810617194709 | 0.128585200591023 | 0.899653879448873 |
| count_gt_median | vault_count | 0.0691163234207247 | 2.71631094251205 | 0.0299247267445759 |
| count_gt_median | utilization10 | 0.077055044341494 | 8.92510881970796 | 4.50381133423982e-05 |
| count_gt_median | log_cash | 0.030010980383273 | 3.08330511077482 | 0.017732875103966 |
| count_gt_median | largest_position_supply | -0.23586359272722 | -1.45725357779002 | 0.188396448553165 |

The positive utilization-by-vault-count interaction and larger utilization coefficient in the high-count group agree with greater duplication when more vaults draw on heavily utilized markets.

Logit wild p-values for the ten-vault panel use [restricted WCLR-C inference](https://arxiv.org/html/2406.00650v1), with 9,999 Rademacher draws and seed 20261003.

## Sample sizes and inference

| model | spec | Obs | eligible | dropped | FE | clusters | df_p | rank | within_R2 | outcome_mean | absorbed | wild_draws | pseudo_R2 | constant_outcome_vaults | converged | wild_method | constant_outcome_states | R2 | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| task1 | 1a | 4380 | 4380 | 0 | vault | date:438 | 437 | 14 | 0.296283570602169 | 0.0503780875650295 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task1 | 1b | 4380 | 4380 | 0 | vault | date:438 | 437 | 16 | 0.303859074514842 | 0.0503780875650295 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task1 | 1c | 480 | 480 | 0 | vault | date:367 | 366 | 7 | 0.0003714440942936 | -3.76495336229166e-05 | OwnFlow | 0 | NA | NA | NA | NA | NA | NA | NA |
| task1 | 1d | 4374 | 4380 | 6 | vault | date:438 | 437 | 14 | 0.0012384787812076 | 0.0003004798344113 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_capacity_million | horizons | 15444 | 15444 | 0 | pair | event_id:834 | 833 | 1724 | 0.0024733091501572 | 0.213589710134628 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_capacity_million | sharing_interaction | 15444 | 15444 | 0 | pair | event_id:834 | 833 | 1732 | 0.0035249099441189 | 0.213589710134628 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_capacity_million | borrow_size_interaction | 14589 | 15444 | 855 | pair | event_id:776 | 775 | 1637 | 0.0025605214915767 | 0.221188336604517 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_capacity_share | horizons | 15444 | 15444 | 0 | pair | event_id:834 | 833 | 1724 | 0.0007416801073506 | 1.29044920533003 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_capacity_share | sharing_interaction | 15444 | 15444 | 0 | pair | event_id:834 | 833 | 1732 | 0.0015687252429667 | 1.29044920533003 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_capacity_share | borrow_size_interaction | 14589 | 15444 | 855 | pair | event_id:776 | 775 | 1637 | 0.0007808553744595 | 1.32666030922256 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_delta_D | horizons | 15300 | 15300 | 0 | pair | event_id:820 | 819 | 1708 | 0.0005449782310804 | 0.0006569131963362 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_delta_D | sharing_interaction | 15300 | 15300 | 0 | pair | event_id:820 | 819 | 1716 | 0.0008063588980802 | 0.0006569131963362 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_delta_D | borrow_size_interaction | 14499 | 15300 | 801 | pair | event_id:768 | 767 | 1627 | 0.0036061335799627 | 0.0008334853972181 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_delta_market_duplication | horizons | 5859 | 5859 | 0 | pair | event_id:651 | 650 | 659 | 0.0077869977515113 | 0.0087710890893501 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | 5859 | 5859 | 0 | pair | event_id:651 | 650 | 667 | 0.0138857749675337 | 0.0087710890893501 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | 5859 | 5859 | 0 | pair | event_id:651 | 650 | 667 | 0.0077989774334156 | 0.0087710890893501 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_joint_million | horizons | 7506 | 7506 | 0 | pair | event_id:834 | 833 | 842 | 0.0047173944670816 | 0.0003130241102206 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_joint_million | sharing_interaction | 7506 | 7506 | 0 | pair | event_id:834 | 833 | 850 | 0.03639982194556 | 0.0003130241102206 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_borrow_joint_million | borrow_size_interaction | 6984 | 7506 | 522 | pair | event_id:776 | 775 | 792 | 0.0054187687243882 | -0.00900819147278 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_capacity_million | horizons | 6201 | 6201 | 0 | pair | event_id:513 | 512 | 697 | 0.00046758796654 | -0.0183940907842909 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_capacity_million | sharing_interaction | 6201 | 6201 | 0 | pair | event_id:513 | 512 | 705 | 0.0037126511516809 | -0.0183940907842909 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_capacity_million | borrow_size_interaction | 5832 | 6201 | 369 | pair | event_id:482 | 481 | 664 | 0.0004935803249633 | -0.0221120997681967 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_capacity_share | horizons | 6201 | 6201 | 0 | pair | event_id:513 | 512 | 697 | 0.0014633979736279 | 855.346283087064 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_capacity_share | sharing_interaction | 6201 | 6201 | 0 | pair | event_id:513 | 512 | 705 | 0.0021422394748095 | 855.346283087064 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_capacity_share | borrow_size_interaction | 5832 | 6201 | 369 | pair | event_id:482 | 481 | 664 | 0.0015627068757831 | 909.457767379018 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_delta_D | horizons | 6129 | 6129 | 0 | pair | event_id:506 | 505 | 689 | 0.0048010746601796 | 0.0072191571835191 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_delta_D | sharing_interaction | 6129 | 6129 | 0 | pair | event_id:506 | 505 | 697 | 0.0057223795656324 | 0.0072191571835191 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_delta_D | borrow_size_interaction | 5778 | 6129 | 351 | pair | event_id:477 | 476 | 658 | 0.0035017631600502 | 0.0050644170046815 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_delta_market_duplication | horizons | 3924 | 3924 | 0 | pair | event_id:436 | 435 | 444 | 0.0042480630190691 | -0.000889256213397 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | 3924 | 3924 | 0 | pair | event_id:436 | 435 | 452 | 0.0430523318695072 | -0.000889256213397 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | 3717 | 3924 | 207 | pair | event_id:413 | 412 | 429 | 0.0178285713026487 | -0.0007741183940043 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_joint_million | horizons | 4617 | 4617 | 0 | pair | event_id:513 | 512 | 521 | 0.0018898463666162 | -0.0721641418587585 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_joint_million | sharing_interaction | 4617 | 4617 | 0 | pair | event_id:513 | 512 | 529 | 0.0026280533223722 | -0.0721641418587585 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task2_placebo_joint_million | borrow_size_interaction | 4338 | 4617 | 279 | pair | event_id:482 | 481 | 498 | 0.0018583638561156 | -0.0673151627315918 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task3_25 | LPM_lag | 4377 | 4390 | 13 | vault + month | vault:10 | 9 | 30 | 0.546010720070925 | 0.129769248343614 | NA | 9999 | NA | NA | NA | NA | NA | NA | NA |
| task3_25 | LPM_no_lag | 4377 | 4390 | 13 | vault + month | vault:10 | 9 | 29 | 0.167987797381644 | 0.129769248343614 | NA | 9999 | NA | NA | NA | NA | NA | NA | NA |
| task3_25 | FE_logit | 3501 | 4390 | 889 | vault + month | vault:8 | inf | NA | NA | 0.162239360182805 | NA | 9999 | 0.650199480175786 | 0xcd347c1e7d600a9a3e403497562edd0a7bc3ef21;0xee8f4ec5672f09119b96ab6fb59c27e1b7e44b61 | True | restricted WCLR-C | NA | NA | NA |
| task3_10 | LPM_lag | 4377 | 4390 | 13 | vault + month | vault:10 | 9 | 30 | 0.17623258222962 | 0.0203335618003199 | NA | 9999 | NA | NA | NA | NA | NA | NA | NA |
| task3_10 | LPM_no_lag | 4377 | 4390 | 13 | vault + month | vault:10 | 9 | 29 | 0.0794296341635198 | 0.0203335618003199 | NA | 9999 | NA | NA | NA | NA | NA | NA | NA |
| task3_10 | FE_logit | 2187 | 4390 | 2203 | vault + month | vault:5 | inf | NA | NA | 0.040695016003658 | NA | 9999 | 0.391504121595387 | 0xbeef010f9cb27031ad51e3333f9af9c6b1228183;0xc0c5689e6f4d256e861f65465b691aeecc0deb12;0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca;0xcd347c1e7d600a9a3e403497562edd0a7bc3ef21;0xee8f4ec5672f09119b96ab6fb59c27e1b7e44b61 | True | restricted WCLR-C | NA | NA | NA |
| task3_cross_25 | LPM_lag | 1799 | 2141 | 342 | chain_state | entity:338 | 337 | 30 | 0.320123593266763 | 0.116175653140634 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task3_cross_25 | LPM_no_lag | 1799 | 2141 | 342 | chain_state | entity:338 | 337 | 29 | 0.1364211244263 | 0.116175653140634 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task3_cross_25 | FE_logit | 1799 | 2141 | 342 | chain_state | entity:338 | inf | NA | NA | 0.116175653140634 | NA | NA | 0.342130449244448 | NA | True | NA | NA | NA | NA |
| task4_duplication | asset_weighted | 436 | NA | NA | month + weekday | none | 412 | NA | 0.0183140607115784 | 0.973835926887569 | NA | NA | NA | NA | NA | NA | NA | 0.432628735272829 | weighted_duplication |
| task4_duplication | exclude_Spark | 439 | NA | NA | month + weekday | none | 415 | NA | 0.121218049894151 | 0.375067854129093 | NA | NA | NA | NA | NA | NA | NA | 0.885414754363864 | duplication |
| task4_duplication | HAC14_no_calendar_FE | 439 | NA | NA | none | none | 435 | NA | NA | 0.583691891386779 | NA | NA | NA | NA | NA | NA | NA | 0.102918249215124 | duplication |
| task4_duplication | lagged_outcome | 439 | NA | NA | month + weekday | none | 414 | NA | 0.642286196307396 | 0.583691891386779 | NA | NA | NA | NA | NA | NA | NA | 0.902177486698491 | duplication |
| task4_J_assets | asset_weighted | 436 | NA | NA | month + weekday | none | 411 | NA | 0.0195296599423357 | 0.973835926887569 | NA | NA | NA | NA | NA | NA | NA | 0.433331298124504 | weighted_duplication |
| task4_J_assets | exclude_Spark | 439 | NA | NA | month + weekday | none | 414 | NA | 0.12476883057163 | 0.457803411809332 | NA | NA | NA | NA | NA | NA | NA | 0.901984469248593 | J_assets |
| task4_J_assets | HAC14_no_calendar_FE | 439 | NA | NA | none | none | 434 | NA | NA | 0.154335265304471 | NA | NA | NA | NA | NA | NA | NA | 0.538378922289427 | J_assets |
| task4_J_assets | lagged_outcome | 439 | NA | NA | month + weekday | none | 413 | NA | 0.569298710454473 | 0.154335265304471 | NA | NA | NA | NA | NA | NA | NA | 0.782911835794563 | J_assets |
| task4_cross_a | exclude_1 | 208 | 208 | 0 | chain | chain:3 | 2 | 8 | 0.521711841323169 | 0.566387064287069 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_a | exclude_8453 | 181 | 181 | 0 | chain | chain:3 | 2 | 8 | 0.56486640032233 | 0.497778039234577 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_a | exclude_42161 | 302 | 302 | 0 | chain | chain:3 | 2 | 8 | 0.572707732117937 | 0.555571866510153 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_a | exclude_137 | 323 | 323 | 0 | chain | chain:3 | 2 | 8 | 0.580647482241712 | 0.580677205662752 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_b | exclude_1 | 1287 | 1287 | 0 | chain_state | entity:222 | 221 | 26 | 0.709386018822953 | 0.724292969437873 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_b | exclude_8453 | 1184 | 1184 | 0 | chain_state | entity:204 | 203 | 26 | 0.693032667649143 | 0.674322839018051 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_b | exclude_42161 | 1905 | 1905 | 0 | chain_state | entity:327 | 326 | 26 | 0.712619111280294 | 0.689163102416418 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_b | exclude_137 | 2047 | 2047 | 0 | chain_state | entity:354 | 353 | 26 | 0.709611858510377 | 0.714309976880116 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_b | two_way_entity_date | 2141 | 2141 | 0 | chain_state | entity:369;date:7 | 6 | 33 | 0.70613908782658 | 0.701480854093226 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_c | exclude_1 | 1287 | 1287 | 0 | entity + chain_state | entity:222 | 221 | 245 | 0.366508252955553 | 0.724292969437873 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_c | exclude_8453 | 1184 | 1184 | 0 | entity + chain_state | entity:204 | 203 | 227 | 0.446891706306384 | 0.674322839018051 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_c | exclude_42161 | 1905 | 1905 | 0 | entity + chain_state | entity:327 | 326 | 350 | 0.406461153555829 | 0.689163102416418 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_c | exclude_137 | 2047 | 2047 | 0 | entity + chain_state | entity:354 | 353 | 377 | 0.400072749674583 | 0.714309976880116 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task4_cross_c | two_way_entity_date | 2141 | 2141 | 0 | entity + chain_state | entity:369;date:7 | 6 | 398 | 0.406158874132526 | 0.701480854093226 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task5 | interaction | 3167 | 3167 | 0 | market + date | market:15;date:439 | 14 | 458 | 0.197278402962011 | 0.381983821773614 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task5 | count_le_median | 1725 | 1725 | 0 | market + date | market:14;date:437 | 13 | 454 | 0.100396264962077 | 0.242702599170709 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |
| task5 | count_gt_median | 1442 | 1442 | 0 | market + date | market:8;date:439 | 7 | 450 | 0.278196369102733 | 0.548599708729239 | NA | 0 | NA | NA | NA | NA | NA | NA | NA |

## Complete numerical estimates

| model | spec | variable | coefficient | standard_error | t_statistic | p_value | covariance | wild_cluster_p |
|---|---|---|---|---|---|---|---|---|
| task1 | 1a | OwnFlow | 0.636741947342866 | 0.136456552874555 | 4.66626141383056 | 4.08464212927442e-06 | cluster:date | NA |
| task1 | 1a | OtherVaultFlow | 0.185079027687795 | 0.0242755412015983 | 7.62409481011323 | 1.54570028716783e-13 | cluster:date | NA |
| task1 | 1a | OutsideFlow | 0.227719241272975 | 0.0067104271566902 | 33.9351334804285 | 1.49570949104068e-124 | cluster:date | NA |
| task1 | 1a | BorrowFlow | -0.39448761058721 | 0.112036860867715 | -3.52105197817879 | 0.0004750213325713 | cluster:date | NA |
| task1 | 1a | OwnFlow | 0.636741947342866 | 0.134612417357922 | 4.73018730248213 | 3.03254488495952e-06 | Driscoll-Kraay5 | NA |
| task1 | 1a | OtherVaultFlow | 0.185079027687795 | 0.0231385113293587 | 7.99874395778274 | 1.13836821881189e-14 | Driscoll-Kraay5 | NA |
| task1 | 1a | OutsideFlow | 0.227719241272975 | 0.0075481846202753 | 30.1687429135337 | 6.81901084778934e-109 | Driscoll-Kraay5 | NA |
| task1 | 1a | BorrowFlow | -0.39448761058721 | 0.112966306539021 | -3.49208204351573 | 0.0005280616075459 | Driscoll-Kraay5 | NA |
| task1 | 1b | OwnFlow | 0.645295202847696 | 0.135888138234097 | 4.74872355478174 | 2.7798961856894e-06 | cluster:date | NA |
| task1 | 1b | OtherVaultFlow | -0.0291001386451888 | 0.0775645699565781 | -0.375173080460312 | 0.70771376890989 | cluster:date | NA |
| task1 | 1b | OutsideFlow | 0.226440486613275 | 0.0054738266339827 | 41.36785867632 | 3.25871966326533e-153 | cluster:date | NA |
| task1 | 1b | BorrowFlow | -0.386665958324842 | 0.111525463854969 | -3.46706433633554 | 0.0005782717314531 | cluster:date | NA |
| task1 | 1b | Peer_x_exposure | 0.240747003900453 | 0.0917029674713139 | 2.62529131323654 | 0.0089611173419982 | cluster:date | NA |
| task1 | 1b | ExposureShare | -0.0914338533585441 | 0.599718491074 | -0.152461287619798 | 0.878893487554337 | cluster:date | NA |
| task1 | 1b | OwnFlow | 0.645295202847696 | 0.134555985728608 | 4.79573762068989 | 2.22669588495679e-06 | Driscoll-Kraay5 | NA |
| task1 | 1b | OtherVaultFlow | -0.0291001386451888 | 0.0749948068971061 | -0.388028716243174 | 0.698183729095001 | Driscoll-Kraay5 | NA |
| task1 | 1b | OutsideFlow | 0.226440486613275 | 0.006122688890598 | 36.9838302516064 | 1.13915663850932e-136 | Driscoll-Kraay5 | NA |
| task1 | 1b | BorrowFlow | -0.386665958324842 | 0.111864026292328 | -3.45657108134468 | 0.0006006310989011 | Driscoll-Kraay5 | NA |
| task1 | 1b | Peer_x_exposure | 0.240747003900453 | 0.0845379692914528 | 2.84779733790925 | 0.0046099358141803 | Driscoll-Kraay5 | NA |
| task1 | 1b | ExposureShare | -0.0914338533585441 | 0.550187299163146 | -0.16618677584455 | 0.868086826476603 | Driscoll-Kraay5 | NA |
| task1 | 1c | OtherVaultFlow | -3.78028878150997e-06 | 2.41517967307433e-06 | -1.56522051905893 | 0.118395385986157 | cluster:date | NA |
| task1 | 1c | OutsideFlow | 6.3814838153861e-06 | 6.54151921194384e-06 | 0.975535438883136 | 0.329939055116616 | cluster:date | NA |
| task1 | 1c | BorrowFlow | 1.63871840965809e-06 | 1.98779634673984e-05 | 0.0824389486551641 | 0.93434273075431 | cluster:date | NA |
| task1 | 1c | OtherVaultFlow | -3.78028878150997e-06 | 2.66126586594826e-06 | -1.42048520212879 | 0.156317788155793 | Driscoll-Kraay5 | NA |
| task1 | 1c | OutsideFlow | 6.3814838153861e-06 | 6.80930813389724e-06 | 0.937170662555069 | 0.349288763960776 | Driscoll-Kraay5 | NA |
| task1 | 1c | BorrowFlow | 1.63871840965809e-06 | 1.92557607705579e-05 | 0.0851027611520649 | 0.932226227478508 | Driscoll-Kraay5 | NA |
| task1 | 1d | OwnFlow | -6.39981658616365e-06 | 0.0001485789440507 | -0.0430735096890867 | 0.965662609610984 | cluster:date | NA |
| task1 | 1d | OtherVaultFlow | -8.85103406283858e-05 | 0.0001688670844094 | -0.524142054906123 | 0.600445476182254 | cluster:date | NA |
| task1 | 1d | OutsideFlow | -0.0002002447439333 | 0.0001472578084593 | -1.35982428387591 | 0.174586684860216 | cluster:date | NA |
| task1 | 1d | BorrowFlow | 0.0004254503302351 | 0.0005359508226204 | 0.793823448492912 | 0.427729050951191 | cluster:date | NA |
| task1 | 1d | OwnFlow | -6.39981658616365e-06 | 0.0001626212727336 | -0.0393541169527521 | 0.968626033057429 | Driscoll-Kraay5 | NA |
| task1 | 1d | OtherVaultFlow | -8.85103406283858e-05 | 0.0001794232823918 | -0.493304656165321 | 0.622045144604053 | Driscoll-Kraay5 | NA |
| task1 | 1d | OutsideFlow | -0.0002002447439333 | 0.0001119374444701 | -1.78889865568403 | 0.0743236353335357 | Driscoll-Kraay5 | NA |
| task1 | 1d | BorrowFlow | 0.0004254503302351 | 0.0005531144004487 | 0.769190478298948 | 0.442195772051634 | Driscoll-Kraay5 | NA |
| task2_borrow_capacity_million | horizons | h_m1 | 0.170857632123596 | 0.280015412515432 | 0.610172242266056 | 0.541914134539366 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_pre | 0.180865573826775 | 0.272715862191792 | 0.663201518141172 | 0.5073849795904 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_event | 0.0469857629321878 | 0.276712218979936 | 0.169800101728051 | 0.86520857471688 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_p1 | 0.241886113104665 | 0.292223567296086 | 0.82774334507929 | 0.408052936998778 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_p6 | 0.332344732342774 | 0.342481633332892 | 0.970401621565894 | 0.332128018970455 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_p24 | 0.622678170564901 | 0.431796261787335 | 1.44206475523306 | 0.149659961927836 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_p72 | 0.933183444331063 | 0.492177101489845 | 1.89603181762473 | 0.0583016659885322 | cluster:event_id | NA |
| task2_borrow_capacity_million | horizons | h_p168 | 1.02129612642656 | 0.583996765099741 | 1.74880442403157 | 0.0806931539021528 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_m1 | 0.0298812329595337 | 0.146556173670862 | 0.20388928157091 | 0.838489820606247 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_pre | 0.0136890052548155 | 0.14458817245211 | 0.0946758301364485 | 0.92459508514755 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_event | 0.0214190097192501 | 0.145802537984961 | 0.146904230991228 | 0.88324315821991 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_p1 | 0.0501705134126404 | 0.142476838913417 | 0.352131011575355 | 0.724829077011252 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_p6 | -0.0032427572236568 | 0.13369267095609 | -0.0242553103357621 | 0.98065476885734 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_p24 | 0.321760430844652 | 0.273883547380454 | 1.17480744616504 | 0.240407474420901 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_p72 | 0.458958346182154 | 0.304351181639027 | 1.50798936843458 | 0.131936401418655 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | h_p168 | 0.887849315381315 | 0.409599861458674 | 2.16760160079032 | 0.0304716321658856 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_m1 | 0.124619224681314 | 0.142596431000963 | 0.873929479206059 | 0.3824085342177 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_pre | 0.147779447367458 | 0.146877910736509 | 1.0061380001011 | 0.314641361833224 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_event | 0.0226003003474842 | 0.157291058922723 | 0.143684583868099 | 0.885784296439785 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_p1 | 0.169471269904763 | 0.16501344166346 | 1.02701494009436 | 0.304711556699979 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_p6 | 0.296650028022408 | 0.232983837596322 | 1.27326440787878 | 0.203279434585654 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_p24 | 0.266002931264765 | 0.293045724300134 | 0.907718179134147 | 0.364289654772762 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_p72 | 0.419201826732454 | 0.298481074912371 | 1.40445027161446 | 0.160557559277246 | cluster:event_id | NA |
| task2_borrow_capacity_million | sharing_interaction | count_p168 | 0.117963277734865 | 0.328046359317693 | 0.359593314738252 | 0.719242423413726 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_m1 | 0.197709683121786 | 0.296266743122245 | 0.667336742012272 | 0.504755711213737 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_pre | 0.192661977020226 | 0.288895957891273 | 0.666890524971398 | 0.505040557036255 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_event | 0.0453081365036637 | 0.293178856609033 | 0.154540941416127 | 0.877223468355424 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_p1 | 0.249888099104432 | 0.309728330381585 | 0.806797682332032 | 0.420030571575996 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_p6 | 0.341291366295995 | 0.363023641065905 | 0.940135373260815 | 0.347441050706321 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_p24 | 0.649659506517439 | 0.457800197927623 | 1.41908961476716 | 0.156274940212712 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_p72 | 0.97501741359557 | 0.52171641064978 | 1.86886475811872 | 0.062018641901089 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | h_p168 | 1.07374949449618 | 0.619207013768544 | 1.73407191879378 | 0.0833029755076257 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_m1 | -6.92013378504939e-09 | 4.91312126656019e-08 | -0.140850050499453 | 0.888025003139733 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_pre | -6.66757595003835e-09 | 4.96164249727697e-08 | -0.134382433915737 | 0.893135061364473 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_event | 1.66158863777921e-08 | 4.9379233401376e-08 | 0.336495430026848 | 0.736588388717174 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_p1 | -1.55296398843913e-08 | 5.31011363646228e-08 | -0.292454002825022 | 0.7700177999572 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_p6 | -2.16224787427464e-08 | 6.23454712438441e-08 | -0.346817151452382 | 0.728822838790054 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_p24 | -2.7651408324099e-08 | 8.25324332965657e-08 | -0.335036872410372 | 0.73768793312307 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_p72 | -5.32470908917907e-08 | 1.02670268112062e-07 | -0.518622302940445 | 0.604172195551581 | cluster:event_id | NA |
| task2_borrow_capacity_million | borrow_size_interaction | size_p168 | -2.35242395024423e-09 | 1.23905947113561e-07 | -0.0189855612667907 | 0.984857510409651 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_m1 | -0.361767406805667 | 0.195863742000814 | -1.84703612373628 | 0.0650963753148124 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_pre | -0.45450964125768 | 0.245696341124933 | -1.84988363756939 | 0.0646843204796652 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_event | -0.380535738479053 | 0.154728740315419 | -2.4593733375152 | 0.0141202297892188 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_p1 | -0.205142070504308 | 0.0956236102486688 | -2.14530773279566 | 0.0322167629236612 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_p6 | -0.0528076983980782 | 0.168509097809315 | -0.313381883142211 | 0.754068997515957 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_p24 | 2.35962447052303 | 2.45940148620514 | 0.959430367005241 | 0.337620372240923 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_p72 | 2.17015132130189 | 2.20090988585809 | 0.986024614295277 | 0.324407342857177 | cluster:event_id | NA |
| task2_borrow_capacity_share | horizons | h_p168 | 4.44844284027125 | 4.47573772280106 | 0.993901590258347 | 0.32055939801448 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_m1 | -0.332383634180704 | 0.155483183122514 | -2.13774652348608 | 0.0328278125808384 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_pre | -0.400329442822641 | 0.159142666315527 | -2.51553811489448 | 0.0120721804739156 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_event | -0.422546377370414 | 0.159009869211985 | -2.65735944230666 | 0.0080263772288981 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_p1 | -0.236219751908231 | 0.128261424524532 | -1.84170535126912 | 0.0658736057255384 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_p6 | 0.0790490564141293 | 0.243724971557759 | 0.324337124377902 | 0.745764241103117 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_p24 | 4.26357595493127 | 4.25829658089328 | 1.00123978542539 | 0.317001649828822 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_p72 | 3.74350918716815 | 3.81489810850624 | 0.981286807849755 | 0.326736237583771 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | h_p168 | 7.45642931858576 | 7.75561645127366 | 0.961423165448213 | 0.336618429920879 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_m1 | -0.025974439583127 | 0.156232658782412 | -0.166254864927454 | 0.867996728497372 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_pre | -0.0478937918835181 | 0.198924056631143 | -0.240764202654109 | 0.809797119602136 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_event | 0.0371362389595159 | 0.119569450399884 | 0.310583002893455 | 0.756195344676571 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_p1 | 0.0274718079367626 | 0.0694943694880699 | 0.395309837892388 | 0.692715450045526 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_p6 | -0.116557712149866 | 0.119529517338795 | -0.975137478548458 | 0.329775158651946 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_p24 | -1.6830402764201 | 1.59886491335313 | -1.05264695119892 | 0.292808078966862 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_p72 | -1.39080469180035 | 1.42995934079119 | -0.972618348036962 | 0.331025359257878 | cluster:event_id | NA |
| task2_borrow_capacity_share | sharing_interaction | count_p168 | -2.65897657339932 | 2.90882529816624 | -0.914106658476732 | 0.360925312515142 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_m1 | -0.259106832754255 | 0.190410957899928 | -1.36077689861962 | 0.173979785749272 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_pre | -0.351438906457033 | 0.245619904117038 | -1.43082421483876 | 0.152883678618705 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_event | -0.274882286862403 | 0.138788015713615 | -1.98059094258985 | 0.0479903546418226 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_p1 | -0.117449564635549 | 0.0747794743350774 | -1.57061233286119 | 0.11668088137605 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_p6 | 0.0415340362184193 | 0.165237326357672 | 0.251359890249706 | 0.801602508181627 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_p24 | 2.55287677424086 | 2.60907997148724 | 0.978458614584227 | 0.328152877590521 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_p72 | 2.38577162181003 | 2.33328345307353 | 1.02249541034861 | 0.306865541797908 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | h_p168 | 4.82019922840156 | 4.74757901090429 | 1.01529626307018 | 0.310281480748345 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_m1 | 3.61685614268087e-08 | 3.43599429434437e-08 | 1.05263741230135 | 0.29283528645932 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_pre | 3.41986880219336e-08 | 5.35594217278686e-08 | 0.638518619482012 | 0.523324776785119 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_event | 2.07804834915797e-08 | 4.52976628289096e-08 | 0.458753988479894 | 0.64653946393248 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_p1 | -2.63414059474144e-09 | 4.20563318220645e-08 | -0.0626336268670836 | 0.950074401295563 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_p6 | -2.44278739754104e-08 | 5.1323673146643e-08 | -0.475957243076009 | 0.63423897675708 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_p24 | -4.09792081084462e-07 | 4.27347802667911e-07 | -0.958919359187411 | 0.337898422717122 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_p72 | -4.14157474200435e-07 | 3.95666861828061e-07 | -1.04673277991223 | 0.295549181563083 | cluster:event_id | NA |
| task2_borrow_capacity_share | borrow_size_interaction | size_p168 | -7.91660668325807e-07 | 7.77817273342733e-07 | -1.01779774692272 | 0.309091705784756 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_m1 | 0.0018220237807978 | 0.0029482650002511 | 0.617998646879635 | 0.53674803791164 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_pre | 0.0028610225824054 | 0.0029144738478559 | 0.981660063448557 | 0.326557238583637 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_event | 0.0037706269327651 | 0.0029326636931474 | 1.28573451554495 | 0.198899138586309 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_p1 | 0.0053205028955708 | 0.002935574981739 | 1.81242275488362 | 0.0702869577862716 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_p6 | 0.0046611292731264 | 0.002857858948812 | 1.63098646805647 | 0.103277631760038 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_p24 | 0.0050016302288251 | 0.0031046511350005 | 1.61101199823671 | 0.107562404885612 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_p72 | 0.0049626791020187 | 0.0034674813860988 | 1.43120569353715 | 0.152752730920808 | cluster:event_id | NA |
| task2_borrow_delta_D | horizons | h_p168 | 0.0032618072131671 | 0.0036199024561657 | 0.901075996567626 | 0.367812805823379 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_m1 | 0.0012007196443658 | 0.0041707918978747 | 0.287887689859959 | 0.77350554383324 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_pre | 0.0040003325572004 | 0.0038575832309098 | 1.03700485971288 | 0.300039663975993 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_event | 0.0048920728273864 | 0.0039050854445233 | 1.25274411965743 | 0.210656412310492 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_p1 | 0.0067127148152008 | 0.0040207153647595 | 1.66953246032683 | 0.0953940450052127 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_p6 | 0.0057063531643485 | 0.0042154895277445 | 1.35366322862191 | 0.176217289251906 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_p24 | 0.00519407818134 | 0.004567188976267 | 1.13725930946377 | 0.255762510854898 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_p72 | 0.004553429654509 | 0.0050209897562395 | 0.906878897502352 | 0.364737579342719 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | h_p168 | 0.0032936269348474 | 0.0050788429649091 | 0.64849946289024 | 0.516843738045762 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_m1 | 0.0005496940633322 | 0.0016176305607826 | 0.339814341209187 | 0.734083473596882 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_pre | -0.0010079957507389 | 0.0016973657177095 | -0.593858907495299 | 0.552770468728283 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_event | -0.0009921906429944 | 0.0017015114356307 | -0.583123111733094 | 0.559970952390792 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_p1 | -0.0012317488042422 | 0.0016074509412674 | -0.76627458581785 | 0.443733734339245 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_p6 | -0.0009247538108425 | 0.0017082150323591 | -0.541356792514254 | 0.588408905812276 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_p24 | -0.0001702668480615 | 0.0019079654673574 | -0.0892400051125542 | 0.928912990189419 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_p72 | 0.0003620803058063 | 0.002213780146043 | 0.163557481737063 | 0.870119869596568 | cluster:event_id | NA |
| task2_borrow_delta_D | sharing_interaction | count_p168 | -2.81522543934787e-05 | 0.0022619014804547 | -0.0124462778935085 | 0.990072594535392 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_m1 | 0.0034058613280243 | 0.002794435155021 | 1.21880134591948 | 0.223294321399204 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_pre | 0.0034368287837613 | 0.0029704489931787 | 1.15700649688095 | 0.247629910679245 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_event | 0.0045448269257589 | 0.0029803681936138 | 1.52492129512633 | 0.127690939433416 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_p1 | 0.0065332384066847 | 0.0027720275472707 | 2.35684469049277 | 0.0186814124739216 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_p6 | 0.0045485978220467 | 0.002935727624671 | 1.54939367801751 | 0.121699609125748 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_p24 | 0.0059858648465943 | 0.0031976505713706 | 1.87195714884776 | 0.0615928840980132 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_p72 | 0.0065606986284747 | 0.0034833473763132 | 1.88344655864285 | 0.0600179924997805 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | h_p168 | 0.0044114651838971 | 0.0036200051954393 | 1.21863504214163 | 0.223357427194527 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_m1 | 4.44862276618527e-09 | 5.0271878938637e-10 | 8.84912770341319 | 6.02010487744325e-18 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_pre | 4.45129806251437e-09 | 1.12636233569516e-09 | 3.95192374731452 | 8.46826830096149e-05 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_event | 6.35607184192767e-10 | 5.73856913679292e-09 | 0.110760569236251 | 0.911835189522959 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_p1 | 5.78101340692416e-10 | 5.51054334905729e-09 | 0.104908228476474 | 0.916476057143997 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_p6 | 8.92260127029538e-10 | 5.45774039867668e-09 | 0.163485263470187 | 0.870179441885793 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_p24 | 2.09488998209665e-09 | 5.58739026341593e-09 | 0.374931745114205 | 0.707814875912556 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_p72 | -3.53571245989468e-08 | 3.86317152661283e-08 | -0.915235690555716 | 0.360355555125874 | cluster:event_id | NA |
| task2_borrow_delta_D | borrow_size_interaction | size_p168 | -2.72797952506956e-08 | 4.25822833873114e-08 | -0.64063721061103 | 0.521949765015303 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_m1 | -0.0020045356266169 | 0.003731201202112 | -0.537236004716721 | 0.591288459458038 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_pre | -0.0009307346997852 | 0.0040291471954607 | -0.231000421338258 | 0.81738716601998 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_event | 0.0162065941147805 | 0.0044780324888474 | 3.61913276760342 | 0.0003185668768338 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_p1 | 0.0139749540689217 | 0.0046510376009057 | 3.00469599863052 | 0.0027607764855 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_p6 | 0.0117983209507698 | 0.0048614017418047 | 2.426938067947 | 0.0154976249839398 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_p24 | 0.0126520238014266 | 0.005241500492733 | 2.41381715387944 | 0.0160617872480821 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_p72 | 0.0116219483994077 | 0.0062867192389197 | 1.84865077598162 | 0.0649622057829845 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | horizons | h_p168 | 0.0072446184971795 | 0.0060699623966934 | 1.19351950205259 | 0.233101403463093 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_m1 | -0.0020045356266168 | 0.0037280063128205 | -0.537696414226377 | 0.590970693439468 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_pre | -0.0009307346997852 | 0.0040198810857485 | -0.231532893618407 | 0.816973701094328 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_event | 0.0162065941147805 | 0.0043868067752579 | 3.69439433853967 | 0.0002389627764101 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_p1 | 0.0139749540689217 | 0.0046240860845323 | 3.02220888916149 | 0.0026080487606594 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_p6 | 0.0117983209507698 | 0.0048427451766071 | 2.43628779142901 | 0.0151063499658373 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_p24 | 0.0126520238014267 | 0.0052229157376795 | 2.42240626440736 | 0.0156904720997179 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_p72 | 0.0116219483994077 | 0.0062755737986948 | 1.85193398599261 | 0.0644885519637294 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | h_p168 | 0.0072446184971795 | 0.0060712189124211 | 1.19327248805964 | 0.233198030314997 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_m1 | 0.0031448302996374 | 0.0023219070487527 | 1.35441696571219 | 0.17607401111667 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_pre | 0.0046639607592035 | 0.0025956644725144 | 1.7968272897327 | 0.0728271802564818 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_event | 0.0135415253306397 | 0.0028644269156567 | 4.72748152749953 | 2.78885785195767e-06 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_p1 | 0.0078661575478749 | 0.0028831694864181 | 2.728302163619 | 0.0065381856464056 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_p6 | 0.0068916329722042 | 0.0031372591922322 | 2.19670500584321 | 0.028393830779278 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_p24 | 0.0071917063872269 | 0.0035295855448322 | 2.0375498187759 | 0.0419994435737589 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_p72 | 0.0066241889800631 | 0.0041798611928154 | 1.58478683250276 | 0.113501141343519 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | sharing_interaction | count_p168 | 0.0030111804123549 | 0.0043517993774911 | 0.691939161517798 | 0.489222621254649 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_m1 | -0.0020076196609699 | 0.0037398184488463 | -0.536822759829206 | 0.59157374035466 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_pre | -0.0009321664266009 | 0.004038453798324 | -0.23082260517325 | 0.81752525168903 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_event | 0.016231528562029 | 0.0044882977602719 | 3.61641081518744 | 0.0003218666130081 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_p1 | 0.0139964551327914 | 0.0046617247341713 | 3.00241990484654 | 0.0027812163064288 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_p6 | 0.0118164731213369 | 0.0048725927333729 | 2.42508942731954 | 0.0155760384206687 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_p24 | 0.0126714901726778 | 0.0052535670357795 | 2.41197839227676 | 0.0161422774677224 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_p72 | 0.0116398305024432 | 0.006301212219441 | 1.84723670574543 | 0.0651670916952279 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | h_p168 | 0.0072557648949291 | 0.0060839718981175 | 1.19260328884394 | 0.233459950477004 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_m1 | 4.99668779495198e-10 | 9.3082732175486e-10 | 0.536800723203084 | 0.591588954974747 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_pre | 2.31965376737965e-10 | 1.00515338118971e-09 | 0.230776099527624 | 0.817561367245345 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_event | -4.03982686250702e-09 | 1.117098011688e-09 | -3.61635847547757 | 0.0003219303758645 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_p1 | -3.48355728633303e-09 | 1.16025893252863e-09 | -3.00239643813048 | 0.0027814277623218 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_p6 | -2.94097661515854e-09 | 1.21275799766424e-09 | -2.42503172176381 | 0.0155784917277914 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_p24 | -3.15390065446871e-09 | 1.30759936582575e-09 | -2.41197780979116 | 0.0161423030217321 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_p72 | -2.89722083993754e-09 | 1.56835336928202e-09 | -1.84730105898511 | 0.0651577559077971 | cluster:event_id | NA |
| task2_borrow_delta_market_duplication | borrow_size_interaction | size_p168 | -1.80591599245204e-09 | 1.51429086022783e-09 | -1.19258198004334 | 0.233468294034036 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_m1 | -0.0448682257828832 | 0.0271118254157406 | -1.65493193818051 | 0.0983149915683505 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_pre | -0.0699958011044621 | 0.0299228393003575 | -2.33920987249448 | 0.0195600623476115 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_event | -0.225050874339082 | 0.0656714957956118 | -3.42691865949733 | 0.0006403815507171 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_p1 | -0.0903065754111777 | 0.0414969572703516 | -2.17622161602916 | 0.0298190142988587 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_p6 | -0.0990241024931312 | 0.0436802406985844 | -2.26702282106107 | 0.02364439229525 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_p24 | -0.0658894037394067 | 0.0714746485449576 | -0.921856981191901 | 0.356870093366008 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_p72 | -0.0421877341754568 | 0.0667336102870475 | -0.632181205152707 | 0.527441945997988 | cluster:event_id | NA |
| task2_borrow_joint_million | horizons | h_p168 | 0.010177724097447 | 0.0772854453556396 | 0.131690049149783 | 0.895261256310402 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_m1 | -0.0448682257828835 | 0.026858959756841 | -1.67051241705128 | 0.0951936754913097 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_pre | -0.069995801104462 | 0.0295544054848319 | -2.36837114319169 | 0.0180939684795268 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_event | -0.225050874339082 | 0.0617001794855701 | -3.64749140465167 | 0.0002812730122796 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_p1 | -0.0903065754111775 | 0.0410408312350665 | -2.20040804958202 | 0.0280517706469144 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_p6 | -0.0990241024931317 | 0.0429635108054596 | -2.30484196092625 | 0.0214204882619059 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_p24 | -0.065889403739407 | 0.0712559832250837 | -0.924685910673287 | 0.355397097558866 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_p72 | -0.0421877341754571 | 0.066590770632869 | -0.633537257108019 | 0.526556763671144 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | h_p168 | 0.0101777240974471 | 0.0773241226447116 | 0.131624178190959 | 0.895313344022788 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_m1 | -0.0679114126035492 | 0.0328295400657073 | -2.06860688476374 | 0.038891034475338 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_pre | -0.085420720785672 | 0.0403896848390812 | -2.11491426897738 | 0.0347336560292482 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_event | -0.402731034058376 | 0.126391089898607 | -3.1863878567821 | 0.00149429197799 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_p1 | -0.112276172870179 | 0.0708372693732414 | -1.58498730772068 | 0.113348750328937 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_p6 | -0.142961191711277 | 0.0740393264443973 | -1.93088185126372 | 0.0538367215593505 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_p24 | -0.108879274478213 | 0.145198455285639 | -0.74986523970949 | 0.453547598699511 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_p72 | -0.087995884288309 | 0.12813186003669 | -0.686760375312681 | 0.492424873680159 | cluster:event_id | NA |
| task2_borrow_joint_million | sharing_interaction | count_p168 | -0.0195098266512196 | 0.151605205208023 | -0.128688369402947 | 0.897635301908054 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_m1 | -0.0466922397492164 | 0.0291237289953392 | -1.60323699470933 | 0.109289784308447 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_pre | -0.0667001011643604 | 0.032187814782561 | -2.07221588712812 | 0.0385754729914213 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_event | -0.250971834353471 | 0.0702929653465699 | -3.57036914172121 | 0.0003784516316198 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_p1 | -0.0970948848191361 | 0.0446939866147861 | -2.17243732710597 | 0.0301251044410101 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_p6 | -0.109416092010504 | 0.0469731875714308 | -2.32933078778436 | 0.0200976553684565 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_p24 | -0.0720074120691613 | 0.07698788114872 | -0.935308401721852 | 0.349920722706601 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_p72 | -0.0468929985066413 | 0.0719124850996844 | -0.65208424436506 | 0.514540169877469 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | h_p168 | 0.0080418021320104 | 0.0832606225731861 | 0.0965858995942735 | 0.923080225198438 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_m1 | 7.98872677989915e-09 | 5.16439111082723e-09 | 1.54688647866941 | 0.12229885110369 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_pre | 1.06085809040405e-08 | 5.94381634994188e-09 | 1.78480967100275 | 0.0746832407281307 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_event | 4.33268012180226e-08 | 1.50676474065421e-08 | 2.87548547221851 | 0.0041446715133582 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_p1 | 1.70689051446878e-08 | 8.89166187500235e-09 | 1.91965297203604 | 0.055268592171209 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_p6 | 1.99637887626094e-08 | 9.26819119677679e-09 | 2.15401132095249 | 0.0315469513271694 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_p24 | 1.36957578520508e-08 | 1.36015651381557e-08 | 1.00692513787482 | 0.314285023838555 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_p72 | 9.10328257238246e-09 | 1.26120717611202e-08 | 0.721791212800228 | 0.470640561317281 | cluster:event_id | NA |
| task2_borrow_joint_million | borrow_size_interaction | size_p168 | -8.21046742506585e-10 | 1.42390952256513e-08 | -0.0576614405266069 | 0.954033171795864 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_m1 | 0.259092552039896 | 0.269950007491244 | 0.95977975495444 | 0.337619087721418 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_pre | 0.258415894324959 | 0.255026443319562 | 1.01329058650263 | 0.311399984354076 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_event | 0.257892112838635 | 0.254998039482527 | 1.01134939453645 | 0.31232692942034 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_p1 | 0.227865949562581 | 0.254241187818156 | 0.896258987452343 | 0.370535650752564 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_p6 | 0.247202918277104 | 0.284353306315762 | 0.86935130623238 | 0.385062359075478 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_p24 | 0.209780628572054 | 0.306458387171784 | 0.684532182356171 | 0.493948911399092 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_p72 | 0.310003940292339 | 0.37039712309726 | 0.836950183900152 | 0.403011041345207 | cluster:event_id | NA |
| task2_placebo_capacity_million | horizons | h_p168 | 0.389942235958411 | 0.480678764003085 | 0.81123250112191 | 0.417609111898425 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_m1 | 0.306343970954192 | 0.252234641793741 | 1.21451981684854 | 0.225109131185213 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_pre | 0.28715549435136 | 0.239829885655056 | 1.19732990559972 | 0.23173203432889 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_event | 0.28767972967911 | 0.239796700648061 | 1.19968176752075 | 0.230817806553057 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_p1 | 0.263895267119777 | 0.238009579883939 | 1.10875901402145 | 0.268054692440839 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_p6 | 0.293178420092163 | 0.265387575518134 | 1.10471795644454 | 0.269800694419673 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_p24 | 0.214311302196617 | 0.283362961476181 | 0.756313743617588 | 0.449808955297649 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_p72 | 0.311945116324415 | 0.339574478036929 | 0.91863534069981 | 0.358718894474449 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | h_p168 | 0.111788971340208 | 0.408404530599775 | 0.273721183200481 | 0.784409283450292 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_m1 | -0.113985236177434 | 0.100206235132155 | -1.13750642389775 | 0.255858681080804 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_pre | -0.0693289253936666 | 0.104220585963391 | -0.665213352552245 | 0.506213574429301 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_event | -0.0718570705121656 | 0.104150640936043 | -0.689934021205798 | 0.490548275910831 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_p1 | -0.086914009471706 | 0.109396036110366 | -0.794489568013431 | 0.427278579154626 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_p6 | -0.110907324122283 | 0.10429126933693 | -1.0634382420256 | 0.288084553111715 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_p24 | -0.0109294051904626 | 0.159751924611723 | -0.0684148577053237 | 0.945482104289779 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_p72 | -0.0046827251659754 | 0.203484463272418 | -0.0230126914392789 | 0.981649115065765 | cluster:event_id | NA |
| task2_placebo_capacity_million | sharing_interaction | count_p168 | 0.670992877876065 | 0.752219294526494 | 0.892017637354597 | 0.372802502177246 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_m1 | 0.274979712530447 | 0.288489882853359 | 0.953169344486928 | 0.340983017213018 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_pre | 0.273786086118855 | 0.27252461696999 | 1.00462882642636 | 0.315580728566489 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_event | 0.269112213343905 | 0.272522273349839 | 0.987487041099364 | 0.323900400793496 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_p1 | 0.235344618072187 | 0.271708118044842 | 0.866167046335165 | 0.386830398229291 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_p6 | 0.257347348478925 | 0.303889489663337 | 0.846845176396284 | 0.397502558305991 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_p24 | 0.222289214953838 | 0.327500268558102 | 0.678745137927733 | 0.497625794439648 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_p72 | 0.321698631301774 | 0.395849961169872 | 0.812678193401975 | 0.41680462929023 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | h_p168 | 0.401269536136371 | 0.5135509427076 | 0.781362670703618 | 0.434973630005362 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_m1 | -7.91792571120197e-08 | 6.44324995693828e-08 | -1.22887141801409 | 0.219720881147006 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_pre | -8.3127121658171e-08 | 6.4155880517264e-08 | -1.29570541294031 | 0.195698428336348 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_event | -8.22553235415165e-08 | 6.4047988022387e-08 | -1.28427646334129 | 0.19966345638422 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_p1 | -7.71551394164941e-08 | 6.38065787600036e-08 | -1.20920351656368 | 0.227178689804179 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_p6 | -8.06541286200475e-08 | 6.8826760408727e-08 | -1.17184258188361 | 0.241840371148466 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_p24 | -5.31486695960884e-08 | 6.39395569554689e-08 | -0.831232997643448 | 0.406254451161928 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_p72 | 3.50568308984127e-09 | 8.74490508387069e-08 | 0.0400882920537038 | 0.96803936954133 | cluster:event_id | NA |
| task2_placebo_capacity_million | borrow_size_interaction | size_p168 | 1.03972738933839e-07 | 1.74179668421597e-07 | 0.596928102321199 | 0.550836245164363 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_m1 | -1568.13380126846 | 1662.23783851564 | -0.943387140476108 | 0.345927853747274 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_pre | -1568.23533624611 | 1662.23624721715 | -0.943449126964703 | 0.345896191157707 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_event | -1568.24627098708 | 1662.23624412054 | -0.943455707053733 | 0.345892830168514 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_p1 | -1565.10668388807 | 1659.15144667721 | -0.943317553694399 | 0.34596340075975 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_p6 | 155.632901432874 | 154.801520603811 | 1.00537062443456 | 0.315193316830671 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_p24 | 2030.06683199903 | 2139.88223022825 | 0.948681569163972 | 0.343230146522382 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_p72 | -1361.30165036846 | 1458.81081385013 | -0.933158458550001 | 0.351178003909406 | cluster:event_id | NA |
| task2_placebo_capacity_share | horizons | h_p168 | -970.677469104856 | 1048.15718316943 | -0.926080061932805 | 0.354840674487651 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_m1 | -1966.14278288487 | 2083.78171929487 | -0.94354546096613 | 0.345846987594541 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_pre | -1966.26851535257 | 2083.77949207893 | -0.943606808122907 | 0.345815656246562 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_event | -1966.28242527532 | 2083.77946035228 | -0.943613497823277 | 0.345812239778515 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_p1 | -1962.34719711715 | 2079.91289824684 | -0.943475661298708 | 0.345882638032547 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_p6 | 195.153058144488 | 194.03517727921 | 1.00576122783999 | 0.315005523174871 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_p24 | 2545.35164445979 | 2682.52919191258 | 0.948862607770919 | 0.343138139644966 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_p72 | -1706.82810368017 | 1828.80114813373 | -0.933304370145418 | 0.351102756534752 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | h_p168 | -1217.06046183634 | 1314.01319420152 | -0.926216317466966 | 0.354769942417335 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_m1 | 960.122443149781 | 1024.43067171336 | 0.937225397150568 | 0.349084501318218 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_pre | 960.180815081916 | 1024.43037522667 | 0.937282648290729 | 0.349055087498845 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_event | 960.187992153075 | 1024.43045926123 | 0.937289577318422 | 0.349051527691354 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_p1 | 958.268656477588 | 1022.5276969974 | 0.937156674867088 | 0.349119810731914 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_p6 | -95.335007922462 | 95.4783977960162 | -0.998498195645673 | 0.318509497512272 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_p24 | -1243.02851420228 | 1318.88686510669 | -0.942483049220246 | 0.346389872460997 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_p72 | 833.518131121599 | 898.949150395499 | 0.927213881624881 | 0.354252365502214 | cluster:event_id | NA |
| task2_placebo_capacity_share | sharing_interaction | count_p168 | 594.353021811685 | 645.841034900925 | 0.92027757558462 | 0.35786110622425 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_m1 | -1674.54969963677 | 1776.5850921341 | -0.942566560448413 | 0.346375814256564 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_pre | -1674.65996171417 | 1776.58339063263 | -0.942629527296118 | 0.346343628024624 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_event | -1674.67207979451 | 1776.58337834752 | -0.942636354817298 | 0.34634013817309 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_p1 | -1671.31855615448 | 1773.28638017247 | -0.942497824853272 | 0.346410951431797 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_p6 | 166.20955630587 | 165.450153816928 | 1.00458991709238 | 0.31559945214712 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_p24 | 2167.83993292826 | 2287.08679861391 | 0.947860804514322 | 0.343676275221877 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_p72 | -1453.70075062498 | 1559.1645919998 | -0.932358750374421 | 0.35161890739891 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | h_p168 | -1036.56226858342 | 1120.26174785504 | -0.925285783048577 | 0.355281252583742 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_m1 | 0.0003123407536431 | 0.0003373570845249 | 0.925846137433178 | 0.354990226353434 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_pre | 0.0003123607474487 | 0.0003373574569501 | 0.925904381283259 | 0.354959985429945 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_event | 0.000312363007731 | 0.0003373575405083 | 0.925910851912104 | 0.354956625900527 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_p1 | 0.0003117372697952 | 0.000336729691297 | 0.925778978962249 | 0.355025097882622 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_p6 | -3.10064440648385e-05 | 3.14930761939687e-05 | -0.984547964570593 | 0.325341130990282 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_p24 | -0.0004043558391613 | 0.0004343833679597 | -0.930873207831377 | 0.35238611675098 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_p72 | 0.0002710757418713 | 0.0002959704920931 | 0.915887729057839 | 0.360184725364819 | cluster:event_id | NA |
| task2_placebo_capacity_share | borrow_size_interaction | size_p168 | 0.0001933671685736 | 0.000212595581074 | 0.909554034927289 | 0.363513278263476 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_m1 | -0.0021763725111372 | 0.0062570045151947 | -0.34782978114401 | 0.728112954747055 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_pre | -0.0066893990514542 | 0.0069084951840637 | -0.968285983159562 | 0.333365061981299 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_event | -0.0069048259442772 | 0.006874611365765 | -1.0043950962323 | 0.315669224916723 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_p1 | -0.0030256883354677 | 0.0060638725979381 | -0.498969641363599 | 0.618018050774045 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_p6 | 0.0043944994783044 | 0.0050487024889731 | 0.870421556410277 | 0.384483626993815 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_p24 | 0.0018620482876823 | 0.0052247360548647 | 0.356390881401292 | 0.721696705845436 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_p72 | 0.007260252440713 | 0.0061455725211684 | 1.18137934516354 | 0.238008102462037 | cluster:event_id | NA |
| task2_placebo_delta_D | horizons | h_p168 | 0.0100473088242213 | 0.006253280019251 | 1.60672619701822 | 0.108739492030438 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_m1 | -0.0020032133487479 | 0.0054277786021952 | -0.369066886393968 | 0.712232557426873 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_pre | -0.006168467893923 | 0.0057629890798305 | -1.07035911546521 | 0.284968997474932 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_event | -0.0065090098283124 | 0.0057560909786779 | -1.13080384803221 | 0.258674404119105 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_p1 | -0.0009542546334327 | 0.0055732351730761 | -0.171220952247397 | 0.864118616578777 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_p6 | 0.0050819358649705 | 0.0044941489869386 | 1.13078936184361 | 0.258680496886785 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_p24 | 0.0002654307529976 | 0.0049682790204386 | 0.0534250898360869 | 0.957414342256789 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_p72 | 0.0070432493963978 | 0.0064440646186226 | 1.09298242851937 | 0.274922621571106 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | h_p168 | 0.0098112100760685 | 0.0063973484286702 | 1.5336369724836 | 0.125745206481663 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_m1 | -0.0004150255486615 | 0.0079968589090545 | -0.0518985708490644 | 0.958630035027997 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_pre | -0.0012485607835364 | 0.0083460730214891 | -0.149598593293118 | 0.881141043512101 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_event | -0.0009486867367033 | 0.0082908852140782 | -0.114425264879124 | 0.908946165755278 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_p1 | -0.0049647844032094 | 0.0070986794001301 | -0.69939549645226 | 0.484626911714489 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_p6 | -0.0016476382745754 | 0.0060041111366097 | -0.274418350541363 | 0.783875361628727 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_p24 | 0.0038267514071562 | 0.0057983319694502 | 0.659974528419255 | 0.509571060407947 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_p72 | 0.0005201099744619 | 0.0058893624613376 | 0.0883134597125438 | 0.929662551095509 | cluster:event_id | NA |
| task2_placebo_delta_D | sharing_interaction | count_p168 | 0.000565878300278 | 0.0062779767646702 | 0.0901370491624912 | 0.928214046340979 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_m1 | 0.0027143019664435 | 0.0056490292993547 | 0.480489978473585 | 0.631099776052534 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_pre | -0.0016949877431595 | 0.0063155100310989 | -0.268384934045399 | 0.788519307501215 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_event | -0.0019244990608411 | 0.0062738729105911 | -0.306748174256501 | 0.759169197376213 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_p1 | 0.0017416553415038 | 0.0054064176814477 | 0.322145909569735 | 0.747483591968758 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_p6 | 0.0055917155732639 | 0.0053195039231176 | 1.05117237510876 | 0.293712783468088 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_p24 | 0.0034564917481293 | 0.0054740025491928 | 0.631437730813453 | 0.528057456241675 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_p72 | 0.0082834223857123 | 0.0065096803104697 | 1.27247760114885 | 0.20382469610337 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | h_p168 | 0.0123644811302689 | 0.0065747853535649 | 1.88059084294891 | 0.0606378867654421 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_m1 | -6.02682261982529e-10 | 1.07052655063587e-09 | -0.562977407355798 | 0.57371533658918 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_pre | 2.22653067985859e-10 | 1.17816673287418e-09 | 0.188982647169717 | 0.850186966707012 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_event | 2.65463066887635e-10 | 1.17028562194626e-09 | 0.226836134623404 | 0.820648547796476 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_p1 | -4.14526736600103e-10 | 1.0189933302564e-09 | -0.406800245194737 | 0.684337556948265 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_p6 | -1.12839893674164e-09 | 1.03311788293454e-09 | -1.09222670072892 | 0.275285964632373 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_p24 | -7.04500944296064e-10 | 1.03754761565862e-09 | -0.679005892032106 | 0.497464138281418 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_p72 | -1.85389497312731e-09 | 1.34998993697382e-09 | -1.37326577210128 | 0.170316236775409 | cluster:event_id | NA |
| task2_placebo_delta_D | borrow_size_interaction | size_p168 | -2.69282175072703e-09 | 1.47189211159938e-09 | -1.82949669307009 | 0.067950578703097 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_m1 | -0.0044998241566208 | 0.002960802785606 | -1.51979867706716 | 0.129288063725654 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_pre | -0.004288694643141 | 0.0030706782808358 | -1.39666036325163 | 0.163227890674518 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_event | -0.0043119587058765 | 0.0030403480409069 | -1.41824509821259 | 0.156835205430688 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_p1 | -0.0041487837820196 | 0.0030225362504637 | -1.37261671597258 | 0.170578788187544 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_p6 | -0.004560340377096 | 0.0030673698839356 | -1.48672659302661 | 0.137811466341369 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_p24 | -0.0095545900657752 | 0.0036725440635021 | -2.60162707392104 | 0.0095946860748792 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_p72 | -0.0066740303245845 | 0.0044860377296089 | -1.48773388162437 | 0.137545600774943 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | horizons | h_p168 | -0.0085633356537286 | 0.0051186860436739 | -1.67295582902799 | 0.0950549516115888 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_m1 | -0.0044998241566208 | 0.0029527246233815 | -1.52395659283238 | 0.128246201218264 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_pre | -0.004288694643141 | 0.0030601262910672 | -1.40147635594652 | 0.161784736020821 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_event | -0.0043119587058765 | 0.0030301705493709 | -1.42300858503546 | 0.155450422012035 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_p1 | -0.0041487837820196 | 0.0030126596069208 | -1.37711667540831 | 0.16918440324727 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_p6 | -0.004560340377096 | 0.0030462529522968 | -1.49703273119773 | 0.135109953001171 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_p24 | -0.0095545900657751 | 0.0034682724840472 | -2.7548556550048 | 0.0061181973142735 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_p72 | -0.0066740303245845 | 0.0044107044326819 | -1.51314385863899 | 0.130969296505752 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | h_p168 | -0.0085633356537286 | 0.0049961238092087 | -1.71399588575945 | 0.0872418392359395 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_m1 | -0.0068037313319729 | 0.008896096206407 | -0.764799657525379 | 0.444805547081499 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_pre | -0.007671722599479 | 0.0089732279608882 | -0.854956837485667 | 0.393045667010492 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_event | -0.0075221620522531 | 0.008938061915132 | -0.841587597364729 | 0.400481245559384 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_p1 | -0.0074116158556489 | 0.0085682291912347 | -0.865011391528952 | 0.387509309378603 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_p6 | -0.0101335699313123 | 0.0091609766410266 | -1.10616698725439 | 0.269265616909811 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_p24 | -0.0318526916468505 | 0.0134908124741029 | -2.36106548126698 | 0.0186626196895199 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_p72 | -0.0220915426122375 | 0.0143906151867853 | -1.53513538688213 | 0.125477560470389 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | sharing_interaction | count_p168 | -0.0297558856648658 | 0.0151400178901944 | -1.96537982191801 | 0.0500061054094964 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_m1 | -0.0043694244783027 | 0.0031112466796563 | -1.40439667059296 | 0.160954171166956 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_pre | -0.0041568138511361 | 0.0032300099414287 | -1.28693531181437 | 0.198839409684509 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_event | -0.0041814331662454 | 0.0031976323714865 | -1.30766538503035 | 0.191716037252389 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_p1 | -0.0040265621352415 | 0.003180042561551 | -1.26619756097782 | 0.206157807654402 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_p6 | -0.004473772762061 | 0.0032293806665365 | -1.38533459632652 | 0.166699723504989 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_p24 | -0.0098020789175362 | 0.0038785496597765 | -2.52725368433239 | 0.0118690058765278 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_p72 | -0.0059449813863811 | 0.0046706153378157 | -1.27284757069319 | 0.203789921850389 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | h_p168 | -0.0073386015958935 | 0.0052694897237525 | -1.39265886843166 | 0.164474054744447 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_m1 | -3.86713070947664e-08 | 7.75022654312638e-10 | -49.8970022096499 | 9.75849225428959e-177 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_pre | -3.76162151926496e-08 | 8.04606563538756e-10 | -46.7510667912141 | 7.87633425752657e-167 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_event | -3.76100869155679e-08 | 7.96539667110059e-10 | -47.2168411298608 | 2.51666060577546e-168 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_p1 | -3.64801330790961e-08 | 7.92156551983815e-10 | -46.0516712103663 | 1.44929442166532e-164 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_p6 | -3.51528256861432e-08 | 8.04446961109291e-10 | -43.6981272670473 | 9.03416630316787e-157 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_p24 | -2.85547275257606e-08 | 9.66172327569533e-10 | -29.5544870319271 | 7.58345631137629e-104 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_p72 | -3.34019566108516e-08 | 1.16350111322468e-09 | -28.7081432335523 | 2.41746266761997e-100 | cluster:event_id | NA |
| task2_placebo_delta_market_duplication | borrow_size_interaction | size_p168 | -9.97593629047496e-08 | 1.31269153979167e-09 | -75.9960431531248 | 1.68762341616403e-244 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_m1 | 0.127623699898356 | 0.123280347274279 | 1.03523150867197 | 0.301049505534963 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_pre | 0.149401152017755 | 0.124431384358027 | 1.20067097853611 | 0.23043404442463 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_event | 0.148144666050351 | 0.124441691294613 | 1.1904745468271 | 0.234411589424697 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_p1 | 0.147350649609795 | 0.12222132037965 | 1.20560511989305 | 0.228526649309233 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_p6 | 0.173267067866164 | 0.206548401446835 | 0.838869081786444 | 0.401934255697206 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_p24 | -0.0192204590394715 | 0.0161426428512222 | -1.1906637108072 | 0.234337356771993 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_p72 | -0.0163826852611033 | 0.0181451836195508 | -0.902866876665362 | 0.367021115349974 | cluster:event_id | NA |
| task2_placebo_joint_million | horizons | h_p168 | -0.0150509997108577 | 0.0187300307447345 | -0.803575814475847 | 0.422014900366618 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_m1 | 0.127623699898355 | 0.123365843533855 | 1.03451406193589 | 0.301384278547174 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_pre | 0.149401152017755 | 0.124549671873927 | 1.19953067535163 | 0.230876462489652 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_event | 0.148144666050352 | 0.124558459025663 | 1.18935853260539 | 0.234849881214301 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_p1 | 0.147350649609795 | 0.12231766527822 | 1.20465551132484 | 0.228892861309544 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_p6 | 0.173267067866164 | 0.206682232092763 | 0.838325898224277 | 0.402238886259416 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_p24 | -0.0192204590394714 | 0.0159488671015933 | -1.2051300519992 | 0.228709804628673 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_p72 | -0.0163826852611034 | 0.0180670075593464 | -0.906773587562283 | 0.364953089818046 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | h_p168 | -0.0150509997108576 | 0.0186184889553943 | -0.808389969074096 | 0.419241572020111 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_m1 | -0.0839543136140166 | 0.114090969546837 | -0.735854151713136 | 0.462156432208042 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_pre | -0.0262858613813776 | 0.130688492337531 | -0.201133710483771 | 0.840673900857696 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_event | -0.0316447857487962 | 0.130859526939028 | -0.241822559572147 | 0.809014480820132 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_p1 | -0.067971330029292 | 0.0985172433034634 | -0.689943483496787 | 0.490542330182203 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_p6 | 0.151506473062119 | 0.257326101217823 | 0.588772271235211 | 0.55627370334273 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_p24 | -0.0740257531161523 | 0.0699526971310492 | -1.05822586050503 | 0.290451485447299 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_p72 | -0.0532005710605686 | 0.0728145316678619 | -0.730631233106587 | 0.465338623555814 | cluster:event_id | NA |
| task2_placebo_joint_million | sharing_interaction | count_p168 | -0.0628642579274135 | 0.071814959463105 | -0.875364386436924 | 0.381786130568195 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_m1 | 0.128339755397242 | 0.131511639651885 | 0.975881342039082 | 0.329613801168824 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_pre | 0.144832662205112 | 0.132108950351236 | 1.09631226211432 | 0.273490724752539 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_event | 0.143490366091818 | 0.132119948360213 | 1.08606132437022 | 0.277995842804825 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_p1 | 0.149176975047948 | 0.130419198038264 | 1.14382680841344 | 0.253264389601799 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_p6 | 0.185762184472183 | 0.220930722385537 | 0.840816444478089 | 0.4008685531801 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_p24 | -0.019875462486645 | 0.0172413602090083 | -1.15277810136235 | 0.249574037290169 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_p72 | -0.0180652390676815 | 0.0193430078372634 | -0.933941567912702 | 0.350802629109856 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | h_p168 | -0.0183164505645009 | 0.019843873964163 | -0.923027963067059 | 0.356455405892269 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_m1 | -2.08301404746395e-08 | 2.26108279340152e-08 | -0.921246251372475 | 0.35738369432211 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_pre | -2.36840989734386e-08 | 2.27782964414752e-08 | -1.03976603493113 | 0.298970977718871 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_event | -2.34548162291143e-08 | 2.27747760132782e-08 | -1.02985935911903 | 0.303593602191275 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_p1 | -2.44641307790784e-08 | 2.25166695901852e-08 | -1.08648975289588 | 0.277806546609825 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_p6 | -3.0750582467563e-08 | 3.79925312933723e-08 | -0.809384934899754 | 0.418693957895377 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_p24 | 4.11476410522988e-09 | 3.26012535649222e-09 | 1.26214904498556 | 0.2075067925875 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_p72 | 2.96988508976126e-09 | 3.62808344534634e-09 | 0.818582354705944 | 0.413430092026645 | cluster:event_id | NA |
| task2_placebo_joint_million | borrow_size_interaction | size_p168 | 4.79297512930139e-09 | 3.69444959599829e-09 | 1.29734484251538 | 0.195134444936787 | cluster:event_id | NA |
| task3_25 | LPM_lag | D | 0.0809433841797816 | 0.0638953695799574 | 1.26681142486375 | 0.237022541908747 | cluster:vault | 0.3823 |
| task3_25 | LPM_lag | utilization10 | 0.0045404685071198 | 0.0108445133086122 | 0.418688084739958 | 0.685258858250446 | cluster:vault | 0.873 |
| task3_25 | LPM_lag | log_assets | 0.0105472299745814 | 0.0068191421084263 | 1.54670922043821 | 0.156336877835409 | cluster:vault | 0.2163 |
| task3_25 | LPM_lag | Flow | 0.0010829915804599 | 0.0003994698311958 | 2.71107226600307 | 0.023955403360921 | cluster:vault | 0.0226 |
| task3_25 | LPM_lag | shared_exposure | -0.0758899969280874 | 0.0559443239171805 | -1.3565271972977 | 0.207979813552392 | cluster:vault | 0.3065 |
| task3_25 | LPM_lag | refused25 | 0.722628603365624 | 0.0809514450616786 | 8.92669183131984 | 9.12839417716751e-06 | cluster:vault | 0.0081 |
| task3_25 | LPM_no_lag | D | -0.329776838235406 | 0.116867785777686 | -2.82179418426504 | 0.0199883706349657 | cluster:vault | 0.0568 |
| task3_25 | LPM_no_lag | utilization10 | 0.0958130173325839 | 0.0109262185867504 | 8.76909212202387 | 1.05555406032276e-05 | cluster:vault | 0.0564 |
| task3_25 | LPM_no_lag | log_assets | 0.0334462569287797 | 0.0296719163416016 | 1.12720245445982 | 0.288811305856686 | cluster:vault | 0.4143 |
| task3_25 | LPM_no_lag | Flow | 0.0026997516684726 | 0.0012425673087939 | 2.17272066419737 | 0.0578565397032769 | cluster:vault | 0.4337 |
| task3_25 | LPM_no_lag | shared_exposure | -0.0041966329033466 | 0.196051042113053 | -0.0214058178835216 | 0.98338900030881 | cluster:vault | 0.9866 |
| task3_25 | FE_logit | D | 1.08687714530268 | 0.771694080412482 | 1.40843006690129 | 0.1590037613184 | cluster:vault asymptotic z | 0.3285 |
| task3_25 | FE_logit | utilization10 | 0.140057715520535 | 0.152584007738298 | 0.917905602274862 | 0.358668288417115 | cluster:vault asymptotic z | 0.5444 |
| task3_25 | FE_logit | log_assets | 0.161165552327997 | 0.190357471262774 | 0.846646844270797 | 0.397191995228231 | cluster:vault asymptotic z | 0.5776 |
| task3_25 | FE_logit | Flow | 0.0163004476899936 | 0.0025720802875168 | 6.33745679289456 | 2.33588684840287e-10 | cluster:vault asymptotic z | 0.0001 |
| task3_25 | FE_logit | shared_exposure | -1.47433492076486 | 0.731206967885459 | -2.01630316109872 | 0.0437682845786372 | cluster:vault asymptotic z | 0.179 |
| task3_25 | FE_logit | refused25 | 4.03187926575791 | 0.762156866892117 | 5.29009110971984 | 1.22255444136184e-07 | cluster:vault asymptotic z | 0.0289 |
| task3_10 | LPM_lag | D | -0.0234127528324731 | 0.034874274066334 | -0.671347388850014 | 0.51885705517653 | cluster:vault | 0.5393 |
| task3_10 | LPM_lag | utilization10 | 0.0175116610776279 | 0.0020157674250488 | 8.68734203163529 | 1.13911558615395e-05 | cluster:vault | 0.033 |
| task3_10 | LPM_lag | log_assets | -0.0012213349833795 | 0.0016108481039746 | -0.758193761637688 | 0.467723425561689 | cluster:vault | 0.4462 |
| task3_10 | LPM_lag | Flow | 0.000104279149251 | 4.56445229445891e-05 | 2.28459281692212 | 0.0481990767381856 | cluster:vault | 0.1506 |
| task3_10 | LPM_lag | shared_exposure | -0.0466695904285067 | 0.0594987655793186 | -0.784379137518253 | 0.452967363469776 | cluster:vault | 0.7528 |
| task3_10 | LPM_lag | refused10 | 0.345629957427805 | 0.0492371620807448 | 7.01969696915109 | 6.18883746306894e-05 | cluster:vault | 0.0017 |
| task3_10 | LPM_no_lag | D | -0.101096133687307 | 0.0415901957517645 | -2.43076840250309 | 0.0379347161021351 | cluster:vault | 0.0722 |
| task3_10 | LPM_no_lag | utilization10 | 0.0341636829229434 | 0.0066087905657874 | 5.16943040982461 | 0.0005876123836245 | cluster:vault | 0.0121 |
| task3_10 | LPM_no_lag | log_assets | -0.0023609364788356 | 0.0030202768987724 | -0.781695373624582 | 0.454465424891221 | cluster:vault | 0.4938 |
| task3_10 | LPM_no_lag | Flow | 0.0001228457037589 | 7.38309189239679e-05 | 1.66387884031942 | 0.13049569979758 | cluster:vault | 0.3903 |
| task3_10 | LPM_no_lag | shared_exposure | -0.0426502692334688 | 0.0727980293960026 | -0.585871205406705 | 0.572359083488904 | cluster:vault | 0.777 |
| task3_10 | FE_logit | D | 0.504985042376995 | 1.24411475723282 | 0.405899085627912 | 0.684816749925443 | cluster:vault asymptotic z | 0.6277 |
| task3_10 | FE_logit | utilization10 | 0.85709149273438 | 0.162083616756418 | 5.28795883190608 | 1.23688805870962e-07 | cluster:vault asymptotic z | 0.1858 |
| task3_10 | FE_logit | log_assets | -0.384721207342782 | 0.0846749703593308 | -4.54350566300951 | 5.53263183495115e-06 | cluster:vault asymptotic z | 0.0001 |
| task3_10 | FE_logit | Flow | 0.0327038572775442 | 0.0095082220997732 | 3.43953442971471 | 0.0005827156602393 | cluster:vault asymptotic z | 0.0617 |
| task3_10 | FE_logit | shared_exposure | -3.18241832741896 | 1.99280851502325 | -1.5969513896732 | 0.110276543278542 | cluster:vault asymptotic z | 0.3769 |
| task3_10 | FE_logit | refused10 | 0.675531122693569 | 0.401746043991944 | 1.68148792700275 | 0.0926681795332808 | cluster:vault asymptotic z | 0.6866 |
| task3_cross_25 | LPM_lag | D | -0.0880102769655242 | 0.0515952467856515 | -1.70578265341294 | 0.0889699418429757 | cluster:entity | NA |
| task3_cross_25 | LPM_lag | utilization10 | 0.0123684764609799 | 0.0053865007998407 | 2.296198760677 | 0.0222777393347647 | cluster:entity | NA |
| task3_cross_25 | LPM_lag | log_assets | 0.0019688419738265 | 0.0007487315423525 | 2.62956996260695 | 0.0089412452681812 | cluster:entity | NA |
| task3_cross_25 | LPM_lag | Flow | 0.0069056983239826 | 0.0036190082630768 | 1.90817423503517 | 0.0572182373900481 | cluster:entity | NA |
| task3_cross_25 | LPM_lag | shared_market_share | -0.014166608926474 | 0.032099901608605 | -0.44132873362691 | 0.659258044577303 | cluster:entity | NA |
| task3_cross_25 | LPM_lag | refused25 | 0.563969179223623 | 0.0567368063756834 | 9.9400938341382 | 1.38234483465469e-20 | cluster:entity | NA |
| task3_cross_25 | LPM_no_lag | D | -0.319820937963787 | 0.0759230425958833 | -4.21243573793668 | 3.24659778565626e-05 | cluster:entity | NA |
| task3_cross_25 | LPM_no_lag | utilization10 | 0.0459250042117009 | 0.0077959205370171 | 5.89090204211761 | 9.3049533920419e-09 | cluster:entity | NA |
| task3_cross_25 | LPM_no_lag | log_assets | 0.0054213278857862 | 0.0011596061242424 | 4.67514595900226 | 4.25546077562764e-06 | cluster:entity | NA |
| task3_cross_25 | LPM_no_lag | Flow | 0.0017723456061859 | 0.0026096236103795 | 0.679157560935815 | 0.497504207129893 | cluster:entity | NA |
| task3_cross_25 | LPM_no_lag | shared_market_share | -0.0552864592632075 | 0.0536835187247238 | -1.02985908108414 | 0.303814723139827 | cluster:entity | NA |
| task3_cross_25 | FE_logit | D | -1.02048684801014 | 0.524880007190032 | -1.9442288409371 | 0.0518678613205234 | cluster:entity asymptotic z | NA |
| task3_cross_25 | FE_logit | utilization10 | 0.158165744336967 | 0.0654809352730214 | 2.41544723937583 | 0.0157158991681083 | cluster:entity asymptotic z | NA |
| task3_cross_25 | FE_logit | log_assets | 0.0373265763533792 | 0.0131310467859049 | 2.84262001057267 | 0.0044744381964082 | cluster:entity asymptotic z | NA |
| task3_cross_25 | FE_logit | Flow | 0.0547429190150003 | 0.0350560100963406 | 1.56158441489936 | 0.118385923332439 | cluster:entity asymptotic z | NA |
| task3_cross_25 | FE_logit | shared_market_share | -0.17332611104082 | 0.442792636579792 | -0.391438557740302 | 0.695473096397033 | cluster:entity asymptotic z | NA |
| task3_cross_25 | FE_logit | refused25 | 3.21649021654393 | 0.379062143345193 | 8.4853902533201 | 2.14995956414967e-17 | cluster:entity asymptotic z | NA |
| task4_duplication | asset_weighted | L_cash_hhi | 0.0515891878265034 | 0.0389649772263009 | 1.32398865593796 | 0.186240893534434 | HAC7 | NA |
| task4_duplication | asset_weighted | L_log_assets | -0.019743129752416 | 0.0487523155689947 | -0.404968041455906 | 0.685711183395447 | HAC7 | NA |
| task4_duplication | asset_weighted | L_utilization10 | 0.0149378793034782 | 0.0071303090423549 | 2.09498343125737 | 0.0367825314212607 | HAC7 | NA |
| task4_duplication | exclude_Spark | L_cash_hhi | -0.097983953431987 | 0.0655246126735398 | -1.49537630874932 | 0.1355762818093 | HAC7 | NA |
| task4_duplication | exclude_Spark | L_log_assets | 0.192439761729581 | 0.0440459690117639 | 4.36906636514646 | 1.57843713419109e-05 | HAC7 | NA |
| task4_duplication | exclude_Spark | L_utilization10 | 24.8004914117273 | 16.5674906009755 | 1.49693710466129 | 0.135169761813227 | HAC7 | NA |
| task4_duplication | HAC14_no_calendar_FE | L_cash_hhi | -0.19683239297643 | 0.0719608407558568 | -2.7352708905143 | 0.0064877268517157 | HAC14 | NA |
| task4_duplication | HAC14_no_calendar_FE | L_log_assets | 0.051464094297542 | 0.0223972198613454 | 2.2977893960117 | 0.0220475558356489 | HAC14 | NA |
| task4_duplication | HAC14_no_calendar_FE | L_utilization10 | 0.0110697329858932 | 0.0205317232367326 | 0.539152649695216 | 0.590057358978325 | HAC14 | NA |
| task4_duplication | lagged_outcome | L_cash_hhi | -0.0232390748165882 | 0.0243502108416321 | -0.954368525501875 | 0.340454035425513 | HAC7 | NA |
| task4_duplication | lagged_outcome | L_log_assets | 0.0128260684970363 | 0.0110884207016835 | 1.15670832141938 | 0.24805854691727 | HAC7 | NA |
| task4_duplication | lagged_outcome | L_utilization10 | -0.0169398195245433 | 0.0072598293065882 | -2.33336333530191 | 0.0201070959400843 | HAC7 | NA |
| task4_duplication | lagged_outcome | lag_y | 0.877077992536948 | 0.048771566190807 | 17.9833878843585 | 7.50033998584988e-54 | HAC7 | NA |
| task4_J_assets | asset_weighted | L_cash_hhi | 0.0565728973756318 | 0.038449908951626 | 1.47134021687298 | 0.14196435560178 | HAC7 | NA |
| task4_J_assets | asset_weighted | L_log_assets | -0.0199730514344763 | 0.0488207351397382 | -0.409110009861753 | 0.682672034490821 | HAC7 | NA |
| task4_J_assets | asset_weighted | L_utilization10 | 0.0143838885227872 | 0.0072724697945478 | 1.97785469436678 | 0.0486126234364849 | HAC7 | NA |
| task4_J_assets | asset_weighted | L_spark_flow_share | -0.0590206765217706 | 0.0539693986887116 | -1.09359522165874 | 0.274773079569919 | HAC7 | NA |
| task4_J_assets | exclude_Spark | L_cash_hhi | 0.0905041024174808 | 0.0920742723632276 | 0.982946702640748 | 0.326207747751894 | HAC7 | NA |
| task4_J_assets | exclude_Spark | L_log_assets | -0.218418144441719 | 0.0541350999122819 | -4.03468627185752 | 6.51206454372467e-05 | HAC7 | NA |
| task4_J_assets | exclude_Spark | L_utilization10 | -34.6375188722328 | 19.0204356318212 | -1.82106864126099 | 0.0693180642672574 | HAC7 | NA |
| task4_J_assets | exclude_Spark | L_spark_flow_share | 0.154123421638117 | 0.0402428437408569 | 3.82983425899502 | 0.0001480826414544 | HAC7 | NA |
| task4_J_assets | HAC14_no_calendar_FE | L_cash_hhi | -0.0731736233993581 | 0.0399642830585572 | -1.83097550610732 | 0.0677896345463724 | HAC14 | NA |
| task4_J_assets | HAC14_no_calendar_FE | L_log_assets | 0.0167755342026912 | 0.0084019746862803 | 1.99661803671988 | 0.0464908419125297 | HAC14 | NA |
| task4_J_assets | HAC14_no_calendar_FE | L_utilization10 | -0.112016780589755 | 0.0158296176218571 | -7.07640470323716 | 5.97686478112511e-12 | HAC14 | NA |
| task4_J_assets | HAC14_no_calendar_FE | L_spark_flow_share | -0.0576981292902312 | 0.0685263661897089 | -0.841984370373576 | 0.400260423457491 | HAC14 | NA |
| task4_J_assets | lagged_outcome | L_cash_hhi | -0.0531812806897226 | 0.0196970126707616 | -2.69996682129699 | 0.0072196122578198 | HAC7 | NA |
| task4_J_assets | lagged_outcome | L_log_assets | -0.0076046204264497 | 0.0128449898601365 | -0.592030084044686 | 0.554154394772792 | HAC7 | NA |
| task4_J_assets | lagged_outcome | L_utilization10 | 0.032050957653865 | 0.0223858894482074 | 1.43174823265428 | 0.15297221481376 | HAC7 | NA |
| task4_J_assets | lagged_outcome | L_spark_flow_share | 0.0635670180245935 | 0.042800653275465 | 1.48518803242269 | 0.138256887203107 | HAC7 | NA |
| task4_J_assets | lagged_outcome | lag_y | 0.963719418896928 | 0.139281206671457 | 6.91923513536318 | 1.73956208073786e-11 | HAC7 | NA |
| task4_cross_a | exclude_1 | shared_market_share | 0.439414086544883 | 0.0793465940511752 | 5.53790735190825 | 0.0310940230819796 | cluster:chain | NA |
| task4_cross_a | exclude_1 | active_markets | -0.0089380955141091 | 0.0116030120471932 | -0.770325453231888 | 0.521657041017977 | cluster:chain | NA |
| task4_cross_a | exclude_1 | log_assets | -0.006340327797946 | 0.0031277882732521 | -2.02709622392492 | 0.179865524200412 | cluster:chain | NA |
| task4_cross_a | exclude_1 | utilization10 | 0.0659885545227197 | 0.0090549109154704 | 7.28759842462694 | 0.0183135189850962 | cluster:chain | NA |
| task4_cross_a | exclude_1 | max_market_share | 0.0379100942331925 | 0.224971211272749 | 0.168510868651684 | 0.881681800023306 | cluster:chain | NA |
| task4_cross_a | exclude_8453 | shared_market_share | 0.513251316783526 | 0.059139620347538 | 8.67863732921128 | 0.013018211042504 | cluster:chain | NA |
| task4_cross_a | exclude_8453 | active_markets | -0.0149422469034974 | 0.0054222341881977 | -2.75573617532444 | 0.110315698823974 | cluster:chain | NA |
| task4_cross_a | exclude_8453 | log_assets | -0.0006390488130566 | 0.0009270295090936 | -0.689351101327261 | 0.561837816523288 | cluster:chain | NA |
| task4_cross_a | exclude_8453 | utilization10 | 0.065386516698192 | 0.0091563407261951 | 7.14111877806487 | 0.0190509688043208 | cluster:chain | NA |
| task4_cross_a | exclude_8453 | max_market_share | -0.216688666905145 | 0.0764309031587073 | -2.83509232456923 | 0.105152453991585 | cluster:chain | NA |
| task4_cross_a | exclude_42161 | shared_market_share | 0.450631951363635 | 0.0584596738591913 | 7.70842397186561 | 0.0164161393807504 | cluster:chain | NA |
| task4_cross_a | exclude_42161 | active_markets | -0.0057543131030523 | 0.0048696659143991 | -1.181664862478 | 0.358806275800597 | cluster:chain | NA |
| task4_cross_a | exclude_42161 | log_assets | -0.005198036852575 | 0.0032342906232396 | -1.60716443204736 | 0.249265370168482 | cluster:chain | NA |
| task4_cross_a | exclude_42161 | utilization10 | 0.070115347682824 | 0.0044268978002751 | 15.8384834812463 | 0.0039626470372259 | cluster:chain | NA |
| task4_cross_a | exclude_42161 | max_market_share | 0.0047734493983627 | 0.16476486135884 | 0.0289712828269052 | 0.979518506712327 | cluster:chain | NA |
| task4_cross_a | exclude_137 | shared_market_share | 0.495055019121518 | 0.0593930088679821 | 8.33524060419163 | 0.0140899270092786 | cluster:chain | NA |
| task4_cross_a | exclude_137 | active_markets | -0.0090723606325399 | 0.006024135527368 | -1.50600207968822 | 0.271027381220121 | cluster:chain | NA |
| task4_cross_a | exclude_137 | log_assets | -0.004411225663219 | 0.0029814727846903 | -1.47954584253473 | 0.277113110891767 | cluster:chain | NA |
| task4_cross_a | exclude_137 | utilization10 | 0.0713876210130595 | 0.0022792717206136 | 31.3203644688051 | 0.0010178479890515 | cluster:chain | NA |
| task4_cross_a | exclude_137 | max_market_share | -0.03578720070641 | 0.154702079828955 | -0.231329796897222 | 0.838570538497154 | cluster:chain | NA |
| task4_cross_b | exclude_1 | shared_market_share | 0.538186241357776 | 0.0587700845472973 | 9.15748625348073 | 3.68852843357771e-17 | cluster:entity | NA |
| task4_cross_b | exclude_1 | active_markets | 0.0113637110181804 | 0.0043939123248072 | 2.58623981958466 | 0.0103446440893652 | cluster:entity | NA |
| task4_cross_b | exclude_1 | log_assets | -0.0033709447973157 | 0.0013516409430776 | -2.49396469867226 | 0.0133652331301447 | cluster:entity | NA |
| task4_cross_b | exclude_1 | utilization10 | 0.0668677209585769 | 0.0067917445902662 | 9.84544104535521 | 3.38966979739048e-19 | cluster:entity | NA |
| task4_cross_b | exclude_1 | max_market_share | 0.118206473060361 | 0.0681978069826226 | 1.73328847789022 | 0.0844391964487379 | cluster:entity | NA |
| task4_cross_b | exclude_8453 | shared_market_share | 0.500511409109197 | 0.0472435441192473 | 10.5942815773063 | 3.69041796918866e-21 | cluster:entity | NA |
| task4_cross_b | exclude_8453 | active_markets | -0.0005421792972752 | 0.0028920777517091 | -0.187470512144721 | 0.851478986892561 | cluster:entity | NA |
| task4_cross_b | exclude_8453 | log_assets | 0.0005997286754045 | 0.00210207782716 | 0.285302793101051 | 0.775703053282199 | cluster:entity | NA |
| task4_cross_b | exclude_8453 | utilization10 | 0.0705627559132939 | 0.0057126206452475 | 12.3520815218137 | 1.65985617845649e-26 | cluster:entity | NA |
| task4_cross_b | exclude_8453 | max_market_share | -0.0728861401691258 | 0.0469447688767325 | -1.55259343933528 | 0.12207791304925 | cluster:entity | NA |
| task4_cross_b | exclude_42161 | shared_market_share | 0.553447816167402 | 0.0427475051111684 | 12.9469033275302 | 3.22189732422849e-31 | cluster:entity | NA |
| task4_cross_b | exclude_42161 | active_markets | 0.0066578302796612 | 0.0030450974277281 | 2.1864096100953 | 0.0294962783925428 | cluster:entity | NA |
| task4_cross_b | exclude_42161 | log_assets | -0.0016189483793539 | 0.0014791963172254 | -1.09447837349319 | 0.274553218253761 | cluster:entity | NA |
| task4_cross_b | exclude_42161 | utilization10 | 0.0684903632464015 | 0.0051761997113528 | 13.2317852992 | 2.75739046567745e-32 | cluster:entity | NA |
| task4_cross_b | exclude_42161 | max_market_share | 0.0088733884019452 | 0.0471305628473108 | 0.188272489566747 | 0.850780190719671 | cluster:entity | NA |
| task4_cross_b | exclude_137 | shared_market_share | 0.554389409582512 | 0.0418937991469714 | 13.233209230741 | 9.66624191015182e-33 | cluster:entity | NA |
| task4_cross_b | exclude_137 | active_markets | 0.0048767934794238 | 0.0027824011890781 | 1.75272836231056 | 0.0805167552524842 | cluster:entity | NA |
| task4_cross_b | exclude_137 | log_assets | -0.0009827991353043 | 0.0013065939049719 | -0.752184080734276 | 0.452441617451525 | cluster:entity | NA |
| task4_cross_b | exclude_137 | utilization10 | 0.0670671398929756 | 0.0052000522706368 | 12.8973972572705 | 1.89228867522129e-31 | cluster:entity | NA |
| task4_cross_b | exclude_137 | max_market_share | -0.0128842485477398 | 0.0445179891753446 | -0.289416678210512 | 0.772432439862807 | cluster:entity | NA |
| task4_cross_b | two_way_entity_date | shared_market_share | 0.540979780982373 | 0.0387517524367199 | 13.9601372058147 | 8.4213887358657e-06 | cluster:entity,date | NA |
| task4_cross_b | two_way_entity_date | active_markets | 0.0054131980659101 | 0.0025077020592095 | 2.15862887141243 | 0.0742171501820407 | cluster:entity,date | NA |
| task4_cross_b | two_way_entity_date | log_assets | -0.0013591565330865 | 0.0015740626200721 | -0.863470433612208 | 0.421049595720985 | cluster:entity,date | NA |
| task4_cross_b | two_way_entity_date | utilization10 | 0.0683456672120925 | 0.0045036042199188 | 15.1757711989452 | 5.16499053645295e-06 | cluster:entity,date | NA |
| task4_cross_b | two_way_entity_date | max_market_share | 0.0013746760436903 | 0.03665375729749 | 0.0375043691301045 | 0.971299546929764 | cluster:entity,date | NA |
| task4_cross_c | exclude_1 | shared_market_share | 0.525687173667913 | 0.084228795122384 | 6.24118121248312 | 2.19075545691301e-09 | cluster:entity | NA |
| task4_cross_c | exclude_1 | active_markets | 0.0091613616953247 | 0.0084345652361539 | 1.08616881117421 | 0.278587617215468 | cluster:entity | NA |
| task4_cross_c | exclude_1 | log_assets | -0.0003118275700588 | 0.0031552526310221 | -0.0988280833657986 | 0.921364352128816 | cluster:entity | NA |
| task4_cross_c | exclude_1 | utilization10 | 0.0548954242256219 | 0.006755885564022 | 8.12557046820968 | 3.14267826753421e-14 | cluster:entity | NA |
| task4_cross_c | exclude_1 | max_market_share | 0.0106592575222298 | 0.0710402204369116 | 0.150045389170715 | 0.880865653631459 | cluster:entity | NA |
| task4_cross_c | exclude_8453 | shared_market_share | 0.587961258387147 | 0.0632981995552461 | 9.28875169465097 | 2.46831407542583e-17 | cluster:entity | NA |
| task4_cross_c | exclude_8453 | active_markets | 0.0019692227650304 | 0.0036287191011335 | 0.542677101794753 | 0.587947436838294 | cluster:entity | NA |
| task4_cross_c | exclude_8453 | log_assets | 0.00190065742224 | 0.0039896610615586 | 0.476395712045145 | 0.634304845193202 | cluster:entity | NA |
| task4_cross_c | exclude_8453 | utilization10 | 0.0591081752729065 | 0.0076412406621633 | 7.73541599934011 | 4.72962743508967e-13 | cluster:entity | NA |
| task4_cross_c | exclude_8453 | max_market_share | -0.0281427544777595 | 0.0550057614356856 | -0.511632849781833 | 0.609464078858059 | cluster:entity | NA |
| task4_cross_c | exclude_42161 | shared_market_share | 0.573204611337746 | 0.0602465710924895 | 9.51431095485538 | 4.21948596643794e-19 | cluster:entity | NA |
| task4_cross_c | exclude_42161 | active_markets | 0.0079470400943521 | 0.0047380499581313 | 1.67728077259162 | 0.094446080132732 | cluster:entity | NA |
| task4_cross_c | exclude_42161 | log_assets | 9.81122327583309e-05 | 0.0027242582808173 | 0.0360142918346546 | 0.971293005126085 | cluster:entity | NA |
| task4_cross_c | exclude_42161 | utilization10 | 0.0546871478232307 | 0.0063091945612693 | 8.66784932564017 | 2.09830462874509e-16 | cluster:entity | NA |
| task4_cross_c | exclude_42161 | max_market_share | -0.0110728510446009 | 0.0542856205451504 | -0.203973924096372 | 0.838501148288935 | cluster:entity | NA |
| task4_cross_c | exclude_137 | shared_market_share | 0.562520774983829 | 0.0556110919297878 | 10.115262179963 | 2.7376830582875e-21 | cluster:entity | NA |
| task4_cross_c | exclude_137 | active_markets | 0.0065400840844803 | 0.0042897850529436 | 1.52457151203709 | 0.128261388610695 | cluster:entity | NA |
| task4_cross_c | exclude_137 | log_assets | 4.5517654001956e-05 | 0.002828801006041 | 0.0160907939104767 | 0.987171048395757 | cluster:entity | NA |
| task4_cross_c | exclude_137 | utilization10 | 0.0530465071724853 | 0.0059994071250547 | 8.841958224664 | 4.55111675286403e-17 | cluster:entity | NA |
| task4_cross_c | exclude_137 | max_market_share | -0.0138104129272789 | 0.0522419268394586 | -0.264354968562298 | 0.791660681069806 | cluster:entity | NA |
| task4_cross_c | two_way_entity_date | shared_market_share | 0.565627195273895 | 0.0528150033230818 | 10.7095931020551 | 3.91290090547044e-05 | cluster:entity,date | NA |
| task4_cross_c | two_way_entity_date | active_markets | 0.0061789695374416 | 0.0045769924309712 | 1.35000650113167 | 0.225714555771868 | cluster:entity,date | NA |
| task4_cross_c | two_way_entity_date | log_assets | 0.0003743564708168 | 0.0021333249391698 | 0.175480286168916 | 0.866474629945347 | cluster:entity,date | NA |
| task4_cross_c | two_way_entity_date | utilization10 | 0.0552029416407518 | 0.0092625446139248 | 5.95980304999152 | 0.0009991329233305 | cluster:entity,date | NA |
| task4_cross_c | two_way_entity_date | max_market_share | -0.0125414539531705 | 0.0353418735846655 | -0.354861038227814 | 0.73483383868994 | cluster:entity,date | NA |
| task5 | interaction | vault_count | 0.0016568637789779 | 0.0318417382578017 | 0.0520343382501092 | 0.959236499898596 | cluster:market,date | NA |
| task5 | interaction | utilization10 | 0.0115036529528581 | 0.0158522230584414 | 0.72568073956872 | 0.479990533899157 | cluster:market,date | NA |
| task5 | interaction | log_cash | -0.0044675113746339 | 0.0074004547409328 | -0.603680656260701 | 0.555711722000703 | cluster:market,date | NA |
| task5 | interaction | largest_position_supply | -0.0217856244468038 | 0.0853574754819734 | -0.255228078428874 | 0.802258272528615 | cluster:market,date | NA |
| task5 | interaction | utilization_x_vaults | 0.0096294797321563 | 0.003878691334147 | 2.48266203793553 | 0.0263335194818018 | cluster:market,date | NA |
| task5 | count_le_median | vault_count | 0.121014359918205 | 0.0248267812200295 | 4.87434753807608 | 0.0003036634248511 | cluster:market,date | NA |
| task5 | count_le_median | utilization10 | 0.0308998179309628 | 0.0148202268379521 | 2.08497604448494 | 0.0573539748457764 | cluster:market,date | NA |
| task5 | count_le_median | log_cash | -0.0077656160877575 | 0.0079641258068901 | -0.975074512388938 | 0.347319242580988 | cluster:market,date | NA |
| task5 | count_le_median | largest_position_supply | 0.012810617194709 | 0.0996274620704937 | 0.128585200591023 | 0.899653879448873 | cluster:market,date | NA |
| task5 | count_gt_median | vault_count | 0.0691163234207247 | 0.0254449232372512 | 2.71631094251205 | 0.0299247267445759 | cluster:market,date | NA |
| task5 | count_gt_median | utilization10 | 0.077055044341494 | 0.008633513147912 | 8.92510881970796 | 4.50381133423982e-05 | cluster:market,date | NA |
| task5 | count_gt_median | log_cash | 0.030010980383273 | 0.0097333800272952 | 3.08330511077482 | 0.017732875103966 | cluster:market,date | NA |
| task5 | count_gt_median | largest_position_supply | -0.23586359272722 | 0.161854872976134 | -1.45725357779002 | 0.188396448553165 | cluster:market,date | NA |

## Accounting validation and scope

The 3949883 committed market operations reconcile 11263 observed market closing balances with maximum error 0 micro-USDC. Ten randomly drawn vault-days also match direct peer-flow recomputation. The unadjusted supply-stock/net-supply difference exceeds 1 USDC on 7321 market-days; interest and bad debt are separately recorded, with zero remaining balance error. Interest in this reconciliation is derived from the stock-flow balance. Liquidation repayments are recorded separately from voluntary Repay, and enter neither a fabricated OutsideFlow nor a renamed BorrowFlow.

Exact machine-readable values are in outputs/quoteable_values.csv, all_estimates.csv, all_models.csv and all_tests.csv. Every paper-facing table has its numeric companion and definitions note.
