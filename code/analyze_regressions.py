from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/processed"
TABLES = ROOT / "tables"
REPORTS = ROOT / "reports"
VOL_TERMS = ["eth_abs_return_pp_t", "eth_abs_return_pp_l1", "eth_abs_return_pp_l2"]
BASE_CONTROLS = [
    "log_average_fee_usd",
    "log_eth_transaction_count",
    "log_bitstamp_usdcusd_volume",
    "usdc_discount_bps",
]
LATEX_BREAK = r" \\"


def build_panel() -> pd.DataFrame:
    burns = pd.read_parquet(DATA / "daily_burn_decomposition.parquet").copy()
    burns["date"] = pd.to_datetime(burns["date_utc"])

    eth = pd.read_parquet(DATA / "coinmetrics_eth_daily.parquet").copy()
    eth["date"] = pd.to_datetime(eth["date_utc"])
    eth = eth.sort_values("date")
    eth["eth_log_return"] = np.log(eth["PriceUSD"]).diff()
    eth["eth_abs_return_pp_t"] = 100 * eth["eth_log_return"].abs()
    eth["eth_abs_return_pp_l1"] = eth["eth_abs_return_pp_t"].shift(1)
    eth["eth_abs_return_pp_l2"] = eth["eth_abs_return_pp_t"].shift(2)
    eth["eth_abs_return_pp_f1"] = eth["eth_abs_return_pp_t"].shift(-1)
    eth["eth_abs_return_pp_f2"] = eth["eth_abs_return_pp_t"].shift(-2)
    eth["log_average_fee_usd"] = np.log(eth["average_fee_usd"])
    eth["log_eth_transaction_count"] = np.log(eth["TxCnt"])

    market = pd.read_parquet(DATA / "bitstamp_usdcusd_hourly.parquet").copy()
    market["date"] = market["timestamp_utc"].dt.tz_localize(None).dt.floor("D")
    daily_market = market.groupby("date", as_index=False).agg(
        bitstamp_usdcusd_close=("close", "last"),
        bitstamp_usdcusd_low=("low", "min"),
        bitstamp_usdcusd_volume=("volume", "sum"),
    )
    daily_market["usdc_discount_bps"] = 10_000 * (
        1 - daily_market["bitstamp_usdcusd_close"]
    )
    daily_market["usdc_downside_bps"] = 10_000 * np.maximum(
        0, 1 - daily_market["bitstamp_usdcusd_low"]
    )
    daily_market["log_bitstamp_usdcusd_volume"] = np.log1p(
        daily_market["bitstamp_usdcusd_volume"]
    )

    keep_eth = [
        "date",
        "PriceUSD",
        "eth_log_return",
        "eth_abs_return_pp_t",
        "eth_abs_return_pp_l1",
        "eth_abs_return_pp_l2",
        "eth_abs_return_pp_f1",
        "eth_abs_return_pp_f2",
        "average_fee_usd",
        "log_average_fee_usd",
        "TxCnt",
        "log_eth_transaction_count",
        "AdrActCnt",
    ]
    panel = burns.merge(eth[keep_eth], on="date", how="left", validate="one_to_one")
    panel = panel.merge(daily_market, on="date", how="left", validate="one_to_one")
    panel["year_month"] = panel["date"].dt.to_period("M").astype(str)
    panel["day_of_week"] = panel["date"].dt.dayofweek
    panel["linear_trend"] = np.arange(len(panel), dtype=float)
    panel["ihs_events_gross"] = np.arcsinh(panel["events_gross_burn"])
    panel["ihs_events_filtered"] = np.arcsinh(panel["events_other_native_burn"])
    panel["ihs_events_cctp"] = np.arcsinh(panel["events_cctp_transport"])
    panel["ihs_value_gross"] = np.arcsinh(panel["amount_usdc_gross_burn"] / 1_000_000)
    panel["ihs_value_filtered"] = np.arcsinh(
        panel["amount_usdc_other_native_burn"] / 1_000_000
    )
    panel["ihs_value_cctp"] = np.arcsinh(
        panel["amount_usdc_cctp_transport"] / 1_000_000
    )
    panel["log1p_events_gross"] = np.log1p(panel["events_gross_burn"])
    panel["log1p_events_filtered"] = np.log1p(panel["events_other_native_burn"])
    panel["log1p_events_cctp"] = np.log1p(panel["events_cctp_transport"])
    panel["log1p_value_gross"] = np.log1p(panel["amount_usdc_gross_burn"] / 1_000_000)
    panel["log1p_value_filtered"] = np.log1p(
        panel["amount_usdc_other_native_burn"] / 1_000_000
    )
    panel["log1p_value_cctp"] = np.log1p(
        panel["amount_usdc_cctp_transport"] / 1_000_000
    )
    return panel


def design_matrix(frame: pd.DataFrame, include_future: bool = False) -> pd.DataFrame:
    variables = VOL_TERMS + BASE_CONTROLS
    if include_future:
        variables += ["eth_abs_return_pp_f1", "eth_abs_return_pp_f2"]
    matrix = frame[variables].copy()
    matrix = pd.concat(
        [
            matrix,
            pd.get_dummies(frame["year_month"], prefix="month", drop_first=True, dtype=float),
            pd.get_dummies(frame["day_of_week"], prefix="dow", drop_first=True, dtype=float),
        ],
        axis=1,
    )
    return sm.add_constant(matrix).astype(float)


def fit_model(
    frame: pd.DataFrame,
    outcome: pd.Series,
    hac_lags: int = 7,
    include_future: bool = False,
) -> sm.regression.linear_model.RegressionResultsWrapper:
    needed = VOL_TERMS + BASE_CONTROLS + ["year_month", "day_of_week"]
    if include_future:
        needed += ["eth_abs_return_pp_f1", "eth_abs_return_pp_f2"]
    work = frame[needed].copy()
    work["outcome"] = outcome
    work = work.dropna()
    matrix = design_matrix(work, include_future=include_future)
    return sm.OLS(work["outcome"].astype(float), matrix).fit(
        cov_type="HAC", cov_kwds={"maxlags": hac_lags}
    )


def linear_combination(fit, terms: list[str]) -> dict:
    restriction = np.zeros((1, len(fit.params)))
    parameter_names = list(fit.params.index)
    for term in terms:
        restriction[0, parameter_names.index(term)] = 1
    estimate = float(sum(fit.params[term] for term in terms))
    variance = float((restriction @ fit.cov_params().to_numpy() @ restriction.T).item())
    standard_error = variance ** 0.5
    p_value = float(fit.wald_test(restriction, scalar=True).pvalue)
    return {"estimate": estimate, "se": standard_error, "p_value": p_value}


def stars(p_value: float) -> str:
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def cell(estimate: float, p_value: float) -> str:
    return f"{estimate:.4f}{stars(p_value)}"


def main_table(panel: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    outcomes = {
        "Gross count": "ihs_events_gross",
        "CCTP-filtered count": "ihs_events_filtered",
        "CCTP count": "ihs_events_cctp",
        "Gross value": "ihs_value_gross",
        "CCTP-filtered value": "ihs_value_filtered",
        "CCTP value": "ihs_value_cctp",
    }
    estimates: list[dict] = []
    fitted = {}
    for label, column in outcomes.items():
        fit = fit_model(panel, panel[column])
        fitted[label] = fit
        for term in VOL_TERMS:
            estimates.append(
                {
                    "outcome": label,
                    "term": term,
                    "estimate": float(fit.params[term]),
                    "se": float(fit.bse[term]),
                    "p_value": float(fit.pvalues[term]),
                    "n": int(fit.nobs),
                    "adjusted_r2": float(fit.rsquared_adj),
                }
            )
        lag_sum = linear_combination(fit, VOL_TERMS[1:])
        estimates.append(
            {
                "outcome": label,
                "term": "cumulative_lag_1_2",
                **lag_sum,
                "n": int(fit.nobs),
                "adjusted_r2": float(fit.rsquared_adj),
            }
        )

    table = pd.DataFrame(estimates)
    lines = [
        "\\begin{table}[!htbp]",
        "\\centering",
        "\\begin{threeparttable}",
        "\\caption{Distributed-lag coefficients across alternative burn outcomes}",
        "\\label{tab:regressions}",
        "\\scriptsize",
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "& \\multicolumn{3}{c}{Burn event count} & \\multicolumn{3}{c}{Burn value}" + LATEX_BREAK,
        "\\cmidrule(lr){2-4} \\cmidrule(lr){5-7}",
        "& Gross & CCTP-filtered & CCTP & Gross & CCTP-filtered & CCTP" + LATEX_BREAK,
        "\\midrule",
    ]
    row_labels = [
        ("eth_abs_return_pp_t", "ETH volatility, $t$"),
        ("eth_abs_return_pp_l1", "ETH volatility, $t-1$"),
        ("eth_abs_return_pp_l2", "ETH volatility, $t-2$"),
        ("cumulative_lag_1_2", "Cumulative lag, $t-1$ to $t-2$"),
    ]
    for term, row_label in row_labels:
        cells = []
        ses = []
        for label in outcomes:
            row = table[(table["outcome"] == label) & (table["term"] == term)].iloc[0]
            cells.append(cell(row["estimate"], row["p_value"]))
            ses.append(f"({row['se']:.4f})")
        lines.append(row_label + " & " + " & ".join(cells) + LATEX_BREAK)
        lines.append(" & " + " & ".join(ses) + LATEX_BREAK)
    first_fit = next(iter(fitted.values()))
    lines += [
        "\\midrule",
        "Year-month fixed effects & Yes & Yes & Yes & Yes & Yes & Yes" + LATEX_BREAK,
        "Day-of-week fixed effects & Yes & Yes & Yes & Yes & Yes & Yes" + LATEX_BREAK,
        "Market and network controls & Yes & Yes & Yes & Yes & Yes & Yes" + LATEX_BREAK,
        "Observations & " + " & ".join(str(int(fitted[label].nobs)) for label in outcomes) + LATEX_BREAK,
        "Adjusted $R^2$ & " + " & ".join(f"{fitted[label].rsquared_adj:.3f}" for label in outcomes) + LATEX_BREAK,
        "\\bottomrule",
        "\\end{tabular}",
        "\\begin{tablenotes}[flushleft]\\footnotesize",
        "\\item \\textit{Notes:} The sample is daily from April 28, 2023, through November 30, 2025. Outcomes are inverse-hyperbolic-sine event counts or burn value in millions of USDC. CCTP-filtered means gross burns minus burns sent from official CCTP TokenMinter addresses; it is a residual burn measure, not verified fiat redemption. Absolute ETH returns are in percentage points. Controls include the contemporaneous USDC/USD close discount, log Bitstamp USDC/USD volume, log average Ethereum transaction fee in dollars, and log Ethereum transaction count. Standard errors in parentheses are Newey-West with seven lags. The cumulative row sums the coefficients on days $t-1$ and $t-2$. $^{***}p<0.01$, $^{**}p<0.05$, $^{*}p<0.10$.",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ]
    return table, "\n".join(lines) + "\n"


def contrast_table(panel: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    contrasts = {
        "Gross minus CCTP-filtered count": panel["ihs_events_gross"] - panel["ihs_events_filtered"],
        "CCTP minus CCTP-filtered count": panel["ihs_events_cctp"] - panel["ihs_events_filtered"],
        "Gross minus CCTP-filtered value": panel["ihs_value_gross"] - panel["ihs_value_filtered"],
        "CCTP minus CCTP-filtered value": panel["ihs_value_cctp"] - panel["ihs_value_filtered"],
    }
    rows = []
    for label, outcome in contrasts.items():
        fit = fit_model(panel, outcome)
        lag_sum = linear_combination(fit, VOL_TERMS[1:])
        rows.append(
            {
                "contrast": label,
                **lag_sum,
                "n": int(fit.nobs),
                "adjusted_r2": float(fit.rsquared_adj),
            }
        )
    table = pd.DataFrame(rows)
    lines = [
        "\\begin{table}[!htbp]",
        "\\centering",
        "\\begin{threeparttable}",
        "\\caption{Tests of coefficient differences across burn measures}",
        "\\label{tab:contrasts}",
        "\\small",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Outcome contrast & Lag coefficient & SE & $p$-value & $N$" + LATEX_BREAK,
        "\\midrule",
    ]
    for _, row in table.iterrows():
        display_label = str(row["contrast"]).replace(" minus CCTP-filtered", " $-$ residual")
        lines.append(
            f"{display_label} & {cell(row['estimate'], row['p_value'])} & "
            f"({row['se']:.4f}) & {row['p_value']:.3f} & {int(row['n'])}" + LATEX_BREAK
        )
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\begin{tablenotes}[flushleft]\\footnotesize",
        "\\item \\textit{Notes:} Residual denotes the CCTP-filtered residual burn measure. Each row estimates the baseline specification using the difference between two transformed outcomes as the dependent variable. The reported coefficient sums the loadings on absolute ETH returns at $t-1$ and $t-2$. With a common regressor set, this is the direct test of whether outcome construction changes the corresponding cumulative coefficient in Table~\\ref{tab:regressions}. Newey-West standard errors use seven lags. Significance levels are defined in Table~\\ref{tab:regressions}.",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ]
    return table, "\n".join(lines) + "\n"


def robustness_table(panel: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    specifications = [
        ("Baseline, NW(7)", panel.copy(), 7, "ihs"),
        ("NW(14)", panel.copy(), 14, "ihs"),
        ("NW(30)", panel.copy(), 30, "ihs"),
        (
            "Drop top 1\\% volatility",
            panel[panel["eth_abs_return_pp_t"] <= panel["eth_abs_return_pp_t"].quantile(0.99)].copy(),
            7,
            "ihs",
        ),
        ("2024 onward", panel[panel["date"] >= "2024-01-01"].copy(), 7, "ihs"),
        ("Log(1+$y$)", panel.copy(), 7, "log1p"),
    ]
    rows = []
    for label, sample, hac_lags, transform in specifications:
        prefix = "ihs" if transform == "ihs" else "log1p"
        contrast_outcomes = {
            "Gross-CCTP-filtered count": sample[f"{prefix}_events_gross"]
            - sample[f"{prefix}_events_filtered"],
            "CCTP-CCTP-filtered count": sample[f"{prefix}_events_cctp"]
            - sample[f"{prefix}_events_filtered"],
            "CCTP-CCTP-filtered value": sample[f"{prefix}_value_cctp"]
            - sample[f"{prefix}_value_filtered"],
        }
        for contrast, outcome in contrast_outcomes.items():
            fit = fit_model(sample, outcome, hac_lags=hac_lags)
            lag_sum = linear_combination(fit, VOL_TERMS[1:])
            rows.append(
                {
                    "specification": label,
                    "contrast": contrast,
                    **lag_sum,
                    "n": int(fit.nobs),
                }
            )
    table = pd.DataFrame(rows)
    column_order = ["Gross-CCTP-filtered count", "CCTP-CCTP-filtered count", "CCTP-CCTP-filtered value"]
    lines = [
        "\\begin{table}[!htbp]",
        "\\centering",
        "\\begin{threeparttable}",
        "\\caption{Robustness of cumulative coefficient contrasts}",
        "\\label{tab:regrobust}",
        "\\begin{tabular}{lrrr}",
        "\\toprule",
        "& Gross-residual count & CCTP-residual count & CCTP-residual value" + LATEX_BREAK,
        "\\midrule",
    ]
    for label, _, _, _ in specifications:
        values = []
        ses = []
        for contrast in column_order:
            row = table[(table["specification"] == label) & (table["contrast"] == contrast)].iloc[0]
            values.append(cell(row["estimate"], row["p_value"]))
            ses.append(f"({row['se']:.4f})")
        lines.append(label + " & " + " & ".join(values) + LATEX_BREAK)
        lines.append(" & " + " & ".join(ses) + LATEX_BREAK)
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\begin{tablenotes}[flushleft]\\footnotesize",
        "\\item \\textit{Notes:} Residual denotes the CCTP-filtered residual burn measure. Entries are cumulative day-$t-1$ and day-$t-2$ ETH-volatility coefficient contrasts. Unless stated otherwise, specifications use inverse-hyperbolic-sine outcomes, the baseline controls and fixed effects, and Newey-West standard errors with seven lags. Significance levels are defined in Table~\\ref{tab:regressions}.",
        "\\end{tablenotes}",
        "\\end{threeparttable}",
        "\\end{table}",
    ]
    return table, "\n".join(lines) + "\n"


def placebo_results(panel: pd.DataFrame) -> pd.DataFrame:
    outcomes = {
        "Gross count": panel["ihs_events_gross"],
        "CCTP-filtered count": panel["ihs_events_filtered"],
        "CCTP count": panel["ihs_events_cctp"],
        "Gross value": panel["ihs_value_gross"],
        "CCTP-filtered value": panel["ihs_value_filtered"],
        "CCTP value": panel["ihs_value_cctp"],
    }
    rows = []
    for label, outcome in outcomes.items():
        fit = fit_model(panel, outcome, include_future=True)
        future_sum = linear_combination(fit, ["eth_abs_return_pp_f1", "eth_abs_return_pp_f2"])
        rows.append({"outcome": label, **future_sum, "n": int(fit.nobs)})
    return pd.DataFrame(rows)


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    panel = build_panel()
    panel.to_parquet(DATA / "regression_daily_panel.parquet", index=False)
    panel.to_csv(DATA / "regression_daily_panel.csv", index=False)

    main_results, main_tex = main_table(panel)
    contrasts, contrasts_tex = contrast_table(panel)
    robustness, robustness_tex = robustness_table(panel)
    placebo = placebo_results(panel)

    main_results.to_csv(TABLES / "table_4_regression_estimates.csv", index=False)
    contrasts.to_csv(TABLES / "table_5_coefficient_contrasts.csv", index=False)
    robustness.to_csv(TABLES / "table_A4_regression_robustness.csv", index=False)
    placebo.to_csv(TABLES / "table_A5_future_volatility_placebo.csv", index=False)
    (TABLES / "table_4_regression_estimates.tex").write_text(main_tex, encoding="utf-8")
    (TABLES / "table_5_coefficient_contrasts.tex").write_text(contrasts_tex, encoding="utf-8")
    (TABLES / "table_A4_regression_robustness.tex").write_text(robustness_tex, encoding="utf-8")

    summary = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel_rows": len(panel),
        "panel_start": panel["date"].min().date().isoformat(),
        "panel_end": panel["date"].max().date().isoformat(),
        "baseline_n": int(main_results["n"].iloc[0]),
        "main_results": main_results.to_dict(orient="records"),
        "coefficient_contrasts": contrasts.to_dict(orient="records"),
        "placebo_future_volatility": placebo.to_dict(orient="records"),
    }
    (REPORTS / "regression_results.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(contrasts.to_string(index=False))
    print("\nRobustness:\n" + robustness.to_string(index=False))
    print("\nFuture-volatility placebo:\n" + placebo.to_string(index=False))


if __name__ == "__main__":
    main()
