from pathlib import Path
import pandas as pd,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
O=Path('reports/revision39_pilot');font_manager.fontManager.addfont('/Library/Fonts/Arial Unicode.ttf');plt.rcParams.update({'font.family':'Arial Unicode MS','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,'svg.fonttype':'none'})
d=pd.read_csv(O/'shared_daily.csv',parse_dates=['date']);fig,ax=plt.subplots(2,1,figsize=(9,7),sharex=True,layout='constrained')
for key,label,col,ls in [('original3','原3金库','#1f4e79','--'),('baseline10','基期前10金库','#a86224','-'),('baseline9_exclude_extrafi','剔除Extrafi的9金库','#47765b',':')]:
 g=d[d['sample'].eq(key)]
 ax[0].plot(g.date,g.dup_pct,label=label,color=col,ls=ls,lw=1.25)
 ax[1].plot(g.date,g.D_usdc/1e6,color=col,ls=ls,lw=1.25)
ax[0].set(ylabel='重复计量比例（%）',title='共享现金：扩大金库范围与延长日度窗口');ax[0].legend(ncol=3,loc='upper left',fontsize=9,frameon=False,bbox_to_anchor=(0,1.01));ax[0].set_ylim(0,90)
ax[1].set(ylabel='重复现金（百万USDC）',xlabel='日期（UTC收盘）')
for a in ax:a.axvline(pd.Timestamp('2025-11-30'),color='#888888',lw=.7);a.grid(axis='y',alpha=.2)
fig.savefig(O/'shared_cash_trend.png',dpi=240);fig.savefig(O/'shared_cash_trend.svg');plt.close(fig)
e=pd.read_csv(O/'ethena_observation_waits.csv');fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax,key,title,xmax in zip(axes,['wait_1_hours','wait_1000000_hours'],['下一笔供给 ≥ 1 USDC','下一笔供给 ≥ 100万USDC'],[3,44]):
 for flag,label,col in [(True,'缺口状态（39）','#a86224'),(False,'无缺口状态（61）','#1f4e79')]:
  x=np.sort(e.loc[e.gap.eq(flag),key]);ax.step(np.r_[0,x],np.r_[0,np.arange(1,len(x)+1)/len(x)*100],where='post',label=label,color=col,lw=1.5)
 ax.set(xlabel='从日度观察状态起等待小时',ylabel='已出现供给的比例（%）',title=title,xlim=(0,xmax),ylim=(0,103));ax.grid(axis='y',alpha=.2)
axes[0].legend(loc='lower right',frameon=False,fontsize=9);fig.suptitle('Ethena缺口与Spark后续供给：等待时间分布',fontsize=12);fig.savefig(O/'ethena_wait_distribution.png',dpi=240);fig.savefig(O/'ethena_wait_distribution.svg');plt.close(fig)
