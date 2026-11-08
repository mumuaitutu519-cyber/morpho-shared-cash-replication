"""Rebuild Table C1 and all cited estimates from the enclosed CSV tables."""
import time
import numpy as np
import pandas as pd
from common import (OUT, read, calendar, hourly_statistics, error_statistics,
                    refill_statistics, hac_fit, cox_hac, unaffected_regressions)


def main():
    begin = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    h = hourly_statistics(read('hourly_eth_arb_base.csv')).set_index(['chain', 'window'])
    e = error_statistics(read('error_calls_windows.csv')).set_index(['chain', 'period'])
    r = refill_statistics(read('refill_daily.csv')).set_index('f')
    records = []
    for window, label in [('W1', 'October'), ('W2', 'November')]:
        for key, title, multiplier, digits in [
            ('baseline_JA', f'Bound before {label} window (%)', 100, 2),
            ('min_JA', f'Minimum, {label} window (%)', 100, 2),
            ('recovery_hours', f'Hours to recover, {label}', 1, 0),
        ]:
            records.append([title] + [f'{h.loc[(c, window), key] * multiplier:.{digits}f}' for c in [8453, 1, 42161]])
    for window, label in [('W1', 'October'), ('W2', 'November')]:
        records.append([f'Error calls, {label} (comparison)'] +
                       [f'{int(e.loc[(c, window), "events"])} ({int(e.loc[(c, window+"_control"), "events"])})' for c in [8453, 1, 42161]])
    panel_a = pd.DataFrame(records, columns=['Variable', 'Base', 'Ethereum', 'Arbitrum'])
    records = []
    for key, title, multiplier, digits in [
        ('zero', 'Paid at the closing block (dates)', 1, 0),
        ('median_tau', 'Median hours to full payment', 1, 2),
        ('within24', 'Paid within 24 hours (%)', 100, 2),
        ('censored', 'Not fully paid after 168 hours (dates)', 1, 0),
        ('censored_paid_fraction', 'Median share paid after 168 hours (%)', 100, 2),
        ('supply_share', 'New supply in completing inflows (%)', 100, 2),
        ('repay_share', 'Repayments in completing inflows (%)', 100, 2),
    ]:
        records.append([title] + [f'{r.loc[f, key] * multiplier:.{digits}f}' for f in [10, 25]])
    panel_b = pd.DataFrame(records, columns=['Variable', '10% request', '25% request'])
    panel_a.to_csv(OUT / 'Table_C1_Panel_A.csv', index=False)
    panel_b.to_csv(OUT / 'Table_C1_Panel_B.csv', index=False)
    # Plain Markdown needs no optional tabulate dependency.
    def md(table):
        return '| ' + ' | '.join(table.columns) + ' |\n| ' + ' | '.join(['---'] * len(table.columns)) + ' |\n' + '\n'.join('| ' + ' | '.join(map(str, row)) + ' |' for row in table.itertuples(index=False, name=None))
    notes = ('Panel A: preceding seven-day median JA, window minimum, hours from that minimum to the first observed recovery, and strict-equity error events. Comparisons are prior 30 days excluding the other window (30/21 days). '
             'Panel B: ten Base vaults, 439 dates; largest assets paid first. Seven-day paid shares are conditional on censoring. Inflow shares sum recorded external inflows over completed runs only. '
             'Original closing positions and queues stay fixed. Follow-up success in error statistics is a later committed withdrawal, not proof of full payment of the failed amount.')
    (OUT / 'Table_C1.md').write_text('# Table C1 Stress windows and cash refill\n\nPanel A\n\n' + md(panel_a) + '\n\nPanel B\n\n' + md(panel_b) + '\n\nNotes. ' + notes + '\n', encoding='utf-8')
    h.reset_index().to_csv(OUT / 'hourly_summary.csv', index=False)
    e.reset_index().to_csv(OUT / 'error_summary.csv', index=False)
    r.reset_index().to_csv(OUT / 'refill_summary.csv', index=False)
    base = calendar(read('base_daily.csv')).sort_values('date').reset_index(drop=True)
    rows = []
    fit = hac_fit('JA ~ W1 + W2 + C(weekday) + C(month)', base)
    for term in ['W1', 'W2']:
        rows.append(dict(model='JA_calendar', term=term, coef=fit.params[term], se=fit.bse[term],
                         statistic=fit.tvalues[term], p=fit.pvalues[term], N=int(fit.nobs)))
    refill = read('refill_daily.csv')
    b = refill[refill.f.eq(25)].merge(base[['date', 'Dup', 'Util', 'assets', 'weekday', 'month', 'W1', 'W2']], on='date', validate='one_to_one').sort_values('date').reset_index(drop=True)
    b['log_tau'] = np.log1p(b.tau)
    b['log_assets'] = np.log(b.assets / 1e6)
    for model, extra in [('OLS', ''), ('OLS_windows', ' + W1 + W2')]:
        fit = hac_fit('log_tau ~ Dup + Util + log_assets + C(month) + C(weekday)' + extra, b)
        for term in ['Dup', 'Util', 'log_assets'] + (['W1', 'W2'] if extra else []):
            rows.append(dict(model=model, term=term, coef=fit.params[term], se=fit.bse[term],
                             statistic=fit.tvalues[term], p=fit.pvalues[term], N=int(fit.nobs)))
    regressions = pd.concat([pd.DataFrame(rows), cox_hac(b)], ignore_index=True)
    regressions.to_csv(OUT / 'body_regressions.csv', index=False)
    unaffected_regressions(read('a4_unaffected_panel.csv')).to_csv(OUT / 'unaffected_regressions.csv', index=False)
    (OUT / 'regression_notes.txt').write_text(
        'OLS: seven-lag Newey-West covariance, finite-sample correction, t inference. '
        'Cox: year-month strata and weekday effects; exact Efron scores with chronological seven-lag HAC; statistic is z. '
        'The unstratified calendar-dummy Cox fit separates because September 2025 has 30 censored dates and no completions. '
        'Zero durations enter Cox at a shared 0.000001 hour. A negative Cox coefficient means lower completion hazard. '
        'Unaffected-vault models absorb vault/hour effects and cluster by vault with absorbed-rank CR1 correction.\n', encoding='utf-8')
    print(f'Table C1 and cited regressions rebuilt in {time.perf_counter()-begin:.2f} seconds.')


if __name__ == '__main__':
    main()
