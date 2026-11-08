from pathlib import Path
import pandas as pd,sqlite3,json,hashlib
A=Path(__file__).resolve().parents[1];R=A.parent;db=R/'real_consequences/raw/events.sqlite';con=sqlite3.connect(f'file:{db}?mode=ro',uri=True)
q="select date,block,tx,logindex,event,assets_raw from logs where vault=? and event in ('Deposit','Withdraw') order by block,logindex"
z=pd.read_sql_query(q,con,params=['0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a']);assert not z.duplicated(['tx','logindex']).any();p=A/'raw/spark_committed_flows.csv.gz';z.to_csv(p,index=False,compression={'method':'gzip','mtime':0})
(A/'raw/spark_flow_provenance.json').write_text(json.dumps({'source_database':str(db),'query':q,'vault':'0x7bfa7c4f149e7415b73bdedfe609237e29cbf34a','rows':len(z),'first':z.date.min(),'last':z.date.max(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2));print(len(z))
