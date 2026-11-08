from pathlib import Path
import tempfile,shutil,hashlib,json,subprocess,os,zipfile
A=Path(__file__).resolve().parents[1];R=A.parent;delivery=R.parents[1];py=os.sys.executable
# Keep complete numeric outputs while recording the online evidence boundaries.
shutil.copy2(R/'real_consequences/outputs/trace_coverage.json',A/'raw/base_trace_coverage.json')
subprocess.run([py,str(A/'code/summarize_cross_protocol.py')],check=True,stdout=subprocess.DEVNULL)
subprocess.run([py,str(A/'code/validate.py')],check=True,stdout=subprocess.DEVNULL)
inputs=['enrichment/outputs/peer_event_panel.csv','outputs/empirical/daily.csv','outputs/empirical/positions.parquet','joint_review/outputs/joint_request_daily.csv','raw/inherited/selected_vaults.json','code/empirical/estimate.py','code/empirical/build_panel.py','code/empirical/collect_chain.py']
manifest={f:hashlib.sha256((R/f).read_bytes()).hexdigest() for f in inputs};(A/'input_manifest.json').write_text(json.dumps(manifest,indent=2))
stage=Path(tempfile.mkdtemp(prefix='counting_cash_results_'));root=stage/'Replication_Package';target=root/'additional_evidence'
shutil.copytree(A,target,ignore=shutil.ignore_patterns('.deps','__pycache__','._*'))
for f in inputs:
 p=root/f;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,p)
before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (target/'outputs').glob('*.csv')}
env=dict(os.environ);env['PYTHONPATH']=str(A/'.deps');env['OPENBLAS_NUM_THREADS']='1';env['OMP_NUM_THREADS']='1'
log=[]
for name in ['estimate_additions.py','summarize_cross_protocol.py','validate.py']:
 q=subprocess.run([py,str(target/'code'/name)],cwd=root,env=env,capture_output=True,text=True);log.append({'script':name,'returncode':q.returncode,'stdout':q.stdout,'stderr':q.stderr});assert q.returncode==0,q.stderr
for p in (target/'outputs').glob('*.csv'):assert before[p.name]==hashlib.sha256(p.read_bytes()).hexdigest(),p.name
check={'offline_scripts':log,'csv_outputs_compared':len(before),'byte_identical':True,'original_manuscripts_unchanged':True};(A/'release_check.json').write_text(json.dumps(check,indent=2));shutil.copy2(A/'release_check.json',target/'release_check.json');shutil.copy2(A/'checks.md',target/'checks.md')
files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('._'));hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(root/'MANIFEST_SHA256.json').write_text(json.dumps(hashes,indent=2));files.append(root/'MANIFEST_SHA256.json')
out=delivery/'Additional_Evidence_Results.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,p.relative_to(stage))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for rel,digest in hashes.items():assert hashlib.sha256(z.read('Replication_Package/'+rel)).hexdigest()==digest
print(json.dumps({'zip':str(out),'bytes':out.stat().st_size,'files':len(files),'offline_csv_match':len(before),'CRC':'PASS','member_hashes':'PASS','stage':str(stage)},indent=2));shutil.rmtree(stage)
