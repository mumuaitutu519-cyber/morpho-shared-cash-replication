"""Six manuscript descriptive panels from frozen regression-ready inputs only.

No raw states are read, no regression is estimated, and no regression output is written.
Run: python code/09_desc_stats.py. Paths resolve relative to this package.
"""
from pathlib import Path
import ast,hashlib,json
import numpy as np
import pandas as pd

R=Path(__file__).resolve().parents[1]
O=R/'desc'
FILES={
 'A':'additional_evidence/outputs/daily_estimation_data.csv',
 'B':'outputs/empirical/estimation_panel.parquet',
 'C':'additional_evidence/outputs/market_estimation_at_least_2.csv',
 'D':'additional_evidence/cross_chain/outputs/vault_state_panel.csv',
 'E':'additional_evidence/panel_evidence/outputs/spillover_panel.parquet',
 'F':'additional_evidence/panel_evidence/outputs/event_market_horizons.parquet'}
SCRIPTS={
 'A':['code/empirical/estimate.py','additional_evidence/code/estimate_additions.py'],
 'B':['code/empirical/estimate.py'],
 'C':['additional_evidence/code/estimate_additions.py','additional_evidence/code/estimate_panel_robustness.py'],
 'D':['additional_evidence/code/estimate_cross_chain.py'],
 'E':['additional_evidence/code/estimate_panel_spillover.py','additional_evidence/code/panel_evidence_stats.py'],
 'F':['additional_evidence/code/estimate_borrow_events.py','additional_evidence/code/panel_evidence_stats.py']}
EXPECTED={'A':439,'B':4387,'C':3167,'D':2141,'E':4380,'F':834}
# Every amount/log below is the stored regression-scale variable, except event J,
# which is the explicitly requested level (J_micro / 1e12), not the regression change.
MAPPING={
 'A':[('Dup','duplication','share'),('JA','J_assets','share'),('HHI','L_cash_hhi','share'),('Size','L_log_assets','log USDC'),('Util','L_utilization10','per 10 pp'),('Flow','L_spark_flow_share','share')],
 'B':[('D','D','share'),('Shared','shared_exposure','share'),('Size','log_assets','log USDC'),('Markets','active_markets','count')],
 'C':[('MDup','duplication','share'),('Vaults','vault_count','count'),('Util','utilization10','per 10 pp'),('Cash','log_cash','log USDC'),('Top','largest_position_supply','share')],
 'D':[('D','D','share'),('Shared','shared_market_share','share'),('Markets','active_markets','count'),('Size','log_assets','log USDC'),('Util','utilization10','per 10 pp'),('Top','max_market_share','share')],
 'E':[('ΔS','dW','million USDC'),('Own','OwnFlow','million USDC'),('Peer','OtherVaultFlow','million USDC'),('Outside','OutsideFlow','million USDC'),('Borrow','BorrowFlow','million USDC'),('Shared','ExposureShare','share')],
 'F':[('MDup','market_duplication','share'),('J','J_level_million','million USDC'),('Vaults','vault_count','count')]}
NOTES={
 'A':"New Table 3 columns (1)–(2), old Table 3 Panel A. Dup and JA are contemporaneous outcomes; HHI, Size, Util and Flow use the stored L_ regressors (previous day). The two columns have the same 439 dates. Dup's regression omits Flow, but its summary here is on the same common sample. Flow is committed Spark net flow / total ten-vault assets, retaining the regression's sign. This panel uses the ready-made daily_estimation_data.csv; no additional shift is applied.",
 'B':"New Table 3 column (3). Apply fit_fe('II_B') finite complete-case selection to D, shared_exposure, log_assets, active_markets, vault and date, sorted by vault/date. From 4,390 candidate rows this removes three undefined-D/zero-standalone-capacity rows. No lag is added and no fixed-effect demeaning is applied to descriptive values.",
 'C':"New Table 3 column (4) and Table B2. The saved at-least-two-vault estimation file already enforces positive holdings, at least two holding vaults, finite duplication and all regressors. Reapply complete-case selection to outcome, four terms, market and date; no rows are dropped. Zero idle cash gives undefined log_cash and is excluded upstream. Top is largest selected-vault position / total market supply, not position concentration among the selected vaults. Cash is the stored ln(cash_micro / 1e6), i.e. ln(USDC), even though one archived robustness note loosely calls it log million USDC. The script and stored values govern.",
 'D':"New Table 4 column (2): b_chain_state_FE. Read the saved positive-asset vault-state panel, exclude zero_S, then verify D plus all five regressors are finite as the original script asserts. All seven census dates and four chains are pooled. Retain singleton vault entities as the original estimator does; no singleton removal is introduced. Top is the largest market position / the vault's total positive positions.",
 'E':"New Table 8, old Table 7. Use the common 4,380-row sample of specifications 1a and 1b from the saved spillover_panel, including their outcome, terms, opening exposure and interaction. Consecutive changes within 439 closes supply 438 dates × ten vaults. ΔS maps to dW: change in standalone withdrawal capacity. All five flow/amount variables are already million USDC; do not divide them again. BorrowFlow retains the original signed net borrower-liquidity-flow definition. Shared is the opening ExposureShare. Column 1c (Own=0) and column 1d (ΔD) have smaller samples and are not substituted for the requested common baseline sample.",
 'F':"New Table 9, old Table 8. Retain real borrow events only, complete nine-horizon panels separately for delta_market_duplication and joint_million exactly as estimate_borrow_events.py does, then take the event-block row. MDup describes the event-block LEVEL on the 651-event duplication-regression sample, not delta_market_duplication. J describes the event-block LEVEL J_micro / 1e12 on the 834-event cash-regression sample, not joint_million (which is a change). Vaults is the uncentered count at the preceding block carried across all horizon rows, on those 834 events. Event-block MDup alone is defined for 763 events, but using all 763 would violate the regression complete-panel filter. The prior discussant boundary correction is not imposed: this task preserves the existing regression sample."}


def md(frame):
 def f(x):return str(x).replace('|','/').replace('\n',' ')
 return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(f(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))+'\n'

def finite(z,cols):return z.replace([np.inf,-np.inf],np.nan).dropna(subset=cols).copy()
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 O.mkdir(exist_ok=True)
 regression_paths=[
 'outputs/empirical/regressions.csv','outputs/empirical/models.json',
 'additional_evidence/outputs/regressions.csv','additional_evidence/outputs/model_metadata.csv',
 'additional_evidence/cross_chain/outputs/cross_chain_regressions.csv','additional_evidence/cross_chain/outputs/cross_chain_models.csv',
 'additional_evidence/panel_evidence/outputs/task1_numeric.csv','additional_evidence/panel_evidence/outputs/task1_models.csv',
 'additional_evidence/panel_evidence/outputs/task2_numeric.csv','additional_evidence/panel_evidence/outputs/task2_models.csv']
 protected={rel:hashfile(R/rel) for rel in regression_paths if (R/rel).exists()}
 rows=[];status=[];provenance=[];errors=[];tables=[];checks=[]
 for panel in 'ABCDEF':
  try:
   p=R/FILES[panel];z=pd.read_parquet(p) if p.suffix=='.parquet' else pd.read_csv(p);raw_n=len(z)
   provenance.append({'path':FILES[panel],'sha256':hashfile(p),'bytes':p.stat().st_size})
   if panel=='A':
    required=['duplication','J_assets','L_cash_hhi','L_log_assets','L_utilization10','L_spark_flow_share','date']
    z=finite(z[z.date.ge('2025-01-16')],required).sort_values('date');assert not z.date.duplicated().any()
   elif panel=='B':
    z=z[z.date.ge('2025-01-16') & ~z.date.str.startswith('snapshot')]
    z=finite(z,['D','shared_exposure','log_assets','active_markets','vault','date']).sort_values(['vault','date']);assert not z.duplicated(['vault','date']).any()
   elif panel=='C':
    z=finite(z[z.vault_count.ge(2)],['duplication','vault_count','utilization10','log_cash','largest_position_supply','market','date']).sort_values(['market','date']);assert not z.duplicated(['market','date']).any()
    assert z.cash.gt(0).all() and z.S.gt(0).all()
    assert np.allclose(z.log_cash,np.log(z.cash/1e6),rtol=0,atol=1e-12)
   elif panel=='D':
    zero=z.zero_S if pd.api.types.is_bool_dtype(z.zero_S) else z.zero_S.astype(str).str.lower().eq('true')
    z=z[~zero].copy();assert z.S_micro.gt(0).all()
    assert len(finite(z,['D','shared_market_share','active_markets','log_assets','utilization10','max_market_share','entity','chain_state']))==len(z)
    assert not z.duplicated(['entity','date']).any()
   elif panel=='E':
    z=finite(z,['dW','OwnFlow','OtherVaultFlow','OutsideFlow','BorrowFlow','Peer_x_exposure','ExposureShare','vault','date'])
    assert not z.duplicated(['vault','date']).any()
    assert all(np.allclose(z[a],z[b]/1e12,rtol=0,atol=1e-12) for a,b in [('OwnFlow','OwnFlow_micro'),('OtherVaultFlow','OtherVaultFlow_micro'),('OutsideFlow','OutsideFlow_micro')])
   else:
    z=z[z.event_type.eq('borrow')].copy();assert not z.duplicated(['event_id','horizon']).any()
    assert z.groupby('event_id').vault_count.nunique().eq(1).all()
    eligible={}
    for var,y in [('MDup','delta_market_duplication'),('J','joint_million')]:
     valid=finite(z,[y]).groupby('pair').horizon.nunique();eligible[var]=valid[valid.eq(9)].index
    raw_defined=int(z.loc[z.horizon.eq('event'),'market_duplication'].notna().sum())
    z=z[z.horizon.eq('event') & z.pair.isin(eligible['J'])].copy();z['J_level_million']=z.J_micro/1e12
    assert len(z)==z.event_id.nunique()
    md_ids=eligible['MDup'];checks.append({'check':'F raw event-block MDup defined before complete-horizon filter','actual':raw_defined,'expected':763,'passed':raw_defined==763})
   n=len(z);match=n==EXPECTED[panel];note=NOTES[panel]
   panelrows=[]
   for label,col,unit in MAPPING[panel]:
    use=z[z.pair.isin(md_ids)] if panel=='F' and label=='MDup' else z
    x=use[col].astype(float);assert x.notna().all() and np.isfinite(x).all()
    if unit=='count':assert np.equal(x,np.floor(x)).all()
    row=dict(panel=panel,variable=label,n=len(x),mean=x.mean(),sd=x.std(ddof=1),min=x.min(),p50=x.quantile(.5),max=x.max())
    rows.append(row);panelrows.append((row,unit))
    if panel=='F' and label=='MDup':
     checks.append({'check':'F MDup complete regression events','actual':len(x),'expected':651,'passed':len(x)==651})
    keys=[c for c in ['date','vault','market','entity','event_id','horizon','block'] if c in use]
    if label==MAPPING[panel][0][0] or panel=='F' and label=='J':use[keys].to_csv(O/(f'sample_keys_{panel}'+('_MDup' if panel=='F' and label=='MDup' else '')+'.csv'),index=False)
   status.append(dict(panel=panel,expected=EXPECTED[panel],actual=n,status='MATCH' if match else 'MISMATCH',input_rows=raw_n,removed_rows=raw_n-n,source=FILES[panel]))
   tab=[]
   for row,unit in panelrows:
    rr={'Variable':row['variable'],'Unit':unit,'N':str(row['n'])}
    for key,label in [('mean','Mean'),('sd','SD'),('min','Min'),('p50','Median'),('max','Max')]:
     v=row[key];digits=2 if unit=='count' and key in ['mean','sd'] else 0 if unit=='count' else 3
     # Actual count medians can be half-integers; don't round unless exactly integer.
     if unit=='count' and key=='p50' and not float(v).is_integer():digits=1
     rr[label]=f'{(0.0 if round(v,digits)==0 else v):.{digits}f}'
    tab.append(rr)
   tables.append(f'## Panel {panel}\n\nExpected observations: {EXPECTED[panel]:,}; selected: {n:,}. **'+('MATCH' if match else 'MISMATCH')+'**.\n\n'+note+'\n\nSource: `'+FILES[panel]+'`.\n\nRegression script(s): '+', '.join('`'+s+'`' for s in SCRIPTS[panel])+'.\n\n'+md(pd.DataFrame(tab)))
  except Exception as exc:
   errors.append({'panel':panel,'error':repr(exc)});status.append(dict(panel=panel,expected=EXPECTED[panel],actual=None,status='FAILED',source=FILES[panel]))
   tables.append(f'## Panel {panel}\n\n**Could not match:** {exc!r}. No alternative raw-state sample was substituted. Other panels continue.\n')
 frame=pd.DataFrame(rows,columns=['panel','variable','n','mean','sd','min','p50','max'])
 # Keep CSV rounding identical to display, while exposing full precision separately.
 frame.to_csv(O/'desc_stats_unrounded.csv',index=False,float_format='%.17g')
 rounded=frame.copy().astype({k:object for k in ['mean','sd','min','p50','max']})
 for idx,row in rounded.iterrows():
  unit=next(u for name,_,u in MAPPING[row.panel] if name==row.variable)
  for col in ['mean','sd','min','p50','max']:
   value=float(row[col]);digits=2 if unit=='count' and col in ['mean','sd'] else 0 if unit=='count' else 3
   if unit=='count' and col=='p50' and not value.is_integer():digits=1
   rounded.at[idx,col]=f'{(0.0 if round(value,digits)==0 else value):.{digits}f}'
 rounded.to_csv(O/'desc_stats.csv',index=False)
 pd.DataFrame(status).to_csv(O/'sample_counts.csv',index=False)
 mapping=[{'panel':p,'variable':name,'source_column':column,'units':unit,'time':'previous day (stored L_)' if p=='A' and column.startswith('L_') else 'event block level' if p=='F' and name!='Vaults' else 'preceding block count' if p=='F' else 'as entered in regression'} for p in MAPPING for name,column,unit in MAPPING[p]]
 pd.DataFrame(mapping).to_csv(O/'variable_map.csv',index=False)
 for rel in sorted({s for v in SCRIPTS.values() for s in v}):provenance.append({'path':rel,'sha256':hashfile(R/rel),'bytes':(R/rel).stat().st_size})
 for rel,before in protected.items():checks.append({'check':'Regression unchanged: '+rel,'actual':hashfile(R/rel),'expected':before,'passed':hashfile(R/rel)==before})
 checks.extend({'check':'Sample count '+s['panel'],'actual':s.get('actual'),'expected':s['expected'],'passed':s['status']=='MATCH'} for s in status)
 checks.append({'check':'All 30 requested variables','actual':len(frame),'expected':30,'passed':len(frame)==30})
 # Compare against frozen model metadata; do not import/run estimators with write side effects.
 comparisons=[('B','outputs/empirical/models.json','II_B',None),('D','additional_evidence/cross_chain/outputs/cross_chain_models.csv','cross_chain_exposure','b_chain_state_FE'),('E','additional_evidence/panel_evidence/outputs/task1_models.csv','task1','1b')]
 for panel,rel,model,spec in comparisons:
  path=R/rel
  if path.suffix=='.json':metadata=next(x for x in json.loads(path.read_text()) if x['model']==model);count=metadata['N']
  else:
   m=pd.read_csv(path);m=m[m.model.eq(model)&m.spec.eq(spec)];count=int(m.iloc[0].Obs)
  actual=next(s.get('actual') for s in status if s['panel']==panel)
  checks.append({'check':'Frozen regression metadata '+panel,'actual':actual,'expected':count,'passed':actual==count})
 # Independent scale/lag checks use frozen derived daily data, never raw states.
 daily=pd.read_csv(R/'outputs/empirical/daily.csv')
 daily=daily[daily.date.between('2025-01-15','2026-03-30')].sort_values('date').copy()
 a=pd.read_csv(R/FILES['A']).set_index('date')
 for label,column,values in [('HHI','L_cash_hhi',daily.cash_hhi.shift(1)),('Size','L_log_assets',np.log(daily.assets).shift(1)),('Util','L_utilization10',daily.utilization10.shift(1))]:
  previous=pd.Series(values.to_numpy(),index=daily.date).reindex(a.index)
  gap=float(np.max(np.abs(previous.to_numpy()-a[column].to_numpy())))
  checks.append({'check':'A exact previous-day '+label,'actual':gap,'expected':0,'passed':gap<1e-12})
 flows=pd.read_csv(R/'additional_evidence/outputs/spark_daily_flow.csv').set_index('date').spark_net_flow_micro
 lagflow=(daily.date.map(flows).fillna(0)/1e6/daily.assets).shift(1)
 previous=pd.Series(lagflow.to_numpy(),index=daily.date).reindex(a.index)
 gap=float(np.max(np.abs(previous.to_numpy()-a.L_spark_flow_share.to_numpy())))
 checks.append({'check':'A exact previous-day Flow','actual':gap,'expected':0,'passed':gap<1e-12})
 for rel in ['outputs/empirical/daily.csv','additional_evidence/outputs/spark_daily_flow.csv']:
  provenance.append({'path':rel,'sha256':hashfile(R/rel),'bytes':(R/rel).stat().st_size})
 runner=ast.parse((R/'run_replication.py').read_text())
 jobs=next(ast.literal_eval(n.value) for n in runner.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='jobs' for t in n.targets))
 checks.append({'check':'Descriptive script registered exactly once in run-all','actual':jobs.count('code/09_desc_stats.py'),'expected':1,'passed':jobs.count('code/09_desc_stats.py')==1})
 (O/'input_manifest.json').write_text(json.dumps(provenance,indent=2))
 validation={'passed':not errors and all(x['passed'] for x in checks),'errors':errors,'checks':checks,'sample_sd_ddof':1,'statistics_before_FE_absorption':True,'raw_states_read':False,'regressions_run':0,'regression_outputs_unchanged':all(hashfile(R/k)==v for k,v in protected.items())}
 (O/'validation.json').write_text(json.dumps(validation,indent=2))
 intro='''# Descriptive statistics — Counting the same cash

All six panels use saved regression-ready observations and the corresponding estimator's complete-case filters, before fixed-effect absorption. No raw contract states are read and no regression is re-estimated. SD is the sample standard deviation (ddof=1); median is the ordinary sample median. Shares are fractions, not percentages; utilization is in 10-percentage-point units. Natural logs and million-USDC scales retain the exact stored regression convention. No winsorization or additional exclusions are introduced.

`desc_stats.csv` has the requested eight columns, variable order and display precision. `desc_stats_unrounded.csv` preserves full precision. Counts have two decimal places for Mean and SD and integer extrema/medians; all other displayed values have three decimals. `sample_counts.csv`, `variable_map.csv`, `sample_keys_*.csv`, `input_manifest.json` and `validation.json` provide inspectable sample identities and provenance.

'''
 count_table=pd.DataFrame(status)[['panel','expected','actual','status']]
 report=intro+md(count_table)+'\n'+'\n'.join(tables)+'''\n## Reproduce and preservation check

Run `python code/09_desc_stats.py` from the replication-package root. The package's `run_replication.py` now registers this script as its last job. The original runner is archived as `desc/run_replication.before.py`; the change adds the descriptive stage and makes its final job count dynamic. The upstream regression stages were not rerun during this descriptive-only task.

The script reads only frozen estimation inputs; if a panel raises an error it records the reason and continues to the other panels. The existing inputs support all six requested samples; Panel F's variable-specific 651/834 counts are intentional. `validation.json` checks sample counts, frozen model metadata and byte-for-byte preservation of ten regression coefficient/metadata files. The four daily lags are also independently reconciled against frozen derived daily levels and committed-flow summaries, including the pre-sample 15 January observation. Negative logs in panels C/D are retained: positive balances below one USDC have negative natural logs. Input files and original regression scripts are SHA-256 pinned in `input_manifest.json`.
'''
 (O/'DESC_REPORT.md').write_text(report)
 print(pd.DataFrame(status)[['panel','expected','actual','status']].to_string(index=False))
 print('Variables:',len(rows),'Validation:',validation['passed'],'Regression outputs unchanged:',validation['regression_outputs_unchanged'])
 if not validation['passed']:raise SystemExit(1)

if __name__=='__main__':main()
