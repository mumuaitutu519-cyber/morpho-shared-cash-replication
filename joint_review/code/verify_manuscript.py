from pathlib import Path
import json,re,os,hashlib
import pandas as pd
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
E=Path(__file__).resolve().parents[1];R=E.parent;O=E/'outputs';P=Path(os.environ.get('MANUSCRIPT_PATH',R.parent/'Counting_the_same_cash.docx'));d=Document(P)
logical={};key=None;checked=0
for e in d.element.body:
 if e.tag==qn('w:p'):
  p=Paragraph(e,d)
  if p.style.name=='Paper Table Caption':key=p.text.split('. ',1)[0];logical[key]=[]
 elif e.tag==qn('w:tbl') and key:logical[key].append(Table(e,d))
def cell(key,panel,row,col,value):
 global checked
 actual=logical[key][panel].rows[row].cells[col].text
 assert actual==str(value),(key,panel,row,col,actual,value);checked+=1
h=pd.read_csv(O/'historical_cash_summary.csv')
for row,z in enumerate(h.itertuples(),1):
 cell('Table I',0,row,1,f'{z.median_duplicate_usdc/1e6:.3f}');cell('Table I',0,row,2,f'{z.median_duplication_pct:.2f}')
x=pd.read_csv(O/'cross_chain_ratios.csv').set_index('chain');t=logical['Table II'][0]
for row in t.rows:
 if row.cells[0].text in ['Standalone capacity / assets, percent','Joint cash bound / assets, percent']:
  col='S_assets_pct' if row.cells[0].text.startswith('Standalone') else 'J_assets_pct'
  for i,chain in enumerate(['Base','Ethereum'],1):assert row.cells[i].text==f'{x.loc[chain,col]:.2f}';checked+=1
a=pd.read_csv(O/'joint_request_summary.csv').set_index('request_pct')
for row,(col,fmt) in enumerate([('dates','i'),('all_individual_pass','i'),('joint_budget_excluded','i'),('excluded_pct_of_passed','p'),('not_excluded','i'),('median_gap_usdc','m'),('max_gap_usdc','m')],1):
 for j,f in enumerate([5,10,25],1):
  z=a.loc[f,col];s='—' if pd.isna(z) else str(int(z)) if fmt=='i' else f'{z:.2f}' if fmt=='p' else f'{z/1e6:.3f}';cell('Table III',0,row,j,s)
cv=pd.read_csv(O/'cross_vault_capacity.csv');cv=cv[cv.positive_common_position]
for row,z in enumerate(cv.itertuples(),1):
 cell('Table VII',0,row,1,'Yes' if z.market_shares_unchanged else 'No')
 for j,v in enumerate([z.before_position_usdc,z.after_position_usdc],2):cell('Table VII',0,row,j,f'{v/1e6:.3f}')
 for j,v in enumerate([z.before_capacity_usdc,z.after_capacity_usdc,z.capacity_change_usdc],1):cell('Table VII',1,row,j,f'{v/1e6:.3f}')
per=pd.read_csv(O/'capacity_persistence.csv')
for row,z in enumerate(per.itertuples(),1):
 for j,v in enumerate([str(z.observed),str(z.changed_shares),f'{z.gains} / {z.unchanged}',str(z.full_request_covered),f'{z.median_gain_usdc/1e6:.3f}'],1):cell('Table IX',0,row,j,v)
assert [[c.text for c in row.cells] for row in logical['Table IX'][0].rows]==[[c.text for c in row.cells] for row in logical['Table S5'][0].rows]
text=' '.join(d._element.xpath('.//w:t/text()|.//m:t/text()'))
for s in ['62 of the 81','55.332 million','120.344 million','0.848 million','76.54 percent','7.580','48.853','4,390 vault-states','60.24 percent','18.04 percent','19.54 and 9.51 percent','513,949','94.57 percent','0.047 percent','247 of 319','eleven still','0.747 million']:
 assert s in text,s
assert 'selection does not change when deposits are netted' not in text
assert 'without reapplying the threshold to net withdrawals' in text
assert any(p.text=='Table S.H.1. Non-Spark monetary amounts in thousands of USDC' for p in d.paragraphs)
caps=[p.text.split('. ',1)[0] for p in d.paragraphs if p.style.name=='Paper Table Caption'];assert caps[:9]==['Table '+x for x in ['I','II','III','IV','V','VI','VII','VIII','IX']]
nums=[int(re.match(r'Table S(\d+)\.',p.text)[1]) for p in d.paragraphs if p.style.name=='Paper Table Caption' and re.match(r'Table S\d+\.',p.text)];assert nums==list(range(1,17))
sectionkeys=set()
for p in d.paragraphs:
 if p.style.name in ['Paper Section','Paper Subsection']:
  m=re.match(r'((?:S\.?[A-Z]?\.?\d*|\d+)(?:\.\d+)*)\.? ',p.text)
  if m:sectionkeys.add(m[1].rstrip('.'))
refs=set(re.findall(r'\b(?:Section|Appendix) (S(?:\.[A-Z]|\d+)(?:\.\d+)?|\d+(?:\.\d+)?)',text));assert refs<=sectionkeys,refs-sectionkeys
# Exact request exclusion is sufficient: no output labels passing the bound as execution success.
checks=json.loads((O/'analysis_checks.json').read_text());assert checks['maximum_S_W_gap_micro']==0
# Second-review economic scale and accounting identity checks.
for row,col in [(8,'excluded_pct_all_dates'),(9,'median_gap_request_pct')]:
 for j,f in enumerate([5,10,25],1):
  z=a.loc[f,col];cell('Table III',0,row,j,'—' if pd.isna(z) else f'{z:.2f}')
agg=pd.read_csv(O/'common_market_aggregate.csv').set_index('phase')
for col in ['standalone_micro','joint_micro','duplicate_micro']:
 vals=[int(agg.loc[k,col]) for k in ['before','after']]
 for v in vals+[vals[1]-vals[0]]:assert f'{v/1e12:.3f}' in text,(col,v)
assert all(agg.standalone_micro-agg.joint_micro==agg.duplicate_micro)
for phrase in ['14.12 percent','28.71 percent','1.25 percent','median across all subsets containing exactly k vaults','median of these 319 daily medians','Individually assessed withdrawal constraints','none covers its fixed pre-deposit full-claim request']:
 assert phrase in text,phrase
assert 'full liquidation capacity does not' not in text and 'any longer' not in text
assert len(logical['Table I'][1].columns)==2
assert 'A same-state fixed-request liquidity shortfall occurs when' in text
compact=re.sub(r'\s+','',text)
assert 'fQvt>Wvt' in compact and 'fQv,t+1>Wv,t+1' in compact
import numpy as np
manifest=pd.read_csv(R/'outputs/r39_shared/subset_manifest.csv') if (R/'outputs/r39_shared/subset_manifest.csv').exists() else None
# Verify the two-stage aggregation from the retained subset-date array.
root=next(R.rglob('subset_daily_ratios.npz')).parent
manifest=pd.read_csv(root/'subset_manifest.csv');rr=np.load(root/'subset_daily_ratios.npz')['ratio'];curve=pd.read_csv(root/'k_curve.csv')
for k in range(1,11):
 masks=manifest.loc[manifest.k==k,'mask'].to_numpy();value=np.nanmedian(np.nanmedian(rr[masks],axis=0))
 expected=curve[(curve.k==k)&(curve.group=='all')].duplication_ratio_median.iloc[0]
 assert abs(value-expected)<1e-12
# Third-review interpretation and attribution checks.
assert 'multiplied by the ratio of market cash to withdrawal capacity' in text
assert 'elasticities rather than directly testing the level derivative' in text
assert 'The matched deposit cohort is predominantly financed by bridged funds.' in text
assert 'mostly bridged position' not in text and 'contrary or null results' not in text
assert logical['Table VIII'][0].rows[9].cells[2].text=='A fixed request of 61.070 million USDC fails before, and succeeds after, the 48.853 million USDC deposit.'
out={'status':'PASS','checked_cells':checked,'section_reference_targets':sorted(refs),'all_section_targets_exist':True,'same_state_joint_screen':'integer arithmetic','main_tables':9,'main_figures':5,'manuscript_sha256':hashlib.sha256(P.read_bytes()).hexdigest()}
(O/'manuscript_checks.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
