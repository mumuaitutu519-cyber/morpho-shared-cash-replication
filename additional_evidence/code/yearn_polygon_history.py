from chain_access import *
import subprocess
for day in ['2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31']:
 p=A/'raw'/f'yearn_137_{day}.json'
 if not p.exists():
  z=subprocess.run([sys.executable,str(A/'code/collect_yearn.py'),'137',day],capture_output=True,text=True);(A/f'yearn_137_{day}.log').write_text(z.stdout+z.stderr);print(day,z.returncode,flush=True)
