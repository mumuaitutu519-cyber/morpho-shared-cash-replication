import ast,hashlib,json,re
from pathlib import Path
import pandas as pd
from settings import OUT,R,PROJECT,MANUSCRIPT

def run():
    checks=[]
    def check(item,ok,detail=''):
        checks.append(dict(item=item,passed=bool(ok),detail=detail))
    text=(OUT/'DISCUSSANT_REPORT.md').read_text()
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if not target.startswith(('https:','http:')):check('Report link '+target,(OUT/target).exists())
    for name in ['table8','full_replay']:
        b=OUT/'package'/name
        manifest=json.loads((b/'input_manifest.json').read_text())
        for r in manifest:
            p=b/r['path'];check(name+' hash '+r['path'],p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'])
        for p in list((b/'code').glob('*.py'))+[b/'README.md']:
            check(name+' portable '+p.name,'/Volumes/' not in p.read_text())
        check(name+' successful captured log',(b/'output/run.log').exists() and 'Traceback' not in (b/'output/run.log').read_text())
    for p in (OUT/'code').glob('*.py'):
        ast.parse(p.read_text());check('Python syntax '+p.name,True)
    programs=pd.read_csv(OUT/'logs/source_map_program_audit.csv')
    check('All source-map program paths exist',programs['exists'].all())
    sm=pd.read_csv(OUT/'SOURCE_MAP.csv',dtype=str)
    for row in sm.itertuples():
        for name in row.result_files.split('; '):
            root=OUT if name.startswith(('tables/','data/','package/')) else PROJECT if name.startswith('addon_package/') else R
            check('Source map '+row.current_table+' '+name,(root/name).exists())
    word=json.loads((OUT/'logs/word_checker_status.json').read_text())
    check('614 mapped Word values unchanged',word['checked_numeric_cells']==614 and word['differences']==0)
    check('Manuscript byte identical',hashlib.sha256(MANUSCRIPT.read_bytes()).hexdigest()==word['sha256_before']==word['sha256_after'])
    for f in ['package/table8/output/checks.csv','package/full_replay/output/replay_verification.csv']:
        v=pd.read_csv(OUT/f);check('All reproduced '+f,v.all_match.all() if 'all_match' in v else v.different_rows.eq(0).all())
    pred=pd.read_csv(OUT/'tables/incremental_prediction.csv')
    check('All 72 D specifications retained',len(pred)==72 and pred.status.eq('PASS').all())
    check('36 chronological holdout comparisons',len(pd.read_csv(OUT/'tables/incremental_prediction_oos.csv'))==36)
    ov=pd.read_csv(OUT/'tables/borrow_overlap_full_tail.csv')
    check('Corrected overlap totals',ov.next_within_24h_events.sum()==386 and ov.next_within_72h_events.sum()==548 and ov.next_within_168h_events.sum()==669)
    check('78 certified isolated events',len(pd.read_csv(OUT/'data/table8_isolated_coverage_certified.csv'))==78)
    frame=pd.DataFrame(checks);frame.to_csv(OUT/'logs/delivery_validation.csv',index=False)
    result={'checks':len(frame),'passed':int(frame.passed.sum()),'failed':frame.loc[~frame.passed].to_dict('records')}
    (OUT/'logs/delivery_validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
    if result['failed']:raise SystemExit(1)
if __name__=='__main__':run()
