from pathlib import Path
import os,json,hashlib,re,zipfile
import pandas as pd
from docx import Document
E=Path(__file__).resolve().parents[1];R=E.parent;P=Path(os.environ.get('MANUSCRIPT_PATH',R.parent/'Counting_the_same_cash.docx'));d=Document(P);x=pd.read_csv(E/'outputs/cross_chain.csv').set_index('chain');s=pd.read_csv(E/'outputs/peer_event_summary.csv').set_index('group');checked=0
# Tables are identified from unique headers, independent of later appendix indices.
t=next(t for t in d.tables if [c.text for c in t.rows[0].cells]==['Measure','Base','Ethereum'])
for original_row,(col,fmt) in enumerate([('vaults','int'),('positive_markets','int'),('assets_usdc','million'),('S_usdc','million'),('J_usdc','million'),('duplicate_usdc','million'),('duplication_pct','percent'),('block','int'),('utc','str')],1):
 row=original_row if original_row<=7 else original_row+2
 for j,chain in enumerate(['Base','Ethereum'],1):
  v=x.loc[chain,col];expected=str(int(v)) if fmt=='int' else f'{v/1e6:.3f}' if fmt=='million' else f'{v:.2f}' if fmt=='percent' else v;assert t.rows[row].cells[j].text==expected;checked+=1
t=next(t for t in d.tables if [c.text for c in t.rows[0].cells]==['Measure','All eligible','Constrained','Covered'])
for row,col in enumerate(['owner_events','transactions','owners','material_gains','full_request_switches','clean_block_gains','median_gain_usdc'],1):
 for j,c in enumerate(['All eligible peers','Initially cash constrained','Initially fully covered'],1):
  v=s.loc[c,col];expected=f'{v:,.3f}' if col=='median_gain_usdc' else str(int(v));assert t.rows[row].cells[j].text==expected;checked+=1
body=' '.join(p.text for p in d.paragraphs);assert all(str(v) in body for v in [308,162,146,495,93,478]);assert '70.05' in body and '51.31' in body and '1.339 million' in body
# Every main regression panel explicitly reports the FE and covariance structure.
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
logical={};key=None
for e in d.element.body:
 if e.tag==qn('w:p'):
  pp=Paragraph(e,d)
  if pp.style.name=='Paper Table Caption':key=pp.text.split('. ',1)[0];logical[key]=[]
 elif e.tag==qn('w:tbl') and key:logical[key].append(Table(e,d))
reg=logical['Table IV']+logical['Table V']+logical['Table VI']
for i,t in enumerate(reg,3):
 txt=' '.join(c.text for row in t.rows for c in row.cells)
 assert ('Covariance' if i==3 else 'Cluster dimensions') in txt
 assert ('Year-month' if i==3 else 'Pair effects' if i==9 else 'Vault') in txt
 assert 'Yes' in txt or i==7
with zipfile.ZipFile(P) as z:
 images={hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')}
 for p in E.glob('figures/*.png'):
  if p.name.startswith('._'):continue
  assert hashlib.sha256(p.read_bytes()).hexdigest() in images,p
caps=[p.text.split('. ',1)[0] for p in d.paragraphs if p.style.name=='Paper Table Caption'];figs=[p.text.split('. ',1)[0] for p in d.paragraphs if p.style.name=='Paper Figure Caption'];assert caps[:9]==['Table '+n for n in ['I','II','III','IV','V','VI','VII','VIII','IX']];assert figs[:5]==['Figure '+str(i) for i in range(1,6)]
res={'status':'PASS','new_table_numeric_cells':checked,'main_tables':9,'main_figures':5,'main_caption_order':'PASS','new_image_hashes':'PASS','regression_footer_settings':'PASS','manuscript_sha256':hashlib.sha256(P.read_bytes()).hexdigest()};(E/'outputs/manuscript_checks.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
