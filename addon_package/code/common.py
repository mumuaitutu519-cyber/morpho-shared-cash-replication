"""Shared definitions. All runtime inputs live inside this package."""
from pathlib import Path
import math
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from lifelines import CoxPHFitter

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'output'
WINDOWS = {'W1': ('2025-10-09', '2025-10-18'), 'W2': ('2025-11-03', '2025-11-22')}
CHAINS = {8453: 'Base', 1: 'Ethereum', 42161: 'Arbitrum'}


def read(name):
    return pd.read_csv(DATA / name, float_precision='round_trip')


def calendar(d):
    d = d.copy()
    date = pd.to_datetime(d.date)
    d['weekday'] = date.dt.dayofweek
    d['month'] = date.dt.strftime('%Y-%m')
    for name, (start, end) in WINDOWS.items():
        d[name] = ((date >= start) & (date < end)).astype(int)
    return d


def hourly_statistics(hours):
    result = []
    for chain, group in hours.groupby('chain'):
        group = group.sort_values('utc').copy()
        group['time'] = pd.to_datetime(group.utc, utc=True)
        for window, (lo, hi) in WINDOWS.items():
            start, end = pd.Timestamp(lo, tz='UTC'), pd.Timestamp(hi, tz='UTC')
            x = group[group.time.ge(start - pd.Timedelta(days=7)) & group.time.lt(end)]
            baseline = x.loc[x.time.lt(start), 'JA'].median()
            event = x[x.time.ge(start)]
            trough = event.loc[event.JA.idxmin()]
            later = x[x.time.ge(trough.time) & x.JA.ge(baseline)]
            recovery = (int(later.timestamp.iloc[0]) - int(trough.timestamp)) / 3600 if len(later) else np.nan
            result.append(dict(chain=chain, window=window, hours=len(x), baseline_JA=baseline,
                               min_JA=trough.JA, min_timestamp=int(trough.timestamp), min_block=int(trough.block),
                               recovery_hours=recovery))
    return pd.DataFrame(result)


def error_statistics(events):
    rows = []
    for chain in CHAINS:
        for period in ['W1', 'W1_control', 'W2', 'W2_control']:
            g = events[events.chain.eq(chain) & events[period].eq(1)]
            completed = g[g.resolved]
            rows.append(dict(chain=chain, period=period, events=len(g), holders=g.holder.nunique(),
                             request_median=g.request_USDC.median(),
                             completed_share=g.resolved.mean(), wait_hours=completed.wait_hours.median()))
    return pd.DataFrame(rows)


def refill_statistics(refill):
    rows = []
    for f, g in refill.groupby('f'):
        complete = g[~g.censored]
        flows = complete[['supply_inflow_micro', 'repay_inflow_micro', 'liquidation_inflow_micro']].sum()
        rows.append(dict(f=f, days=len(g), zero=int(g.tau.eq(0).sum()), median_tau=g.tau.median(),
                         within24=g.tau.le(24).mean(), censored=int(g.censored.sum()),
                         censored_paid_fraction=g.loc[g.censored, 'paid_fraction'].median(),
                         supply_share=flows.iloc[0] / flows.sum(), repay_share=flows.iloc[1] / flows.sum(),
                         liquidation_share=flows.iloc[2] / flows.sum()))
    return pd.DataFrame(rows)


def hac_fit(formula, data):
    return smf.ols(formula, data).fit(cov_type='HAC', cov_kwds={'maxlags': 7, 'use_correction': True}, use_t=True)


def cox_hac(data):
    """Year-month strata; exact individual Efron scores and chronological HAC7."""
    x = pd.concat([data[['Dup', 'Util', 'log_assets', 'month']],
                   pd.get_dummies(data.weekday.astype(str), prefix='weekday', drop_first=True, dtype=float)], axis=1)
    x['duration'] = np.maximum(data.tau, 1e-6)
    x['event'] = ~data.censored.astype(bool)
    model = CoxPHFitter()
    model.fit(x, duration_col='duration', event_col='event', strata=['month'], robust=True)
    terms = list(model.params_.index)
    X = x[terms].to_numpy()
    beta = model.params_.to_numpy()
    scores = np.zeros_like(X)
    hessian = np.zeros((len(terms), len(terms)))
    for _, ids in x.groupby('month').groups.items():
        ids = np.array(list(ids))
        times = x.loc[ids, 'duration'].to_numpy()
        event = x.loc[ids, 'event'].to_numpy()
        XX = X[ids]
        phi = np.exp(XX @ beta)
        for time in np.unique(times[event]):
            deaths = (times == time) & event
            risk = times >= time
            count = int(deaths.sum())
            risk_sum, death_sum = phi[risk].sum(), phi[deaths].sum()
            scores[ids[deaths]] += XX[deaths]
            for tie in range(count):
                fraction = tie / count
                weights = phi * (risk.astype(float) - fraction * deaths.astype(float)) / (risk_sum - fraction * death_sum)
                mean = (weights[:, None] * XX).sum(axis=0)
                scores[ids[deaths]] -= mean / count
                scores[ids] -= weights[:, None] * (XX - mean)
                centered = XX - mean
                hessian += centered.T @ (centered * weights[:, None])
    assert np.abs(scores.sum(axis=0)).max() < 1e-3
    assert np.abs(np.linalg.inv(hessian) - model.variance_matrix_.to_numpy()).max() < 1e-5
    influence = scores @ model.variance_matrix_.to_numpy()
    covariance = influence.T @ influence
    for lag in range(1, 8):
        cross = influence[lag:].T @ influence[:-lag]
        covariance += (1 - lag / 8) * (cross + cross.T)
    se = np.sqrt(np.diag(covariance))
    rows = []
    for term in ['Dup', 'Util', 'log_assets']:
        i = terms.index(term)
        z = float(beta[i] / se[i])
        rows.append(dict(model='Cox_month_strata', term=term, coef=beta[i], se=se[i],
                         statistic=z, p=math.erfc(abs(z) / math.sqrt(2)), N=len(data)))
    return pd.DataFrame(rows)


def unaffected_regressions(panel):
    """Absorb vault/hour effects; cluster covariance with absorbed-rank CR1."""
    rows = []
    for chain in [1, 42161]:
        for outcome in ['D', 'capacity_assets']:
            q = panel[panel.chain.eq(chain)].dropna(subset=[outcome, 'interaction']).copy()
            xy = q[[outcome, 'interaction']].astype(float)
            for _ in range(1000):
                previous = xy.to_numpy().copy()
                for key in ['vault', 'utc']:
                    xy -= xy.groupby(q[key]).transform('mean')
                if np.abs(xy.to_numpy() - previous).max() < 1e-12:
                    break
            else:
                raise AssertionError('Fixed effects did not converge')
            y, x = xy.iloc[:, 0], xy.iloc[:, 1]
            coef = float(x @ y / (x @ x))
            score = x * (y - coef * x)
            g = score.groupby(q.vault).sum()
            n, clusters = len(q), q.vault.nunique()
            rank = clusters + q.utc.nunique()
            se = math.sqrt(float(g @ g) / float(x @ x) ** 2 * clusters / (clusters - 1) * (n - 1) / (n - rank))
            rows.append(dict(chain=chain, outcome=outcome, coef=coef, se=se, statistic=coef / se,
                             N=n, vault_clusters=clusters))
    return pd.DataFrame(rows)
