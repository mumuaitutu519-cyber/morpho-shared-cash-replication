"""Offline submission audit: existing designs and conditional funding bounds."""
from pathlib import Path
import json
import hashlib
import socket
import sys
import os

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/revision15"
READ_INPUTS=set()

def record_read(event,args):
    if event!="open" or not isinstance(args[0],(str,bytes,os.PathLike)):
        return
    mode=args[1]
    if mode is not None and ("w" in mode or "a" in mode or "+" in mode):
        return
    p=Path(os.fsdecode(args[0])).resolve()
    if p.is_relative_to(ROOT) and p.is_file() and "__pycache__" not in p.parts:
        READ_INPUTS.add(p)

sys.addaudithook(record_read)

def deny_network(*args, **kwargs):
    raise RuntimeError("Revision 15 audit is offline; network access is forbidden.")

socket.create_connection=deny_network
socket.socket.connect=deny_network
socket.socket.connect_ex=deny_network

def main():
    frozen=json.loads((OUT/"frozen_results.json").read_text())["frozen_result_inputs"]
    def hashes():
        return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in frozen}
    assert hashes()==frozen
    import audit_jfs_revision as regression
    regression.OUT=OUT/"regression_replay"
    regression.main()

    import revision6_audit_results as funding
    from revision6_audit_operations import audit as operations
    evidence={
        "capacity":funding.capacity(),
        "completion":funding.completed_routes(),
        "base_market_supply_links":funding.market_supply_links(),
        "routes":{str(d):funding.first_disposition(d) for d in [2,6,10]},
        "facility_operations":{str(d):operations(d) for d in [2,3,6,10]},
    }
    (OUT/"funding_evidence_replay.json").write_text(json.dumps(evidence,indent=2)+"\n")
    assert hashes()==frozen
    inputs={}
    for path in sorted(READ_INPUTS):
        inputs[str(path.relative_to(ROOT))]={
            "bytes":path.stat().st_size,
            "sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    (OUT/"audit_input_manifest.json").write_text(json.dumps(inputs,indent=2)+"\n")
    result={
        "status":"PASS", "network_access_disabled":True,
        "frozen_result_files_unchanged":len(frozen),
        "regressions":"Original sample, outcomes and specifications reproduced",
        "funding":"Original messages, historical balances and first-deposit LP bounds replayed",
        "new_empirical_specifications":0,
        "audited_input_files":len(inputs),
        "audited_input_bytes":sum(p["bytes"] for p in inputs.values()),
        "scope":"Numerical and source consistency, not causal validation or journal acceptance",
    }
    (OUT/"analysis_audit.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    main()
