"""Finalize from saved checkpoints without rerunning collection or estimation."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
DATA_PY='/Users/sunhan/Documents/Codex/2026-10-14/codex-shared-cash-stress-counting-the/work/venv/bin/python'
DOC_PY='/Users/sunhan/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
for name,runtime in [('verify_call_headers.py',DOC_PY),('validate_results.py',DATA_PY),('write_inputs.py',DATA_PY),('build_outputs.py',DOC_PY)]:
    subprocess.run([runtime,str(ROOT/'code'/name)],check=True)
print('Saved checkpoints finalized:',ROOT/'out')
