"""Compare fixed manuscript values with enclosed evidence; fail on any mismatch."""
from pathlib import Path
import importlib.util
import importlib.metadata
import hashlib
import json
import math
import sys
import time
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))
from common import read

EXPECTED_A = [
    ['10.91', '12.18', '14.86'], ['10.70', '10.58', '1.88'], ['113', '1', '10'],
    ['11.79', '11.91', '11.35'], ['10.43', '3.13', '0.64'], ['262', '29', '8'],
    ['0 (11)', '1 (0)', '1 (24)'], ['3 (0)', '91 (0)', '61 (0)'],
]
EXPECTED_B = [
    ['313', '15'], ['0.00', '128.02'], ['89.07', '15.03'], ['7', '170'],
    ['99.98', '93.25'], ['88.03', '87.30'], ['11.70', '10.00'],
]


def main():
    begin = time.perf_counter()
    rows = []
    def check(label, paper, reproduced, digits=None, reason=''):
        if digits is None:
            ok = str(paper) == str(reproduced)
            delta = ''
            shown = str(reproduced)
        else:
            shown = f'{float(reproduced):.{digits}f}'
            ok = shown == f'{float(paper):.{digits}f}'
            delta = float(reproduced)-float(paper)
        rows.append(dict(item=label, paper=paper, reproduced=shown, consistent=ok,
                         raw_difference=delta, reason=reason if reason else 'same stated rounding' if digits is not None else 'exact match'))

    a = pd.read_csv(ROOT / 'output/Table_C1_Panel_A.csv', dtype=str)
    b = pd.read_csv(ROOT / 'output/Table_C1_Panel_B.csv', dtype=str)
    for i, expected in enumerate(EXPECTED_A):
        for j, paper in enumerate(expected):
            check(f'C1 A row {i+1} {a.columns[j+1]}', paper, a.iloc[i, j+1])
    for i, expected in enumerate(EXPECTED_B):
        for j, paper in enumerate(expected):
            check(f'C1 B row {i+1} {b.columns[j+1]}', paper, b.iloc[i, j+1])

    daily = read('base_daily.csv').sort_values('date')
    h = read('hourly_eth_arb_base.csv')
    e = read('error_calls_windows.csv')
    r = read('refill_daily.csv')
    order = read('refill_order_check.csv')
    # Numerical identities use S/J/assets, rather than trusting precomputed ratios.
    check('439 daily states', 439, len(daily), 0)
    check('3 chains x 1008 hourly states', 3024, len(h), 0)
    check('unique chain-hour keys', 0, int(h.duplicated(['chain', 'utc']).sum()), 0)
    check('daily Dup identity max error <1e-12', True, bool(np.abs(daily.Dup-(daily.S-daily.J)/daily.S).max()<1e-12))
    check('hourly JA identity max error <1e-12', True, bool(np.abs(h.JA-h.J/h.assets).max()<1e-12))
    check('hourly Dup identity max error <1e-12', True, bool(np.abs(h.Dup-(h.S-h.J)/h.S).dropna().max()<1e-12))
    # Independently reconstruct all 24 Panel A cells from hourly rows / events.
    independent_a = [['']*3 for _ in range(8)]
    for j, c in enumerate([8453, 1, 42161]):
        g = h[h.chain.eq(c)].sort_values('utc')
        t = pd.to_datetime(g.utc, utc=True)
        for offset, w, lo, hi in [(0, 'W1', '2025-10-09', '2025-10-18'), (3, 'W2', '2025-11-03', '2025-11-22')]:
            start, end = pd.Timestamp(lo, tz='UTC'), pd.Timestamp(hi, tz='UTC')
            pre = g[(t>=start-pd.Timedelta(days=7)) & (t<start)]
            event = g[(t>=start) & (t<end)].copy()
            baseline = (pre.J/pre.assets).median()
            ratio = event.J/event.assets
            minimum = event.loc[ratio.idxmin()]
            later = event[event.timestamp.ge(minimum.timestamp) & (event.J/event.assets).ge(baseline)]
            recovery = (int(later.timestamp.iloc[0])-int(minimum.timestamp))/3600
            independent_a[offset][j] = f'{baseline*100:.2f}'
            independent_a[offset+1][j] = f'{ratio.min()*100:.2f}'
            independent_a[offset+2][j] = f'{recovery:.0f}'
            event_count = len(e[e.chain.eq(c) & e[w].eq(1)])
            comparison_count = len(e[e.chain.eq(c) & e[w+'_control'].eq(1)])
            independent_a[6+(w=='W2')][j] = f'{event_count} ({comparison_count})'
    check('C1 A independently recomputed cells', True, independent_a == EXPECTED_A)
    independent_b = []
    for f in [10, 25]:
        g = r[r.f.eq(f)]
        complete = g[~g.censored]
        total_flows = complete.supply_inflow_micro.sum()+complete.repay_inflow_micro.sum()+complete.liquidation_inflow_micro.sum()
        values = [f'{g.tau.eq(0).sum():.0f}', f'{g.tau.median():.2f}', f'{100*g.tau.le(24).mean():.2f}',
                  f'{g.censored.sum():.0f}', f'{100*g.loc[g.censored,"paid_fraction"].median():.2f}',
                  f'{100*complete.supply_inflow_micro.sum()/total_flows:.2f}',
                  f'{100*complete.repay_inflow_micro.sum()/total_flows:.2f}']
        independent_b.append(values)
    check('C1 B independently recomputed cells', True, list(map(list, zip(*independent_b)))==EXPECTED_B)

    for f, zero, median, within, censored, paid, supply, repay in [
        (10,313,0.,89,7,100,88,12), (25,15,128.02,15,170,93,87,10)]:
        g = r[r.f.eq(f)]
        check(f'Body {f}% immediate-payment dates', zero, g.tau.eq(0).sum(), 0)
        check(f'Body {f}% median hours', median, g.tau.median(), 2)
        check(f'Body {f}% within24 rounded percent', within, 100*g.tau.le(24).mean(), 0)
        check(f'Body {f}% censored dates', censored, g.censored.sum(), 0)
        check(f'Body {f}% censored share paid rounded percent', paid, 100*g.loc[g.censored,'paid_fraction'].median(), 0)
        complete = g[~g.censored]
        flows = complete[['supply_inflow_micro','repay_inflow_micro','liquidation_inflow_micro']].sum()
        check(f'Body {f}% completing supply share rounded percent', supply, 100*flows.iloc[0]/flows.sum(), 0)
        check(f'Body {f}% completing repay share rounded percent', repay, 100*flows.iloc[1]/flows.sum(), 0)
    for c, events, share, wait in [(1,91,93.41,.18),(42161,61,100.,.29)]:
        g = e[e.chain.eq(c) & e.W2.eq(1)]
        check(f'Body W2 {c} events', events, len(g), 0)
        check(f'Body W2 {c} later-withdrawal percent', share, 100*g.resolved.mean(), 2)
        check(f'Body W2 {c} later-withdrawal rounded percent', round(share), 100*g.resolved.mean(), 0)
        check(f'Body W2 {c} median wait hours', wait, g.loc[g.resolved,'wait_hours'].median(), 2)
    # Hourly narrative numbers are explicitly cross-referenced to the independent cells.
    for label, row, col, paper in [('ETH November pre',3,1,11.91),('ETH November min',4,1,3.13),
                                  ('ARB November pre',3,2,11.35),('ARB November min',4,2,.64),
                                  ('ARB October pre',0,2,14.86),('ARB October min',1,2,1.88),
                                  ('ETH November recovery',5,1,29),('ARB November recovery',5,2,8)]:
        check('Body '+label, paper, float(independent_a[row][col]), 0 if 'recovery' in label else 2)
    reg = pd.read_csv(ROOT / 'output/body_regressions.csv')
    def coefficient(model, term, col):
        return float(reg.loc[reg.model.eq(model)&reg.term.eq(term),col].iloc[0])
    for term, coef4, points, tval in [('W1',-.0079,-.79,-3.40),('W2',-.0307,-3.07,-2.07)]:
        check('Body JA '+term+' coefficient', coef4, coefficient('JA_calendar',term,'coef'), 4)
        check('Body JA '+term+' percentage points', points, 100*coefficient('JA_calendar',term,'coef'), 2)
        check('Body JA '+term+' t', tval, coefficient('JA_calendar',term,'statistic'), 2)
    for model, term, expected in [('OLS','Util',2.03),('OLS','Dup',1.14),('Cox_month_strata','Dup',-1.72)]:
        check('Body '+model+' '+term+' t/z', expected, coefficient(model,term,'statistic'), 2)
    medians = order[order.f.eq(25)].groupby('order').tau.median()
    check('Body largest-first median 128.02',128.02,medians['large_first'],2)
    check('Body smallest-first median 132.70',132.70,medians['small_first'],2)
    check('Body largest-first median rounded 128',128,medians['large_first'],0)
    check('Body smallest-first median rounded 133',133,medians['small_first'],0)
    check('Original Table1 median Dup percent',57.86,100*daily.Dup.median(),2)
    count = int(daily.all_pass.sum())
    excluded = int((daily.all_pass & daily.request.gt(daily.J)).sum())
    check('Original Table5 25% individual passes',81,count,0)
    check('Original Table5 25% joint exclusions',62,excluded,0)
    check('Original Table5 25% exclusion percent',76.54,100*excluded/count,2)
    primary = order[order.order.eq('large_first')]
    mismatches = primary[primary.f.eq(25)&primary.mismatch]
    check('B3 disclosed 25% mismatch days',4,len(mismatches),0)
    check('B3 5% immediate dates',404,int(primary[primary.f.eq(5)].tau_zero.sum()),0)
    march = mismatches[mismatches.date.eq('2025-03-11')].iloc[0]
    check('2025-03-11 aggregate-bound insufficiency disclosed',True,bool(march.aggregate_bound_not_sufficient))
    check('2025-03-11 max-flow less than requested',True,bool(march.max_flow_paid_micro<march.request_micro))
    resolved = e[e.resolved]
    check('Resolved events have successor blocks',True,bool(resolved.next_success_block.notna().all()))
    check('Successor blocks at/after failed block',True,bool(resolved.next_success_block.ge(resolved.block).all()))
    check('Successor waiting-time identity',True,bool(np.abs((resolved.next_success_timestamp-resolved.timestamp)/3600-resolved.wait_hours).max()<1e-8))
    check('Censor indicator and paid fraction agree',True,bool(r.censored.eq(r.paid_fraction.lt(1)).all()))
    check('Censored duration is exactly 168 hours',True,bool(r.loc[r.censored,'tau'].eq(168).all()))
    check('Zero tau equals complete initial payment',True,bool(r.tau.eq(0).eq(r.initial_paid_micro.eq(r.request_micro)).all()))

    # The README command sequence includes this checker, which also executes the example.
    spec = importlib.util.spec_from_file_location('one_day', ROOT/'code/03_replay_one_day.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    example = []
    for order_name in ['large_first','small_first']:
        for f in [10,25]:
            actual = module.replay(f,order_name,record_trace=(f==25 and order_name=='large_first'))
            example.append(actual)
            saved = order[order.date.eq(actual['date'])&order.f.eq(f)&order.order.eq(order_name)].iloc[0]
            for key in ['tau','censored','paid_fraction','initial_paid_micro','request_micro',
                        'supply_inflow_micro','repay_inflow_micro','liquidation_inflow_micro','clipped_outflow_micro']:
                value = actual[key]
                ok = math.isclose(float(value),float(saved[key]),rel_tol=0,abs_tol=1e-12) if key in ['tau','paid_fraction'] else value==saved[key]
                check(f'Single-day {order_name} {f}% {key}',True,bool(ok),reason=f'saved={saved[key]}; replay={value}')
    pd.DataFrame(example).to_csv(ROOT/'output/replay_example_summary.csv',index=False)
    manifest = pd.read_csv(ROOT/'check/source_manifest.csv')
    for row in manifest.itertuples():
        p = ROOT/'data'/row.file
        check('CSV hash '+row.file, row.sha256, hashlib.sha256(p.read_bytes()).hexdigest())
        check('CSV rows '+row.file, row.rows, len(pd.read_csv(p)),0)
    # Requirements are taken from actually installed versions, never inferred.
    for line in (ROOT/'requirements.txt').read_text().splitlines():
        if not line.strip():
            continue
        name, version = line.split('==')
        check('Dependency '+name,version,importlib.metadata.version(name))
    frame = pd.DataFrame(rows)
    frame.to_csv(ROOT/'check/check_results.csv',index=False)
    failed = int((~frame.consistent).sum())
    lines = ['CHECK REPORT', '论文值 / 复现值 / 是否一致',
             'Fixed manuscript values come from the author-supplied final Table C1 mapping.',
             '38 table cells include the parenthesized comparison counts in six Panel A cells.',
             'Rounded agreement is assessed at the manuscript precision; raw differences are in check_results.csv.', '']
    for row in rows:
        lines.append(f'{row["item"]}: {row["paper"]} / {row["reproduced"]} / {"PASS" if row["consistent"] else "FAIL"}; {row["reason"]}')
    lines += ['', 'B3 explanation: four 25% dates differ from individual-pass plus aggregate-bound feasibility. Three reflect vault order; 2025-03-11 remains infeasible under any allocation. This is retained under the author-approved B1 rule.',
              'Cox note: year-month-stratified Efron model; chronological HAC7, z inference.',
              f'Table C1 Panel A cells: 24; Panel B cells: 14.',
              f'Total checks: {len(rows)}',f'Passed: {len(rows)-failed}',f'Failed: {failed}',
              f'Elapsed seconds: {time.perf_counter()-begin:.2f}',
              'PACKAGE GATE: '+('PASS — all listed manuscript values reproduced.' if failed==0 else 'FAIL — packaging withheld; do not change manuscript targets to fit outputs.')]
    (ROOT/'check/check_report.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines[-10:]))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
