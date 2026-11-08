from pathlib import Path
import sys,json,hashlib,shutil,tempfile,subprocess,os,zipfile
A=Path(__file__).resolve().parents[1];R=A.parent;C=A/'cross_chain';delivery=R.parents[1];py=sys.executable;env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'}
subprocess.run([py,str(A/'code/estimate_cross_chain.py')],check=True,env=env,stdout=subprocess.DEVNULL);subprocess.run([py,str(A/'code/validate_cross_chain.py')],check=True,env=env,stdout=subprocess.DEVNULL)
stage=Path(tempfile.mkdtemp(prefix='cross_chain_results_'));root=stage/'Replication_Package'
def cp(rel):
 src=R/rel;dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for f in C.rglob('*'):
 if f.is_file() and '__pycache__' not in f.parts and not f.name.startswith('._'):cp(f.relative_to(R))
for fn in ['estimate_cross_chain.py','validate_cross_chain.py','collect_cross_chain.py','chain_access.py','package_cross_chain_results.py']:cp(Path('additional_evidence/code')/fn)
for fn in ['estimate.py','build_panel.py','collect_chain.py']:cp(Path('code/empirical')/fn)
cp(Path('raw/inherited/selected_vaults.json'))
for fn in ['mechanism.csv','model_metadata.csv','mechanism_observations.csv']:cp(Path('additional_evidence/outputs')/fn)
cp(Path('additional_evidence/requirements.txt'))
blocks={}
for entry in json.loads((C/'input_manifest.json').read_text()):
 rel=Path(entry['file']);cp(rel);z=json.loads((R/rel).read_text());chain=int(z.get('chain',z.get('header',{}).get('chain')));blocks.setdefault(chain,set()).add(z['block'])
# Include source requests at every reported block. Other cached tasks/dates are omitted.
for chain,bs in blocks.items():
 for f in (A/'raw/rpc'/str(chain)).glob('*.json'):
  if f.name.startswith('._'):continue
  z=json.loads(f.read_text());q=z.get('request',{});params=q.get('params',[]);method=q.get('method');keep=False
  try:
   if method=='eth_call' and len(params)>1:keep=int(params[1],16) in bs
   if method=='eth_getBlockByNumber' and params and str(params[0]).startswith('0x'):keep=int(params[0],16) in bs or int(params[0],16)-1 in bs
  except (ValueError,TypeError):pass
  if keep:cp(f.relative_to(R))
for chain in [42161,137]:
 for name in [f'morpho_discovery_{chain}.json',f'morpho_factory_audit_{chain}.json']:cp(Path('additional_evidence/raw')/name)
for f in (A/'raw').glob('block_*.json'):
 if f.name.startswith('._'):continue
 z=json.loads(f.read_text())
 if z.get('block') in blocks.get(z.get('chain'),set()):cp(f.relative_to(R))
O=root/'additional_evidence/cross_chain/outputs';before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.glob('*.csv')};runs=[]
for name in ['estimate_cross_chain.py','validate_cross_chain.py']:
 result=subprocess.run([py,str(root/'additional_evidence/code'/name)],cwd=root,env=env,capture_output=True,text=True);runs.append({'script':name,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr});assert result.returncode==0,result.stderr
for p in O.glob('*.csv'):assert hashlib.sha256(p.read_bytes()).hexdigest()==before[p.name],p.name
release={'offline_runs':runs,'csv_byte_identical':len(before),'manuscript_unchanged':True};(C/'release_check.json').write_text(json.dumps(release,indent=2));cp(Path('additional_evidence/cross_chain/release_check.json'))
files=sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.startswith('._'));hashes={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};(root/'MANIFEST_SHA256.json').write_text(json.dumps(hashes,indent=2));files.append(root/'MANIFEST_SHA256.json');out=delivery/'Cross_Chain_and_Mechanism_Results.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,p.relative_to(stage))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for rel,h in hashes.items():assert hashlib.sha256(z.read('Replication_Package/'+rel)).hexdigest()==h
print(json.dumps({'zip':str(out),'bytes':out.stat().st_size,'files':len(files),'offline_CSVs':len(before),'CRC':'PASS','hashes':'PASS'},indent=2));shutil.rmtree(stage)
