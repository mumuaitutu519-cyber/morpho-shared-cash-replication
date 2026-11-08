"""Export nine manuscript panels from existing frozen figure inputs; no estimation."""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib import font_manager as fm
R=Path(__file__).resolve().parents[1]
O=R/'results/figures/panels';O.mkdir(parents=True,exist_ok=True)
inputs=['enrichment/outputs/historical_plot_data.csv','enrichment/outputs/cross_chain.csv','outputs/k_curve.csv','reports/revision25/analysis_daily.csv','reports/revision29/market_cash_sequence.parquet','reports/revision29/treasury_transaction_links.csv','reports/revision5/vault_economic_events.parquet','reports/revision22/large_withdrawal_day_market_sequence.csv']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={f:sha(R/f) for f in inputs}
font=Path('/System/Library/Fonts/Supplemental/Times New Roman.ttf')
if font.exists():fm.fontManager.addfont(str(font));family='Times New Roman'
else:family='Liberation Serif';fm.findfont(family,fallback_to_default=False)
plt.rcParams.update({'font.family':family,'font.size':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8.5,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7})
exports=[];audits=[]
def panel():
 fig,ax=plt.subplots(figsize=(7.2,2.8));fig.subplots_adjust(left=.07,right=.99,bottom=.17,top=.96)
 ax.grid(axis='y',color='#dddddd',lw=.5);ax.set_axisbelow(True)
 return fig,ax
def save(fig,ax,name,n):
 fig.canvas.draw()
 assert not ax.get_xlabel() and not ax.get_ylabel() and not ax.get_title()
 assert any(t.get_visible() and t.get_text() for t in ax.get_xticklabels())
 assert not any('Panel ' in t.get_text() for t in ax.texts)
 for ext in ['png','pdf']:
  f=O/f'{name}.{ext}';fig.savefig(f,dpi=300,bbox_inches='tight',pad_inches=.04,facecolor='white');exports.append(f)
 audits.append({'panel':name,'source_rows':n,'axis_titles':False,'panel_titles':False,'x_tick_labels':[t.get_text() for t in ax.get_xticklabels() if t.get_visible()],'canvas_inches':[7.2,2.8]});plt.close(fig)
d=pd.read_csv(R/inputs[0]);assert len(d)==439 and d.date.iloc[0]=='2025-01-16' and d.date.iloc[-1]=='2026-03-30';x=pd.to_datetime(d.date)
for letter in ['A','B']:
 fig,ax=panel()
 if letter=='A':
  ax.plot(x,d.S/1e6,color='#1f4e79',label='Summed standalone capacity');ax.plot(x,d.J/1e6,color='#a34a28',ls='--',label='Joint cash bound');ax.fill_between(x,d.J/1e6,d.S/1e6,color='#1f4e79',alpha=.12);ax.legend(loc='upper left',frameon=False,ncol=2)
 else:ax.plot(x,100*d.duplication,color='#333333');ax.set_ylim(0,100)
 ax.xaxis.set_major_locator(md.MonthLocator(interval=2));ax.xaxis.set_major_formatter(md.DateFormatter('%b %Y'));ax.set_xlim(x.iloc[0],x.iloc[-1]);save(fig,ax,f'figure_1_panel_{letter}',len(d))
k=pd.read_csv(R/inputs[2]);k=k[k.group.eq('all')].sort_values('k');assert k.k.tolist()==list(range(1,11));fig,ax=panel();y=k.duplication_ratio_median*100;ax.plot(k.k,y,color='#1f4e79',marker='o')
for xx,yy in zip(k.k,y):ax.annotate(f'{yy:.2f}',(xx,yy),xytext=(0,6),textcoords='offset points',ha='center')
ax.set_xticks(range(1,11));ax.set_ylim(-3,68);save(fig,ax,'figure_2',len(k))
c=pd.read_csv(R/inputs[1]);assert c.vaults.tolist()==[162,146];fig,ax=panel();xx=np.arange(2);w=.32
for off,col,label,color in [(-w/2,'S_usdc','Summed standalone capacity','#1f4e79'),(w/2,'J_usdc','Joint cash bound','#a34a28')]:
 bars=ax.bar(xx+off,c[col]/1e6,w,label=label,color=color)
 for bar,val in zip(bars,c[col]/1e6):ax.annotate(f'{val:.1f}',(bar.get_x()+bar.get_width()/2,val),xytext=(0,4),textcoords='offset points',ha='center')
ax.set_xticks(xx,[f'{r.chain}\n{r.vaults} vaults; duplication {r.duplication_pct:.2f}%' for r in c.itertuples()]);ax.set_ylim(0,760);ax.legend(loc='upper right',frameon=False);save(fig,ax,'figure_3',len(c))
m=pd.read_parquet(R/inputs[4]);m['utc']=pd.to_datetime(m.timestamp,unit='s',utc=True);lo=pd.Timestamp('2025-10-04 13:25',tz='UTC');hi=pd.Timestamp('2025-10-04 14:30',tz='UTC');g=m[m.utc.between(lo,hi)].sort_values(['block','log_index'])
fig,ax=panel();ax.step(g.utc,g.cash_after_raw/1e12,where='post',color='#244a64',lw=1.25,label='Common-market cash')
v=pd.read_parquet(R/inputs[6]);v['utc']=pd.to_datetime(v.timestamp,unit='s',utc=True);v=v[v.type.eq('Withdraw')&v.onBehalf.eq('0xb8734a14fbd4aa2d44e6aa830405ffc861ba313c')&v.utc.between(lo,hi)&v.assets_raw.gt(1e12)];assert len(v)==3
for i,r in enumerate(v.itertuples()):ax.axvline(r.utc,color='#777777',ls=':',lw=.9,label='Ethena withdrawal (30m)' if i==0 else None)
q=pd.read_csv(R/inputs[5]);q=q[q.deposit_exceeds_opening_cash&q.date.eq('2025-10-04')].sort_values('block');assert len(q)==2
for i,r in enumerate(q.itertuples()):
 t=pd.Timestamp(int(r.timestamp),unit='s',tz='UTC');ax.axvline(t,color='#a4512c',ls='--',lw=1.1,label='Spark arrival-funded deposit' if i==0 else None);ax.plot(t,m[m.tx.eq(r.tx)].cash_after_raw.iloc[-1]/1e12,'o',color='#a4512c',ms=4)
ax.set_xlim(lo,hi);ax.xaxis.set_major_formatter(md.DateFormatter('%H:%M'));ax.set_ylim(top=g.cash_after_raw.max()/1e12*1.40);ax.legend(loc='upper left',frameon=True,facecolor='white',edgecolor='white',framealpha=1,ncol=2);save(fig,ax,'figure_4',len(g))
d=pd.read_csv(R/inputs[3]);assert len(d)==319;x=pd.to_datetime(d.date)
for letter in ['A','B']:
 fig,ax=panel()
 if letter=='A':
  ax.plot(x,d.claim,color='#244e69',label='Treasury claim');ax.plot(x,d.capacity,color='#b07b36',ls='--',label='Withdrawal capacity');ax.legend(frameon=False,ncol=2,loc='upper left')
 else:ax.plot(x,d.coverage,color='#244e69');ax.axhline(25,color='#7e8589',ls='--',lw=1)
 ax.xaxis.set_major_locator(md.MonthLocator());ax.xaxis.set_major_formatter(md.DateFormatter('%b'));save(fig,ax,f'figure_5_panel_{letter}',len(d))
e=pd.read_csv(R/inputs[7],dtype={'matched_account_withdrawal':str});e=e[e.date.eq('2025-04-08')];hours=(e.timestamp.astype('int64')-int(pd.Timestamp('2025-04-08',tz='UTC').timestamp()))/3600;positive=e.type.isin(['Supply','Repay','Liquidation']);amount=e.assets_micro.astype(float)/1e12;selected=e.matched_account_withdrawal.eq('True');assert selected.sum()==3
for letter in ['A','B']:
 fig,ax=panel()
 if letter=='A':
  ax.step(hours,e.cash_after_micro.astype(float)/1e12,where='post',color='#173e5a',lw=1.4);ax.scatter(hours[selected],e.loc[selected,'cash_after_micro'].astype(float)/1e12,color='#9b3d34',s=22,zorder=4,label='Treasury withdrawal')
  for t,r in zip(hours[selected],e[selected].itertuples()):ax.annotate(f'{float(r.assets_micro)/1e12:.3f}',(t,float(r.cash_after_micro)/1e12),xytext=((-8,10) if t>22 else (6,8)),ha=('right' if t>22 else 'left'),textcoords='offset points',fontsize=9)
  ax.legend(loc='upper left',frameon=False)
 else:
  ax.step(hours,amount.where(positive,0).cumsum(),where='post',color='#173e5a',label='Cumulative cash inflows');ax.step(hours,amount.where(~positive,0).cumsum(),where='post',color='#9b3d34',ls='--',label='Cumulative cash outflows');ax.legend(loc='upper left',frameon=False)
 ax.set_xlim(0,24);ax.set_xticks([0,4,8,12,16,20,24]);ax.set_ylim(bottom=0);save(fig,ax,f'figure_6_panel_{letter}',len(e))
assert before=={f:sha(R/f) for f in inputs}
assert len(exports)==18
(O/'checks.md').write_text('# Export checks\n\n- PASS: 18 images; nine PNG and nine PDF files.\n- PASS: every panel has x tick labels and no axis or panel titles.\n- PASS: all eight input files retain their SHA-256 hashes.\n- PASS: sample sizes 439 and 319; three withdrawal and two deposit markers in Figure 4; three withdrawals in Figure 6.\n')
(O/'manifest.json').write_text(json.dumps({'font':family,'inputs':before,'outputs':[{'file':str(p.relative_to(R)),'sha256':sha(p)} for p in exports+[Path(__file__),O/'checks.md']],'layout_checks':audits},indent=2))
print(O)
