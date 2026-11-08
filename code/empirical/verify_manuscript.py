from pathlib import Path
import os,json,re,zipfile,hashlib
import pandas as pd,numpy as np
from docx import Document
R=Path(__file__).resolve().parents[2];O=R/'outputs/empirical';P=Path(os.environ.get('MANUSCRIPT_PATH',R.parent/'Counting_the_same_cash.docx'));d=Document(P);r=pd.read_csv(O/'regressions.csv');meta={x['model']:x for x in json.loads((O/'models.json').read_text())};tables=list(d.tables);checked=0
# Locate preserved regression panels by their current logical captions.
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
logical_blocks={};key=None
for e in d.element.body:
 if e.tag==qn('w:p'):
  pp=Paragraph(e,d)
  if pp.style.name=='Paper Table Caption':key=pp.text.split('. ',1)[0];logical_blocks[key]=[]
 elif e.tag==qn('w:tbl') and key:logical_blocks[key].append(Table(e,d))
for old,key,panel in [(3,'Table IV',0),(4,'Table IV',1),(5,'Table V',0),(6,'Table V',1),(7,'Table V',2),(8,'Table VI',0),(9,'Table VI',1)]:tables[old]=logical_blocks[key][panel]

norm=lambda s:str(s).replace('−','-').replace(',','').replace('*','').strip()
def f(x,n=3):return '—' if pd.isna(x) else f'{x:.{n}f}'
def val(m,t):return r[(r.model==m)&(r.term==t)].iloc[0]
def checkcell(t,row,col,expected):
 global checked
 actual=tables[t].rows[row].cells[col].text;assert norm(actual)==norm(expected),(t,row,col,actual,expected);checked+=1
for ti,model,terms in [(3,'II_A',['L_cash_hhi','L_log_total_assets','L_utilization10']),(4,'II_B',['shared_exposure','log_assets','active_markets']),(8,'IV_A',['interaction','dlog_cash','lag_D','lag_log_assets']),(9,'IV_B',['overlap','size_similarity','shared_utilization'])]:
 for row,term in enumerate(terms,1):
  a=val(model,term);checkcell(ti,row,1,f(a.coef));checkcell(ti,row,2,f(a.se));checkcell(ti,row,3,f(a.p if ti in [3,9] else a.wild_p))
for col,k in enumerate([5,10,25],1):
 for row,t in [(1,'D10'),(3,'log_assets'),(5,'utilization10')]:
  a=val('III_A_'+str(k),t);checkcell(5,row,col,f(a.coef));checkcell(5,row+1,col,'('+f(a.se)+')')
 for row,field in [(8,'N'),(9,'outcome_mean'),(10,'auc')]:checkcell(5,row,col,str(meta['III_A_'+str(k)][field]) if field=='N' else f(meta['III_A_'+str(k)][field],2 if field=='outcome_mean' else 3))
 for row,spec,t in [(1,'coverage','coverage10'),(3,'both','coverage10'),(5,'both','D10')]:
  a=val('III_B_'+spec+'_'+str(k),t);checkcell(6,row,col,f(a.coef));checkcell(6,row+1,col,'('+f(a.se)+')')
 for row,spec in [(8,'coverage'),(10,'both')]:checkcell(6,row,col,str(meta['III_B_'+spec+'_'+str(k)]['N']));checkcell(6,row+1,col,f(meta['III_B_'+spec+'_'+str(k)]['auc']))
for row,(m,t) in enumerate([('III_A_25','D10'),('III_C_own','D10'),('III_C_peer','peerD10'),('III_C_residual','residual_D10'),('III_C_placebo','placebo10')],1):
 a=val(m,t)
 for c,x in [(1,f(a.coef)),(2,f(a.se)),(3,f(a.wild_p)),(4,str(meta[m]['N'])),(5,f(meta[m]['auc']))]:checkcell(7,row,c,x)
checkcell(9,4,1,str(meta['IV_B']['N']));checkcell(9,5,1,f"{meta['IV_B']['entities']}; {meta['IV_B']['dates']}");checkcell(9,6,1,meta['IV_B']['first'])
# Synchronized snapshot and API tables use separate denominators and capture times.
sn=pd.read_csv(O/'synchronized_snapshots.csv');sn=sn[~sn.name.str.endswith('_0437')].sort_values('name');api=pd.read_csv(O/'api_capture_reconciliation.csv');api=api[~api.capture.str.startswith('early')].sort_values('capture')
newtables=[t for t in d.tables if t.rows[0].cells[0].text=='Date' and t.rows[0].cells[1].text in ['GraphQL','Block']];assert len(newtables)==2
for row,a in zip(newtables[0].rows[1:],api.itertuples()):assert [c.text for c in row.cells]==[a.capture,f(a.graphql_usdc/1e6),f(a.rest_usdc/1e6),f(a.residual_usdc/1e6,6)];checked+=4
for row,a in zip(newtables[1].rows[1:],sn.itertuples()):assert [c.text for c in row.cells]==[a.name.removeprefix('snapshot_'),str(a.block),f(a.standalone_usdc/1e6),f(a.joint_usdc/1e6),f(a.duplication*100,2)];checked+=5
snapshot=sn[sn.name.eq('snapshot_2026-09-08')].iloc[0]
for rr,col,valx in [(1,1,snapshot.standalone_usdc/1e6),(2,1,snapshot.joint_usdc/1e6),(3,1,snapshot.duplicate_usdc/1e6)]:checkcell(2,rr,col,f(valx))
# Narrative magnitudes and caption/cross-reference closure.
text=' '.join(d._element.xpath('.//w:t/text()|.//m:t/text()'));main=[]
for p in d.paragraphs:
 if p.text.strip()=='Supplementary material':break
 main.append(''.join(p._p.xpath('.//w:t/text()|.//m:t/text()')))
main=' '.join(main);normmain=main.replace('−','-')
for m,t in [('III_B_both_25','D10'),('IV_A','interaction'),('IV_B','overlap')]:
 a=val(m,t);assert f(a.coef) in normmain and f(a.se) in normmain
assert f(val('II_A','L_utilization10').coef*100) in text
assert '439' in main and '319' in main and '57.86' in main and '58.19' in main
for forbidden in ['1.410','0.168','0.414','19.6 percent','19,755','58.19 percent is a lower bound for the protocol','disclosure regime conceals']:assert forbidden not in main,forbidden
caps={p.text.strip().split('. ',1)[0] for p in d.paragraphs if p.style.name=='Paper Table Caption'};figs={p.text.strip().split('. ',1)[0] for p in d.paragraphs if p.style.name=='Paper Figure Caption'};assert len(caps)==34 and len(figs)==14
for n in ['I','II','III','IV','V','VI','VII','VIII','IX']+['S'+str(i) for i in range(1,17)]:assert 'Table '+n in caps
cross=set(re.findall(r'\b(Table|Figure)\s+(S(?:\.[A-Z])?\.?\d+|[IVX]+|\d+)',text))
missing=[f'{kind} {n}' for kind,n in cross if f'{kind} {n}' not in caps|figs];assert not missing,missing
body=text.split('References',1)[0];bib=json.loads((R/'verification/bibliography.json').read_text());uncited=[]
for key,v in bib.items():
 first=v['label'].split(',')[0].split(' & ')[0].split(' et al.')[0]
 if not re.search(re.escape(first)+r'.{0,120}?'+re.escape(v['year']),body):uncited.append(key)
assert not uncited,uncited
# Every author/year item in parenthetical citations must match a bibliography first author/year.
known={(v['label'].split(',')[0].split(' & ')[0].split(' et al.')[0],v['year']) for v in bib.values()};unmatched=[]
for group in re.findall(r'\(([^()]*\b(?:19|20)\d{2}[a-z]?[^()]*)\)',body):
 for item in group.split(';'):
  years=re.findall(r'\b(?:19|20)\d{2}[a-z]?\b',item)
  if not years or not re.search(r'[A-Za-z].*,\s*(?:19|20)\d{2}',item):continue
  for year in years:
   if not any(year==yy and item.strip().startswith(author) for author,yy in known):unmatched.append(item)
assert not unmatched,unmatched
refs=len(bib);eq=[re.findall(r'\((S[.A-Z\d]*|\d+)\)',p.text)[-1] for p in d.paragraphs if p.style.name=='Paper Equation'];assert len(eq)==len(set(eq))==12
assert len(d.inline_shapes)==14
scan=r'does not establish|cannot|not proof|not interpreted|imprecise|should be interpreted with caution|we do not claim|需要注意|值得指出|谨慎';hits=re.findall(scan,text,re.I);assert len(hits)<=len(d.paragraphs)/10
# Preserve independently reproduced supplementary tables and original figure bytes.
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
fixture=json.loads((R/'verification/supplementary_reference_values.json').read_text());logical={};key=None
for e in d.element.body:
 if e.tag==qn('w:p'):
  q=Paragraph(e,d)
  if q.style.name=='Paper Table Caption':key=q.text.split('. ',1)[0];logical[key]=[]
 elif e.tag==qn('w:tbl') and key:
  tab=Table(e,d);logical[key]+=re.findall(r'(?<![A-Za-z])[-−]?\d+(?:[,.]\d+)*(?:%|\b)', '\n'.join(c.text for row in tab.rows for c in row.cells))
for key,values in fixture['tables'].items():assert logical[key]==values,key
with zipfile.ZipFile(P) as z:assert set(fixture['image_sha256']).issubset({hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith('word/media/')})
headings=[p.text for p in d.paragraphs if re.match(r'^\d+\. ',p.text) and p.style.name.startswith('Paper')]
assert [int(re.match(r'^(\d+)',x)[1]) for x in headings]==list(range(1,9)),headings
res={'status':'PASS','checked_numeric_cells':checked,'preserved_supplementary_numeric_tokens':sum(map(len,fixture['tables'].values())),'image_hashes_match':True,'main_sections':8,'logical_tables':len(caps),'table_blocks':len(tables),'figures':len(figs),'references':refs,'uncited_references':uncited,'unmatched_citations':unmatched,'cross_reference_targets':len(cross),'missing_cross_references':missing,'equations':eq,'style_scan_hits':len(hits),'manuscript_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'exposure_tables_IV_VI':'estimated_from_archived_chain_states'}
(R/'verification/manuscript_checks.json').write_text(json.dumps(res,indent=2));print(json.dumps(res,indent=2))
