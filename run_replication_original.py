"""Offline reproduction using the observations distributed with this package."""
from pathlib import Path
import subprocess,sys,json,os
R=Path(__file__).resolve().parent
os.environ.setdefault('OPENBLAS_NUM_THREADS','1')
jobs=['code/r39_shared/analyze.py','replay_r24.py','code/revision33_validate.py','code/revision28_explore.py','code/revision28_localization.py','code/revision35_analysis.py','code/descriptive_statistics.py','code/public_snapshots.py','verify_results.py','code/empirical/redecode.py','code/empirical/build_panel.py','code/empirical/snapshot_audit.py','code/empirical/estimate.py','code/empirical/check_estimates.py','code/empirical/validate_descriptives.py','code/empirical/verify_manuscript.py','enrichment/code/redecode_census.py','enrichment/code/analyze.py','enrichment/code/verify_extension.py','joint_review/code/cross_vault_states.py','joint_review/code/analyze.py','joint_review/code/verify_manuscript.py','code/09_desc_stats.py']
log=R/'verification/run_logs';log.mkdir(parents=True,exist_ok=True)
bootstrap="import runpy,socket,sys;from pathlib import Path;p=Path(sys.argv[1]).resolve();sys.path.insert(0,str(p.parent));socket.socket.connect=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('Offline reproduction: network disabled'));socket.create_connection=socket.socket.connect;runpy.run_path(str(p),run_name='__main__')"
status=[]
for job in jobs:
 print('Running',job,flush=True)
 with (log/(Path(job).stem+'.log')).open('w') as f:
  result=subprocess.run([sys.executable,'-c',bootstrap,str(R/job)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 status.append({'script':job,'exit_code':result.returncode})
 (R/'verification/run_status.json').write_text(json.dumps(status,indent=2))
 if result.returncode:raise SystemExit('Failed: '+job+'; see verification/run_logs')
print(f'PASS: all {len(jobs)} offline computations completed, including joint requests, cross-vault states, exposure regressions, manuscript checks and descriptive statistics.')
