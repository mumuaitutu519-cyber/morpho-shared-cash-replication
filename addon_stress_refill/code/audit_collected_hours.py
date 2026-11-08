"""Early gates for collected hours; never treated as full hourly coverage."""
import json
import pandas as pd
from hourly import H,state,A
from post_hourly import cash_gate
def run():
    results=[]
    for chain in [1,42161]:
        br=json.loads((H/f'blocks_{chain}.json').read_text());positions=[];markets=[];asset_rows=0
        for r in br:
            path=H/f"{chain}_{r['target']}.json"
            if not path.exists():continue
            z=json.loads(path.read_text());mm,vv,pp=state(z);assert max(abs(v['gap']) for v in vv)<=1;asset_rows+=len(vv)
            positions.extend(pp);markets.extend(dict(market=m,cash=v['cash'],block=r['block'],utc=r['utc']) for m,v in mm.items())
        gap=cash_gate(chain,pd.DataFrame(positions),pd.DataFrame(markets));results.append(dict(chain=chain,collected_hours=len({r['utc'] for r in markets}),required_hours=1008,asset_states_checked=asset_rows,cash_gap_max=gap))
    (A/'out/hourly_collection_audit.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2),flush=True)
if __name__=='__main__':run()
