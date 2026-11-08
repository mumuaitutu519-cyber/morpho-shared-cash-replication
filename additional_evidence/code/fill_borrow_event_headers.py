from pathlib import Path
import pandas as pd,json,concurrent.futures
from panel_archive_rpc import named
A=Path(__file__).resolve().parents[1];P=A/'panel_evidence';O=P/'outputs'
e=pd.read_csv(O/'borrow_event_list.csv');blocks=sorted(e.block.unique());rows=[]
def get(b):
 try:
  h=named(f'block_{b}_header','eth_getBlockByNumber',[hex(int(b)),False]);return dict(block=int(b),hash=h['hash'],timestamp=int(h['timestamp'],16),complete=True)
 except Exception as ex:return dict(block=int(b),complete=False,error=str(ex))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(get,blocks))
pd.DataFrame(rows).to_csv(O/'borrow_event_headers.csv',index=False);print('event headers',len(rows),'complete',sum(x['complete'] for x in rows),flush=True)
