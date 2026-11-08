"""Source-dependent full rerun. Continue after a failed stage and preserve its log."""
import subprocess,sys,json,time
from pathlib import Path
B=Path(__file__).resolve().parent; O=B.parent
stages=[('build_full_replay_bundle.py',B/'build_full_replay_bundle.py'),
        ('full_replay',O/'package/full_replay/code/run_all.py'),
        ('01_incremental_prediction.py',B/'01_incremental_prediction.py'),
        ('02_borrow_events.py',B/'02_borrow_events.py'),
        ('02b_event_boundary_audit.py',B/'02b_event_boundary_audit.py'),
        ('03_withdrawal_spillovers.py',B/'03_withdrawal_spillovers.py'),
        ('04_word_checker.py',B/'04_word_checker.py'),
        ('04_package_and_source_map.py',B/'04_package_and_source_map.py'),
        ('table8_portable',O/'package/table8/code/reproduce.py'),
        ('05_report.py',B/'05_report.py'),
        ('06_validate_delivery.py',B/'06_validate_delivery.py')]
status=[]
for name,path in stages:
    start=time.monotonic()
    dest=O/'package'/('table8' if name=='table8_portable' else 'full_replay')/'output/run.log' if name in ['table8_portable','full_replay'] else O/'logs'/f'{name}.log'
    with dest.open('w') as f:
        p=subprocess.run([sys.executable,str(path)],stdout=f,stderr=subprocess.STDOUT)
    status.append(dict(stage=name,exit_code=p.returncode,elapsed_seconds=time.monotonic()-start,log=str(dest.relative_to(O))))
    print(name,'PASS' if p.returncode==0 else 'FAILED — continued',flush=True)
(O/'logs/pipeline_status.json').write_text(json.dumps(status,indent=2))
raise SystemExit(int(any(r['exit_code'] for r in status)))
