"""Check the configured public archive endpoints for historical call traces."""
import json
from hourly import ref,cohort
from rpc import rpc,A
rows=[]
for chain in [1,42161]:
    z=ref(chain);b=z['block'];addresses=[x['address'] for x in cohort(chain,z['timestamp'])]
    for method,params in [('trace_filter',[{'fromBlock':hex(b-20),'toBlock':hex(b),'toAddress':addresses,'count':1000}]),('debug_traceBlockByNumber',[hex(b),{'tracer':'callTracer','timeout':'10s'}])]:
        try:
            r=rpc(chain,method,params,attempts=2);status='PASS';n=len(r)
        except Exception as e:status=str(e);n=None
        rows.append(dict(chain=chain,block=b,method=method,status=status,rows=n));print(rows[-1],flush=True)
(A/'out/trace_probe.json').write_text(json.dumps(rows,indent=2))
