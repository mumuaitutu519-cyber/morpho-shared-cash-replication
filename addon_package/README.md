# Counting the same cash add-on replication

This package reproduces Table C1, Figures C1–C2, and the added numbers in Sections 5–6 and the conclusion through a replay of recorded operations.

Use Python 3.12; run from this folder:

```bash
pip install -r requirements.txt
python code/01_tables.py
python code/02_figures.py
python check/run_checks.py
```

Runtime: 14 seconds after installation, including first font-cache creation; subsequent runs are faster. Checks also execute the single-day replay; run `python code/03_replay_one_day.py` separately for payment traces. All runtime inputs are local CSVs. Results: `output/`; paper-value comparisons: `check/check_report.txt` (nonzero exit on mismatch).

**Data.** UTF-8 intermediates from archived contract states/ledgers. Money: micro-USDC; ratios: fractions; times: UTC Unix seconds; f: request percent. Chains 8453/1/42161=Base/Ethereum/Arbitrum. S=standalone capacities summed; J=joint bound; assets=totalAssets; Dup=(S−J)/S; JA=J/assets; Util=position-weighted utilization. Shared definitions apply across files; all 132 column definitions and source hashes: `check/data_dictionary.csv`, `check/source_manifest.csv`.

| CSV in data/ | Source, rows, and fields |
|---|---|
| base_daily.csv | A1_daily_panel; **439**. date/block/timestamp=close; S/J/assets/Dup/JA/Util=above; W1/W2=windows; weekday/month=calendar; all_pass/excluded/gap/request=25% tests; Errors=strict ten-vault count, Errors_all=all-vault count, Errors_table11=old ten-vault rule. |
| hourly_eth_arb_base.csv | hourly_daily; **3,024**. chain/utc/block=state; target/timestamp/distance_seconds=nearest-block selection; Vaults=positive-asset vault count; S/J/assets/Dup/JA=above. |
| error_calls_windows.csv | Strict A4 events/logs; **192**. chain/vault/holder/tx/block/timestamp/date=failure; request_micro/request_USDC=amount; W1/W2/*_control=membership; resolved/next_success_tx/block/timestamp=next withdrawal; wait_hours=elapsed hours. |
| refill_daily.csv | B1_daily_replay; **878**. tau=observed/capped hours; censored=incomplete; paid_fraction=paid/request; initial_paid_micro/request_micro=initial payment/request; *_inflow_micro=supply/repayment/liquidation inflows through stopping; clipped_outflow_micro=unavailable outflow; horizon_complete/valid_result=coverage; order=priority; date/f=close/request percent. |
| refill_order_check.csv | B1/joint_requests/max-flow diagnosis; **2,634**. Includes run fields; all_pass/excluded/request/J/gap=bound tests; reference_zero/tau_zero/mismatch=initial-payment checks; max_flow_paid_micro/allocation_fully_feasible=feasibility; queue_order_feasible/feasible_queue_order=alternative order; aggregate_bound_not_sufficient=allocation failure. Blank diagnosis=not audited/applicable. |
| a4_unaffected_panel.csv | A3_hour_panel, main list; **72,946**. chain/utc/block/timestamp/vault=state; assets/capacity=assets/standalone capacity; D=capacity share others exhaust (missing at zero capacity); capacity_assets=capacity/assets; Shared=frozen exposure; interaction=W2×Shared. |
| affected_collateral_list.csv | A3_related_markets; **14**. chain/market/collateralToken=contracts; symbol/name=collateral; scope=main/core; pre_block=classification block; in_pre_queue/positive_vaults=baseline queue membership/holding-vault count. |
| replay_example_vaults.csv | Closing vault states; **10** rows. date/block/timestamp/vault identify the start; assets sets requests and priority. |
| replay_example_positions.csv | Closing positions; **75** rows. vault/market identify exposure; rank is withdrawal-queue order; position is remaining claim. |
| replay_example_market_cash.csv | Reconciled daily cash; **33** rows. market identifies venue; cash is its opening cash. |
| replay_example_ledger.csv | Bounded original ledger slice; **36,544** operations. block/log_index order events; timestamp/tx identify them; market/kind/owner describe action; assets_micro gives cash amount; sample_own_operation marks excluded requester actions. |

**Full evidence.** Omitted raw inputs: **3.90 GB**; full ledger: **263 MB**, 3,949,883 rows. Example: 2 June 2025 plus 168 hours. Original project: `/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/`. Full replay: `addon_stress_refill/code/analyze.py` (`b1`); complete pipeline: `addon_stress_refill/code/run_all.py`; original ledger: `Replication_Package/additional_evidence/panel_evidence/raw/market_operations.parquet`. Exact input paths are in the manifest.

**Methods.** Fixed closing queues; own operations removed; outside outflows capped at cash. Seven-day paid shares condition on censoring; inflow shares on completion. Error follow-up need not repay the failed amount. Four 25% initial-payment differences remain: three reflect order; 11 March 2025 is infeasible. OLS: HAC7. Cox: year-month strata, Efron/HAC7 (calendar-dummy fit separates). Paper targets stay fixed.
