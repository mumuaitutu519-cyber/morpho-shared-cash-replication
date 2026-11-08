from pathlib import Path
import zipfile,subprocess,sys,json,hashlib
import pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];O=R/'reports/revision27';W=O/'offline_replay';W.mkdir(exist_ok=True);archive=R/'delivery/JIFMIM26/R26_evidence_update.zip'
with zipfile.ZipFile(archive) as z:
 assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in z.namelist());z.extractall(W)
runs=[]
for name in ['owner_audit','native_yields','build_panel','estimate']:
 p=subprocess.run([sys.executable,'code/revision26_'+name+'.py'],cwd=W,text=True,capture_output=True);(O/('replay_'+name+'.log')).write_text(p.stdout+'\n'+p.stderr);runs.append({'script':name,'returncode':p.returncode});print(runs[-1],flush=True)
 if p.returncode:break
out={'source_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'runs':runs,'scope':'Independent directory, same retained inputs and runtime; not independent historical recollection.'}
if all(x['returncode']==0 for x in runs) and len(runs)==4:
 a=pd.read_csv(R/'reports/revision26/regression_results.csv').sort_values(['model','term']).reset_index(drop=True);b=pd.read_csv(W/'reports/revision26/regression_results.csv').sort_values(['model','term']).reset_index(drop=True);assert a[['model','term']].equals(b[['model','term']]);out['max_coefficient_difference']=float((a.coefficient-b.coefficient).abs().max());out['max_p_difference']=float((a.p-b.p).abs().max());out['all_coefficients_exact']=bool(a.coefficient.equals(b.coefficient));out['rows']=len(a)
(O/'offline_replay_summary.json').write_text(json.dumps(out,indent=2));print(out)
