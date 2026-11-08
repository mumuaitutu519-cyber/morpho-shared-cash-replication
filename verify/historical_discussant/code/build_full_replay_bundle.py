from pathlib import Path
import shutil,json,hashlib,importlib.metadata
from settings import OUT,RAW,ADD

B=OUT/'package/full_replay'
for d in ['data','code','output']:(B/d).mkdir(parents=True,exist_ok=True)
files={RAW/'market_operations.parquet':'market_operations.parquet',
       ADD/'tail_operations.parquet':'tail_operations.parquet',
       ADD/'positions.parquet':'positions.parquet',
       ADD/'vault_states.parquet':'vault_states.parquet',
       ADD/'full_daily_market_cash.parquet':'market_cash.parquet',
       ADD/'B1_daily_replay.csv':'expected_replay.csv',
       ADD/'tail_coverage.json':'tail_coverage.json'}
rows=[]
for p,name in files.items():
    dest=B/'data'/name
    if not dest.exists():shutil.copy2(p,dest)
    digest=hashlib.sha256(dest.read_bytes()).hexdigest()
    assert digest==hashlib.sha256(p.read_bytes()).hexdigest()
    rows.append({'path':'data/'+name,'bytes':dest.stat().st_size,'sha256':digest})
(B/'input_manifest.json').write_text(json.dumps(rows,indent=2))
shutil.copy2(Path(__file__).with_name('full_replay_analyze.py'),B/'code/analyze.py')
(B/'code/run_all.py').write_text('from pathlib import Path\nimport subprocess,sys\nsubprocess.run([sys.executable,str(Path(__file__).with_name("analyze.py"))],check=True)\n')
(B/'requirements.txt').write_text(''.join(name+'=='+importlib.metadata.version(name)+'\n' for name in ['numpy','pandas','pyarrow','numba']))
(B/'README.md').write_text('''# Full 439-day recorded-operation replay

Run from this directory with Python 3.12:

```
pip install -r requirements.txt
python code/run_all.py
```

All inputs and code paths are relative. No external mount, RPC, or public download is required. The bundle includes the complete 33-market historical operation ledger, its reconciled seven-day tail, all initial vault positions/queues, totalAssets and full 33-market starting cash. Input file names, bytes and SHA-256 hashes are pinned in input_manifest.json. Outputs are written under output/. The original six runs per date (5/10/25 percent, largest/smallest first) are reconstructed and compared with all 2,634 archived results. Vault-level unpaid requests at 24 hours are also retained, permitting a genuine vault-level later-outcome analysis. The 24-hour indicator is taken before applying any event later than that horizon.

The code preserves integer micro-USDC accounting, fixed starting queues/positions, own-action removal, external inflows as recorded and clipped external outflows. Results stop at full payment or 168 hours; no estimate in the manuscript is overwritten. Every 25 dates a recovery checkpoint is saved.
''')
print('Full replay bundle staged:',B,flush=True)
