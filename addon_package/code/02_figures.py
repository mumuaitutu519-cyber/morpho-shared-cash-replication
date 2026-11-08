"""Rebuild Figure C1 (Ethereum/Arbitrum) and Figure C2; no top title."""
import os
import time
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parents[1] / 'output/.mplconfig'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import OUT, WINDOWS, read


def style():
    plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42, 'savefig.facecolor': 'white'})


def figures():
    begin = time.perf_counter()
    OUT.mkdir(exist_ok=True)
    style()
    hours = read('hourly_eth_arb_base.csv')
    fig, axes = plt.subplots(4, 2, figsize=(9.2, 8.8), sharex='col', sharey='row')
    for panel, (chain, name) in enumerate([(1, 'Ethereum'), (42161, 'Arbitrum')]):
        g = hours[hours.chain.eq(chain)].sort_values('utc').copy()
        g['time'] = pd.to_datetime(g.utc, utc=True)
        for col, (window, (lo, hi)) in enumerate(WINDOWS.items()):
            start, end = pd.Timestamp(lo, tz='UTC'), pd.Timestamp(hi, tz='UTC')
            x = g[g.time.ge(start-pd.Timedelta(days=7)) & g.time.lt(end)]
            baseline = x.loc[x.time.lt(start), 'JA'].median()
            a, b = axes[2*panel, col], axes[2*panel+1, col]
            a.plot(x.time, 100*x.Dup, color='#2166ac', linewidth=1.15)
            b.plot(x.time, 100*x.JA, color='#b2182b', linewidth=1.15)
            b.axhline(100*baseline, color='#555555', linestyle='--', linewidth=.85,
                      label='Prior 7-day median')
            a.text(.03, .08, window, transform=a.transAxes, ha='left', va='bottom',
                   bbox=dict(facecolor='white', edgecolor='none', alpha=.85, pad=2))
            ticks = [t for t in pd.date_range(x.time.iloc[0].normalize(), x.time.iloc[-1].normalize(),
                       freq='5D' if window=='W1' else '7D')
                       if x.time.iloc[-1]-t >= pd.Timedelta(days=3)] + [x.time.iloc[-1]]
            for ax in [a, b]:
                ax.axvline(start, color='black', linewidth=.8)
                ax.grid(axis='y', color='#dddddd', linewidth=.55)
                ax.set_xlim(x.time.iloc[0], x.time.iloc[-1])
                ax.set_xticks(ticks)
                ax.set_xticklabels([t.strftime('%b %d') for t in ticks])
            b.legend(frameon=False, fontsize=8, loc='best')
        axes[2*panel, 0].set_ylabel(name+'\nDup (%)')
        axes[2*panel+1, 0].set_ylabel('J / assets (%)')
    for ax in axes[-1]:
        ax.set_xlabel('UTC')
    # Chain names are on the left axis, with no chain heading or overall title.
    fig.tight_layout(h_pad=1.2, w_pad=1.3)
    for ext in ['png', 'pdf']:
        fig.savefig(OUT / f'Figure_C1.{ext}', dpi=220)
    plt.close(fig)
    d = read('refill_daily.csv')
    d = d[d.f.eq(25)].sort_values('date')
    fig, ax = plt.subplots(figsize=(9.2, 3.8))
    date = pd.to_datetime(d.date)
    ax.plot(date, d.tau, color='#2166ac', linewidth=1)
    ax.set_yscale('function', functions=(np.log1p, np.expm1))
    ax.set_yticks([0, 1, 6, 24, 72, 168])
    ax.set_ylabel('τ 25% (hours; log(1 + τ) scale)')
    ax.set_xlabel('UTC close date')
    censored = d[d.censored]
    ax.scatter(pd.to_datetime(censored.date), censored.tau, marker='^', s=12,
               color='#b2182b', label='Right-censored at 168 h', zorder=3)
    ax.legend(frameon=False, loc='upper right', bbox_to_anchor=(1, 1.16), fontsize=9)
    ticks = [date.iloc[0]] + list(pd.date_range('2025-04-01', '2026-01-01', freq='QS')) + [date.iloc[-1]]
    ax.set_xlim(date.iloc[0], date.iloc[-1])
    ax.set_xticks(ticks)
    ax.set_xticklabels([t.strftime('%Y-%m-%d') if i in [0, len(ticks)-1] else t.strftime('%Y-%m') for i, t in enumerate(ticks)])
    for window, (lo, hi) in WINDOWS.items():
        start, end = pd.Timestamp(lo), pd.Timestamp(hi)
        ax.axvspan(start, end, color='grey', alpha=.2)
        ax.text(start+(end-start)/2, .65, window, transform=ax.get_xaxis_transform(), ha='center', fontsize=9)
    ax.grid(axis='y', color='#dddddd', linewidth=.55)
    fig.tight_layout()
    for ext in ['png', 'pdf']:
        fig.savefig(OUT / f'Figure_C2.{ext}', dpi=220)
    plt.close(fig)
    (OUT / 'figure_notes.txt').write_text(
        'Figure C1: upper two rows Ethereum; lower two rows Arbitrum. W1/W2 columns include prior seven days. '
        'Vertical lines mark window starts; dashed horizontal lines are prior-seven-day median JA. Ratios are percentages. '
        'Figure C2: largest-first 25% requests, 439 UTC closes; log(1+tau) axis retains zero waits; triangles indicate right censoring at 168 hours.\n', encoding='utf-8')
    print(f'Figures C1 and C2 rebuilt in {time.perf_counter()-begin:.2f} seconds.')


if __name__ == '__main__':
    figures()
