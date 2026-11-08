"""Format frozen numeric CSVs without re-estimating models."""
import panel_evidence_stats as s
import pandas as pd
for prefix in ['task1','task2','task3','task3_cross','task4_daily','task4_all','tasks4_5']:
 f=s.O/f'{prefix}_numeric.csv'
 if not f.exists():continue
 s.ROWS=pd.read_csv(f,float_precision='round_trip').to_dict('records');s.META=pd.read_csv(s.O/f'{prefix}_models.csv',float_precision='round_trip').to_dict('records');p=s.O/f'{prefix}_tests.csv';s.TESTS=pd.read_csv(p,float_precision='round_trip').to_dict('records') if p.exists() and p.stat().st_size>5 else [];s.save(prefix)
