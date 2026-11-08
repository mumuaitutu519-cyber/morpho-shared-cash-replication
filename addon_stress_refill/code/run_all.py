"""One-command replay. Completed chain reads are reused from the add-on cache."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(__file__).resolve().parents[1]
def script(name):
    print('RUN',name,flush=True)
    subprocess.run([sys.executable,str(ROOT/'code'/name)],check=True)
def run():
    for name in ['preflight.py','daily_market_gate.py','extract_reference_inputs.py','collect_tail.py']:
        script(name)
    script('write_inputs.py')
    import analyze,base_errors
    analyze.a1();base_errors.run();analyze.a1(write_base=False)
    analyze.b1()
    for name in ['diagnose_b3.py','censor_model.py','hourly.py','pre_w2.py','hourly_ledger.py','token_list.py','post_hourly.py','portal_errors.py','verify_call_headers.py','validate_results.py','provenance_audit.py','write_inputs.py','build_outputs.py']:
        script(name)
    print('All requested analyses and source files rebuilt:',ROOT/'out',flush=True)
if __name__=='__main__':run()
