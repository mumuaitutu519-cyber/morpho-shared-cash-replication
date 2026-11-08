from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
O=Path(__file__).resolve().parents[2]/'outputs'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
f=pd.read_csv(O/'market_decomposition.csv').head(10);fig,ax=plt.subplots(figsize=(10,5.5));x=np.arange(len(f));w=.36
ax.bar(x-w/2,f.cash_share_median,w,color='#18364D',label='Cash share');ax.bar(x+w/2,f.duplication_share_median,w,color='#A7C5D8',edgecolor='#6B8BA0',linewidth=.5,label='Duplication share')
labels=[n+'\n'+m[2:8] for n,m in zip(f.name,f.market)];ax.set_xticks(x,labels,rotation=35,ha='right');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.set_ylabel('Median daily share');ax.set_xlabel('Market (collateral / USDC; market ID prefix)');ax.legend(frameon=False);ax.set_ylim(0,1.07);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.subplots_adjust(bottom=.30,left=.09,right=.98,top=.96);fig.savefig(O/'fig_market_shares.pdf');fig.savefig(O/'fig_market_shares.png',dpi=180);plt.close(fig)
g=pd.read_csv(O/'k_curve.csv');fig,ax=plt.subplots(figsize=(8,5))
for group,label,color,marker in [('with_spark','Includes Spark','#18364D','o'),('without_spark','Excludes Spark','#8C642E','s')]:
 a=g[g.group.eq(group)];ax.plot(a.k,a.duplication_ratio_median,color=color,marker=marker,label=label);ax.fill_between(a.k,a.p10,a.p90,color=color,alpha=.16)
ax.set_xticks(range(1,11));ax.set_xlim(.8,10.2);ax.set_ylim(0,.82);ax.set_xlabel('Number of vaults in subset');ax.set_ylabel('Duplication rate');ax.yaxis.set_major_formatter(PercentFormatter(1));ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.legend(frameon=False,loc='upper left');fig.subplots_adjust(left=.12,bottom=.18,right=.98,top=.97)
fig.text(.12,.04,'Lines: time median of daily subset medians.\nBands: time medians of daily subset P10 and P90; not confidence intervals.',fontsize=8.5);fig.savefig(O/'fig_k_curve.pdf');fig.savefig(O/'fig_k_curve.png',dpi=180)
