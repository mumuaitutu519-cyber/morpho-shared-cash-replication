#!/usr/bin/env python3
"""Compare current display tokens with frozen source archives. No estimation."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import csv,json,re,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1]
def tokens(s):
    return re.findall(r'[-+]?\d[\d,]*(?:\.\d+)?',s.replace('−','-').replace('–','-'))
def compare(a,b):
    aa,bb=tokens(a),tokens(b)
    if len(aa)!=len(bb):return False
    for x,y in zip(aa,bb):
        x=x.replace(',','');y=y.replace(',','')
        places=len(x.split('.')[1]) if '.' in x else 0
        if Decimal(y).quantize(Decimal(1).scaleb(-places),rounding=ROUND_HALF_UP)!=Decimal(x):return False
    return re.findall(r'\*+',a)==re.findall(r'\*+',b)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'verify');args=ap.parse_args()
    blocks=json.loads((ROOT/'data/manuscript_tables_current.json').read_text())
    old=json.loads((ROOT/'data/reference_tables_archived.json').read_text())
    mapping=json.loads((ROOT/'data/table_coordinate_map.json').read_text())
    rows=[]
    def add(block,r,c,expected,source):
        displayed=blocks[block]['rows'][r][c]
        if not tokens(displayed):return
        rows.append(dict(table=blocks[block]['table'],block=block,row=r,column=c,
          row_label=blocks[block]['rows'][r][0],manuscript_value=displayed,archived_reference=expected,
          numeric_tokens=len(tokens(displayed)),status='MATCH' if compare(displayed,expected) else 'MISMATCH',
          source=source,method='Frozen archive display comparison; not fresh estimation'))
    desc=list(csv.DictReader((ROOT/'desc/desc_stats.csv').open()))
    positions=[i for i,r in enumerate(blocks[1]['rows']) if len(r)==17 and r[2].replace(',','').isdigit()]
    assert len(positions)==len(desc)==30
    for r,d in zip(positions,desc):
        assert blocks[1]['rows'][r][0]==d['variable']
        for c,key in zip(range(2,17,2),['n','mean','sd','min','p25','p50','p75','max']):
            add(1,r,c,d[key],f'desc/desc_stats.csv: panel={d["panel"]}, variable={d["variable"]}, field={key}')
    for m in mapping:
        b,r=m['block'],m['row']
        # Row zero and the second Table 3 header are structural column labels.
        if r==0 or (b==3 and r==1) or (b==18 and r==1):continue
        prior=old[m['archived_block']]['rows'][m['archived_row']]
        for c in range(2,len(prior),2):
            add(b,r,c,prior[c],f'data/reference_tables_archived.json: block={m["archived_block"]}, row={m["archived_row"]}, column={c}')
    args.output.mkdir(exist_ok=True,parents=True)
    with (args.output/'VERIFICATION.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    summary=[]
    for table in dict.fromkeys(x['table'] for x in rows):
        selected=[r for r in rows if r['table']==table]
        summary.append(dict(table=table,cells=len(selected),numeric_tokens=sum(r['numeric_tokens'] for r in selected),
          matched=sum(r['status']=='MATCH' for r in selected),mismatched=sum(r['status']!='MATCH' for r in selected)))
    with (args.output/'TABLE_SUMMARY.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print('Frozen table comparison only. See verify/VERIFICATION_SCOPE.md for limitations.')
    return int(any(r['status']!='MATCH' for r in rows))
if __name__=='__main__':raise SystemExit(main())
