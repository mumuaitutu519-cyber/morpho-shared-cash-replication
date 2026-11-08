"""Predeclared review diagnostics; never overwrite the historical analysis data/results."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.multitest import multipletests

import analyze_regressions as reg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/jfs_audit"
OUTCOMES = {
    "Gross count": "ihs_events_gross",
    "CCTP-filtered count": "ihs_events_filtered",
    "CCTP count": "ihs_events_cctp",
    "Gross value": "ihs_value_gross",
    "CCTP-filtered value": "ihs_value_filtered",
    "CCTP value": "ihs_value_cctp",
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def compare_numeric(new: pd.DataFrame, old: pd.DataFrame, keys: list[str]) -> dict:
    left = new.set_index(keys).sort_index()
    right = old.set_index(keys).sort_index()
    assert left.index.equals(right.index)
    result = {}
    for column in ["estimate", "se", "p_value", "n"]:
        result[column] = float(np.max(np.abs(left[column] - right[column])))
        np.testing.assert_allclose(left[column], right[column], rtol=1e-9, atol=1e-11)
    return result


def write_review_tables(contrasts: pd.DataFrame, levels: list[dict], future: list[dict]) -> None:
    br = r" \\"
    def wrap(caption: str, label: str, columns: str, header: str, rows: list[str], notes: str, placement: str = "!htbp") -> str:
        return "\n".join([
            "\\begin{table}["+placement+"]", r"\centering", r"\begin{threeparttable}",
            "\\caption{"+caption+"}", "\\label{"+label+"}", r"\small",
            "\\begin{tabular}{"+columns+"}", r"\toprule", header+br, r"\midrule",
            *rows, r"\bottomrule", r"\end{tabular}", r"\begin{tablenotes}[flushleft]\footnotesize",
            "\\item \\textit{Notes:} "+notes, r"\end{tablenotes}", r"\end{threeparttable}", r"\end{table}", "",
        ])
    rows = []
    for _, row in contrasts.iterrows():
        label = row["contrast"].replace(" minus CCTP-filtered", r" $-$ filtered")
        rows.append(f"{label} & {row.estimate:.4f} & ({row.se:.4f}) & [{row.ci95_low:.4f}, {row.ci95_high:.4f}] & {row.p_value:.4f} & {row.p_holm_four_contrasts:.4f}"+br)
    (OUT / "direct_contrasts.tex").write_text(wrap(
        "Direct coefficient contrasts under CCTP filtering", "tab:contrasts", "lrrrrr",
        r"Outcome contrast & Estimate & SE & 95\% interval & $p$ & Holm $p$", rows,
        "All rows use 948 UTC days, April 28, 2023--November 30, 2025. The dependent variable is the difference between two inverse-hyperbolic-sine outcomes; values are in millions of USDC before transformation. Entries sum the coefficients on absolute ETH returns at $t-1$ and $t-2$. The controls and fixed effects are identical to Table~\\ref{tab:regressions}. Newey-West standard errors use seven lags. Intervals use 1.96 standard errors. Holm adjustment controls the family-wise error rate across the four displayed contrasts. Filtered denotes the residual after identifiable CCTP source burns are removed, not verified redemption."))
    rows = []
    for metric, title in [("count", "A. Events"), ("value_millions", "B. Millions of USDC")]:
        rows += [r"\multicolumn{5}{l}{\textit{"+title+"}}"+br]
        for row in levels:
            if row["metric"] != metric:
                continue
            label = row["outcome"].replace("minus", "$-$")
            p_text = "$<0.001$" if row["p_value"] < .001 else f"{row['p_value']:.3f}"
            rows.append(f"{label} & {row['estimate']:.3f} & ({row['se']:.3f}) & [{row['ci95_low']:.3f}, {row['ci95_high']:.3f}] & {p_text}"+br)
        if metric == "count":
            rows += [r"\midrule"]
    (OUT / "levels_additivity.tex").write_text(wrap(
        "Coefficient additivity in natural units", "tab:levels", "lrrrr",
        r"Outcome & Lag coefficient & SE & 95\% interval & $p$", rows,
        "The dependent variables are untransformed daily event counts or burn values in millions of USDC. Each estimate sums the coefficients on the two preceding daily absolute ETH returns. All rows retain the baseline 948 dates, controls, fixed effects, and Newey-West covariance estimator with seven lags. No observation is winsorized or removed. Gross minus filtered and CCTP coincide in levels by construction; their equality verifies the additive projection argument, rather than supplying two independent findings. Filtered remains an unverified residual burn category."))
    rows = []
    for row in future:
        label = row["outcome"].replace("CCTP-filtered", "Filtered")
        rows.append(f"{label} & {row['future_1']:.4f} & {row['future_2']:.4f} & {row['sum_zero_p']:.3f} & {row['joint_zero_p']:.3f}"+br)
    (OUT / "future_tests.tex").write_text(wrap(
        "Future-volatility diagnostics: sum and joint restrictions", "tab:futureplacebo", "lrrrr",
        r"Outcome & $t+1$ & $t+2$ & Sum-zero $p$ & Joint-zero $p$", rows,
        "All rows augment the IHS baseline with absolute ETH returns at $t+1$ and $t+2$ and use 947 UTC dates. Sum-zero tests the single restriction that the two future coefficients sum to zero. Joint-zero tests both coefficients equal to zero using two restrictions. Both are Wald tests with Newey-West covariance and seven lags. No test establishes causal direction; failure to reject is not evidence of equality between future and lagged patterns.", placement="H"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    protected = [
        *sorted((ROOT / "tables").glob("*.csv")),
        *sorted((ROOT / "data/processed").glob("*.parquet")),
        ROOT / "reports/regression_results.json",
    ]
    protected = [p for p in protected if not p.name.startswith("._")]
    before = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    panel = reg.build_panel()
    saved_panel = pd.read_parquet(ROOT / "data/processed/regression_daily_panel.parquet")
    pd.testing.assert_frame_equal(panel, saved_panel)
    rebuilt_main, _ = reg.main_table(panel)
    rebuilt_contrasts, _ = reg.contrast_table(panel)
    rebuilt_robustness, _ = reg.robustness_table(panel)
    rebuilt_placebo = reg.placebo_results(panel)
    reproduction = {
        "main": compare_numeric(rebuilt_main, pd.read_csv(ROOT / "tables/table_4_regression_estimates.csv"), ["outcome", "term"]),
        "contrasts": compare_numeric(rebuilt_contrasts, pd.read_csv(ROOT / "tables/table_5_coefficient_contrasts.csv"), ["contrast"]),
        "robustness": compare_numeric(rebuilt_robustness, pd.read_csv(ROOT / "tables/table_A4_regression_robustness.csv"), ["specification", "contrast"]),
        "future_sums": compare_numeric(rebuilt_placebo, pd.read_csv(ROOT / "tables/table_A5_future_volatility_placebo.csv"), ["outcome"]),
    }
    contrasts = rebuilt_contrasts.copy()
    contrasts["ci95_low"] = contrasts.estimate - 1.96 * contrasts.se
    contrasts["ci95_high"] = contrasts.estimate + 1.96 * contrasts.se
    contrasts["p_holm_four_contrasts"] = multipletests(contrasts.p_value, method="holm")[1]
    contrasts.to_csv(OUT / "direct_contrasts_intervals.csv", index=False)

    future_rows, residual_rows = [], []
    for label, col in OUTCOMES.items():
        fit = reg.fit_model(panel, panel[col], include_future=True)
        names = list(fit.params.index)
        restriction = np.zeros((2, len(names)))
        for j, name in enumerate(["eth_abs_return_pp_f1", "eth_abs_return_pp_f2"]):
            restriction[j, names.index(name)] = 1
        future_rows.append({
            "outcome": label,
            "future_1": float(fit.params.eth_abs_return_pp_f1),
            "future_2": float(fit.params.eth_abs_return_pp_f2),
            "joint_zero_p": float(fit.wald_test(restriction, scalar=True).pvalue),
            "sum_zero_p": reg.linear_combination(fit, ["eth_abs_return_pp_f1", "eth_abs_return_pp_f2"])["p_value"],
            "n": int(fit.nobs),
        })
        baseline = reg.fit_model(panel, panel[col])
        lb = acorr_ljungbox(baseline.resid, lags=[7, 30], return_df=True)
        residual_rows.append({"outcome": label, "n": int(baseline.nobs),
                              "ljung_box_7_p": float(lb.loc[7, "lb_pvalue"]),
                              "ljung_box_30_p": float(lb.loc[30, "lb_pvalue"])})
    pd.DataFrame(future_rows).to_csv(OUT / "future_sum_and_joint_tests.csv", index=False)
    pd.DataFrame(residual_rows).to_csv(OUT / "residual_serial_correlation.csv", index=False)

    level_rows, identities = [], []
    for metric, prefix, divisor in [("count", "events", 1), ("value_millions", "amount_usdc", 1_000_000)]:
        b = panel[f"{prefix}_gross_burn"] / divisor
        f = panel[f"{prefix}_other_native_burn"] / divisor
        x = panel[f"{prefix}_cctp_transport"] / divisor
        fits = {name: reg.fit_model(panel, y) for name, y in [("Gross", b), ("Filtered", f), ("CCTP", x)]}
        delta = reg.fit_model(panel, b-f)
        level_error = float(np.max(np.abs(fits["Gross"].params-fits["Filtered"].params-fits["CCTP"].params)))
        level_se_error = float(np.max(np.abs(delta.bse-fits["CCTP"].bse)))
        gb, gf, gx = np.arcsinh(b), np.arcsinh(f), np.arcsinh(x)
        fit_gb, fit_gf = reg.fit_model(panel, gb), reg.fit_model(panel, gf)
        gap_fit = reg.fit_model(panel, gb-gf)
        gap_error = float(np.max(np.abs(fit_gb.params-fit_gf.params-gap_fit.params)))
        np.testing.assert_allclose(fits["Gross"].params-fits["Filtered"].params, fits["CCTP"].params, rtol=1e-8, atol=1e-9)
        np.testing.assert_allclose(fit_gb.params-fit_gf.params, gap_fit.params, rtol=1e-8, atol=1e-9)
        identities.append({"metric": metric, "levels_parameter_identity_max_abs_error": level_error,
                           "levels_gap_cctp_se_max_abs_error": level_se_error,
                           "ihs_gap_parameter_identity_max_abs_error": gap_error,
                           "ihs_gap_not_ihs_cctp_max_abs_difference": float(np.max(np.abs(gb-gf-gx)))})
        for label, fit in {**fits, "Gross minus filtered": delta}.items():
            row = reg.linear_combination(fit, reg.VOL_TERMS[1:])
            level_rows.append({"metric": metric, "outcome": label, **row, "n": int(fit.nobs),
                               "ci95_low": row["estimate"]-1.96*row["se"],
                               "ci95_high": row["estimate"]+1.96*row["se"]})
    pd.DataFrame(level_rows).to_csv(OUT / "levels_additivity.csv", index=False)
    write_review_tables(contrasts, level_rows, future_rows)

    events = pd.read_parquet(ROOT / "data/processed/ethereum_usdc_mintburn_events.parquet", columns=["operation", "date_utc", "burn_class", "amount_micro_usdc"])
    burns = events.loc[events.operation.eq("burn")].copy()
    assert pd.api.types.is_integer_dtype(burns.amount_micro_usdc)
    by_class = burns.groupby(["date_utc", "burn_class"]).amount_micro_usdc.sum().unstack(fill_value=0)
    integer_series = {
        "gross_burn": by_class.sum(axis=1),
        "other_native_burn": by_class.other_native_burn,
        "cctp_transport": by_class.cctp_v1_transport+by_class.cctp_v2_transport,
    }
    stored = panel.set_index("date_utc")
    integer_checks = {}
    for label, raw in integer_series.items():
        raw = raw.reindex(stored.index, fill_value=0)
        difference = np.abs(raw/1_000_000 - stored[f"amount_usdc_{label}"])
        flips = sum(int(((raw >= cutoff*1_000_000) != (stored[f"amount_usdc_{label}"] >= cutoff)).sum())
                    for cutoff in [10_000_000, 25_000_000, 50_000_000, 100_000_000, 250_000_000, 500_000_000])
        assert flips == 0
        integer_checks[label] = {"max_daily_difference_usdc": float(difference.max()),
                                 "threshold_grid_classification_changes": flips,
                                 "exact_total_micro_usdc": int(raw.sum()),
                                 "exact_total_usdc": str(Decimal(int(raw.sum()))/Decimal(1_000_000))}

    iris = pd.read_csv(ROOT / "data/processed/iris_validation_sample.csv", dtype=str).fillna("")
    v2 = iris.loc[iris.burn_class.eq("cctp_v2_transport")]
    exact_matches = sum(Decimal(a)==Decimal(b) for a,b in zip(v2.amount_micro_usdc, v2.decoded_amount_micro))
    assert exact_matches == len(v2) == 250
    assert iris.http_status.isin(["200", "404"]).all()
    timing = pd.read_parquet(ROOT / "data/processed/bitstamp_usdcusd_hourly.parquet")
    assert timing.timestamp_utc.is_monotonic_increasing
    baseline_index = reg.fit_model(panel, panel.ihs_events_gross).model.data.row_labels
    baseline = panel.loc[baseline_index]
    after = {str(p.relative_to(ROOT)): sha(p) for p in protected}
    assert before == after
    summary = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Review diagnostics, not causal identification or editorial acceptance.",
        "historical_data_and_result_files_unchanged": before == after,
        "protected_hashes": before, "reproduction_max_abs_errors": reproduction,
        "projection_identities": identities, "integer_aggregation_audit": integer_checks,
        "v2_decimal_amount_matches": exact_matches,
        "v2_largest_micro_amount": str(max(Decimal(a) for a in v2.amount_micro_usdc)),
        "bitstamp_hourly_monotone": True,
        "baseline_n": len(baseline), "baseline_start": str(baseline.date.min()), "baseline_end": str(baseline.date.max()),
        "absolute_eth_return_pp_mean": float(baseline.eth_abs_return_pp_t.mean()),
        "absolute_eth_return_pp_sd": float(baseline.eth_abs_return_pp_t.std()),
        "absolute_eth_return_pp_p25": float(baseline.eth_abs_return_pp_t.quantile(.25)),
        "absolute_eth_return_pp_p75": float(baseline.eth_abs_return_pp_t.quantile(.75)),
        "baseline_zero_residual_count_days": int(baseline.events_other_native_burn.eq(0).sum()),
    }
    (OUT / "audit_summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print("Historical results reproduced; protected files unchanged.")
    print(contrasts[["contrast", "estimate", "ci95_low", "ci95_high", "p_holm_four_contrasts"]].to_string(index=False))
    print(pd.DataFrame(level_rows).to_string(index=False))
    print(pd.DataFrame(future_rows).to_string(index=False))
    print(json.dumps(integer_checks, indent=2))


if __name__ == "__main__":
    main()
