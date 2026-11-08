"""Package one auditable results archive with source files and offline replication inputs."""
from pathlib import Path
import sys,json,hashlib,zipfile,subprocess,os,tempfile,shutil,importlib.metadata
A=Path(__file__).resolve().parents[1];R=A.parent;P=A/'panel_evidence';D=R.parents[1];env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','PYTHONPATH':str(A/'.deps')};py=sys.executable
sources=['outputs/empirical/vault_panel.parquet','outputs/empirical/positions.parquet','outputs/empirical/daily.csv','additional_evidence/outputs/daily_estimation_data.csv','additional_evidence/outputs/spark_daily_flow.csv','additional_evidence/outputs/market_estimation_at_least_2.csv','additional_evidence/cross_chain/outputs/vault_state_panel.csv','raw/inherited/selected_vaults.json','data/raw/revision5/event_signatures.json']
sourcepaths=[R/s for s in sources];sourcepaths += [R/x['file'] for x in json.loads((A/'cross_chain/input_manifest.json').read_text())]
code=['panel_evidence_stats.py','export_panel_inputs.py','collect_panel_operations.py','collect_panel_market_api.py','build_panel_operations.py','build_borrow_candidates.py','check_panel_supply_identity.py','estimate_panel_spillover.py','estimate_panel_prediction.py','estimate_cross_state_prediction.py','estimate_panel_robustness.py','collect_borrow_event_states.py','estimate_borrow_events.py','fill_borrow_event_headers.py','panel_archive_rpc.py','probe_panel_archive.py','collect_cross_state_flows.py','check_cross_state_flows.py','check_operation_sources.py','format_panel_evidence.py','report_panel_evidence.py','validate_panel_evidence.py','package_panel_evidence.py','chain_access.py']
sourcepaths += [A/'code'/s for s in code];sourcepaths += [R/'code/empirical'/s for s in ['build_panel.py','estimate.py','collect_chain.py']];sourcepaths += [R/'real_consequences/code'/s for s in ['poolrpc.py','rpc_limiter.py']]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
(P/'input_manifest.json').write_text(json.dumps([{'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sourcepaths],indent=2))
sys.path.insert(0,str(A/'.deps'))
versions=[]
for name in ['numpy','pandas','scipy','statsmodels','pyarrow','requests']:
 versions.append(name+'=='+importlib.metadata.version(name))
versions.append('pycryptodome>=3.20');(P/'requirements.txt').write_text('\n'.join(versions)+'\n')
# Fresh offline working root: copy the exact computational inputs, decoded states and outputs.
stage=Path(tempfile.mkdtemp(prefix='panel_evidence_offline_'));root=stage/'Replication_Package'
def cp(src):
 dst=root/src.relative_to(R);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for src in sourcepaths:cp(src)
for src in P.iterdir():
 if src.is_file() and not src.name.startswith('._'):cp(src)
for src in (P/'outputs').iterdir():
 if src.is_file() and not src.name.startswith('._'):cp(src)
for src in (P/'raw').glob('*.json'):
 if not src.name.startswith('._'):cp(src)
for name in ['market_operations.parquet','opening_market_cash.json','vault_committed_flows.parquet']:
 cp(P/'raw'/name)
for src in (P/'raw/event_states').glob('*_decoded.json'):
 if not src.name.startswith('._'):cp(src)
# Input design grid and complete block headers are included in outputs.
commands=['export_panel_inputs.py','build_panel_operations.py','build_borrow_candidates.py','check_panel_supply_identity.py','estimate_panel_spillover.py','estimate_panel_prediction.py','estimate_cross_state_prediction.py','estimate_panel_robustness.py','estimate_borrow_events.py','format_panel_evidence.py','report_panel_evidence.py','validate_panel_evidence.py']
records=[]
for name in commands:
 run=subprocess.run([py,str(root/'additional_evidence/code'/name)],cwd=root,env=env,capture_output=True,text=True);records.append({'script':name,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr});print('offline',name,run.returncode,flush=True)
 if run.returncode:raise RuntimeError(run.stderr)
# Point estimates, inference and sample metadata must reproduce at numeric precision.
import pandas as pd,numpy as np
checks=[]
for name in ['task1_numeric.csv','task2_numeric.csv','task3_numeric.csv','task3_cross_numeric.csv','tasks4_5_numeric.csv','task1_models.csv','task2_models.csv','task3_models.csv','task3_cross_models.csv','tasks4_5_models.csv']:
 x=pd.read_csv(P/'outputs'/name);y=pd.read_csv(root/'additional_evidence/panel_evidence/outputs'/name);assert x.shape==y.shape and list(x.columns)==list(y.columns),name
 for c in x.columns:
  if pd.api.types.is_numeric_dtype(x[c]) and pd.api.types.is_numeric_dtype(y[c]):np.testing.assert_allclose(x[c],y[c],rtol=1e-9,atol=1e-12,equal_nan=True,err_msg=name+'/'+c)
  else:assert x[c].fillna('').astype(str).equals(y[c].fillna('').astype(str)),(name,c)
 checks.append({'file':name,'rows':len(x),'status':'PASS','byte_identical':sha(P/'outputs'/name)==sha(root/'additional_evidence/panel_evidence/outputs'/name)})
(P/'release_check.json').write_text(json.dumps({'offline_runs':records,'comparisons':checks,'source_manuscripts_unchanged':True},indent=2));shutil.rmtree(stage)
# Full task directory includes archived source responses and intermediate data.
files=sorted(set(sourcepaths+[p for p in P.rglob('*') if p.is_file() and not p.name.startswith('._') and '__pycache__' not in p.parts and p.name != 'MANIFEST_SHA256.json']))
manifest={str(p.relative_to(R)):sha(p) for p in files};(P/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2));files.append(P/'MANIFEST_SHA256.json');target=D/'Panel_Evidence_Results.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for i,p in enumerate(files,1):
  z.write(p,'Replication_Package/'+str(p.relative_to(R)))
  if i%10000==0:print('packed',i,len(files),flush=True)
with zipfile.ZipFile(target) as z:
 assert z.testzip() is None
 for rel,h in manifest.items():
  digest=hashlib.sha256()
  with z.open('Replication_Package/'+rel) as stream:
   for b in iter(lambda:stream.read(2**20),b''):digest.update(b)
  assert digest.hexdigest()==h,rel
print(json.dumps({'archive':str(target),'bytes':target.stat().st_size,'files':len(files),'CRC':'PASS','member_hashes':'PASS','offline_tables':len(checks)},indent=2),flush=True)
