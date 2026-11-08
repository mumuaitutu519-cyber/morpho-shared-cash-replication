from pathlib import Path
import pandas as pd,numpy as np,json,datetime,hashlib,importlib.util
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
E=Path(__file__).resolve().parents[1] if Path(__file__).resolve().parent.name=='code' else Path('/Volumes/T9/JRF_Ryu_delivery/research_enrichment')
R=E.parent if E.parent.name=='Replication_Package' else Path('/Volumes/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/Replication_Package')
O=E/'outputs';O.mkdir(exist_ok=True);F=E/'figures';F.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('build',R/'code/empirical/build_panel.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
records=[]
for chain in ['base','ethereum']:
 z=json.loads(next(p for p in (E/f'raw/{chain}_all_chain').glob('*_decoded.json') if not p.name.startswith('._')).read_text());rows,checks=b.build(z);p=pd.DataFrame(rows);v=pd.DataFrame(checks);g=p.groupby('market').agg(P=('position','sum'),cash=('cash','first'),S=('standalone','sum'));S=int(g.S.sum());J=int(np.minimum(g.P,g.cash).sum());assert J<=z['morpho_token_balance'];assert (g.S>=np.minimum(g.P,g.cash)).all();assert v.asset_reconciliation_gap.abs().max()==0
 discovery=json.loads((E/f'raw/{chain}_all_discovery.json').read_text())['response']['data']['vaults'];assert discovery['pageInfo']['count']==discovery['pageInfo']['countTotal'];selected=json.loads((E/f'raw/{chain}_all_selected.json').read_text());assert set(x['address'].lower() for x in selected)==set(v.vault)
 record=dict(chain=chain.title(),block=z['block'],utc=datetime.datetime.fromtimestamp(z['timestamp'],datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),vaults=len(v),positive_block_vaults=int(v.assets.gt(0).sum()),queue_markets=len(g),positive_markets=int(g.P.gt(0).sum()),assets_usdc=int(v.assets.sum())/1e6,S_usdc=S/1e6,J_usdc=J/1e6,duplicate_usdc=(S-J)/1e6,duplication_pct=(S-J)/S*100,asset_reconciliation_max_micro=0)
 records.append(record);v.to_csv(O/f'{chain}_all_vaults.csv',index=False);p.to_csv(O/f'{chain}_all_positions.csv',index=False)
cross=pd.DataFrame(records);cross.to_csv(O/'cross_chain.csv',index=False)
s=pd.read_csv(R/'reports/revision33/state_comparisons.csv');links=pd.read_csv(R/'reports/revision33/transaction_source_cash_links.csv');g=s[(s.phase=='after')&(s.identity!='Spark')&s.positive_opening_claim&s.unchanged_shares].merge(links,on='tx',validate='many_to_one',suffixes=('','_source'));assert not g.duplicated(['tx','owner']).any();g.to_csv(O/'peer_event_panel.csv',index=False)
summary=[]
for label,mask in [('All eligible peers',g.tx.notna()),('Initially cash constrained',g.material_initial_shortfall),('Initially fully covered',~g.material_initial_shortfall)]:
 h=g[mask];summary.append(dict(group=label,owner_events=len(h),transactions=h.tx.nunique(),owners=h.owner.nunique(),material_gains=int(h.material_capacity_gain.sum()),full_request_switches=int(h.covered_after_shortfall.sum()),median_gain_usdc=h.capacity_change_usdc.median(),clean_block_gains=int((h.material_capacity_gain&h.same_block_other_market_operations.eq(0)).sum())))
su=pd.DataFrame(summary);su.to_csv(O/'peer_event_summary.csv',index=False)
daily=pd.read_csv(R/'outputs/empirical/daily.csv');daily=daily[daily.date.between('2025-01-16','2026-03-30')].copy();assert len(daily)==439;daily.to_csv(O/'historical_plot_data.csv',index=False)
plt.rcParams.update({'font.family':'DejaVu Serif','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':300})
def save(fig,name):
 fig.savefig(F/(name+'.png'),dpi=300,bbox_inches='tight',facecolor='white');fig.savefig(F/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
fig,axs=plt.subplots(2,1,figsize=(7,5.4),sharex=True,gridspec_kw={'height_ratios':[2,1]});x=pd.to_datetime(daily.date);axs[0].plot(x,daily.S/1e6,label='Summed standalone capacity',color='#1f4e79');axs[0].plot(x,daily.J/1e6,label='Joint cash bound',color='#a34a28',linestyle='--');axs[0].fill_between(x,daily.J/1e6,daily.S/1e6,color='#1f4e79',alpha=.12);axs[0].set_ylabel('Million USDC');axs[0].legend(frameon=False,loc='upper left',fontsize=9);axs[1].plot(x,100*daily.duplication,color='#333333');axs[1].set_ylabel('Duplicated share (%)');axs[1].set_ylim(0,100);axs[1].set_xlabel('Daily contract state');fig.tight_layout();save(fig,'historical_capacity')
fig,ax=plt.subplots(figsize=(7,3.7));xx=np.arange(2);width=.32
for off,col,label,color in [(-width/2,'S_usdc','Summed standalone capacity','#1f4e79'),(width/2,'J_usdc','Joint cash bound','#a34a28')]:
 bars=ax.bar(xx+off,cross[col]/1e6,width,label=label,color=color)
 for bar,value in zip(bars,cross[col]/1e6):ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+8,f'{value:.1f}',ha='center',fontsize=10)
ax.set_xticks(xx,[f'{r.chain}\n{r.vaults} vaults; duplication {r.duplication_pct:.2f}%' for r in cross.itertuples()]);ax.set_ylabel('Million USDC');ax.set_ylim(0,760);ax.legend(frameon=False,loc='upper right',fontsize=9);fig.tight_layout();save(fig,'cross_chain_capacity')
fig,axs=plt.subplots(1,2,figsize=(7,3.6),gridspec_kw={'width_ratios':[1,1.5]});counts=[int(g.loc[~g.material_initial_shortfall,'material_capacity_gain'].sum()),int(g.loc[g.material_initial_shortfall,'material_capacity_gain'].sum())];den=[int((~g.material_initial_shortfall).sum()),int(g.material_initial_shortfall.sum())];rates=np.array(counts)/den*100;bars=axs[0].bar([0,1],rates,color=['#777777','#1f4e79'],width=.55);axs[0].set_xticks([0,1],['Initially\ncovered','Initially\nconstrained']);axs[0].set_ylabel('Capacity gain > 1 USDC (%)');axs[0].set_ylim(0,119)
for i,(n,tot,rate) in enumerate(zip(counts,den,rates)):axs[0].text(i,rate+3,f'{n}/{tot}',ha='center')
h=g[g.material_initial_shortfall];clean=h.same_block_other_market_operations.eq(0)
for mask,label,marker,color in [(clean,'No other market operation','o','#1f4e79'),(~clean,'Other operation in block','x','#a34a28')]:axs[1].scatter(h.loc[mask,'deposit_usdc']/1e6,h.loc[mask,'capacity_change_usdc']/1e6,label=label,marker=marker,c=color,s=35)
axs[1].set_ylim(0,33);axs[1].set_xlabel('Treasury deposit (million USDC)');axs[1].set_ylabel('Peer capacity gain (million USDC)');axs[1].legend(frameon=False,fontsize=7,loc='upper left');fig.tight_layout();save(fig,'peer_capacity_response')
res={'status':'PASS','cross_chain':records,'events':summary,'historical_days':len(daily),'figures':3,'raw_decoded_hashes':{str(p.relative_to(E)):hashlib.sha256(p.read_bytes()).hexdigest() for p in E.glob('raw/*_all_chain/*_decoded.json') if not p.name.startswith('._')}};(O/'analysis_checks.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
