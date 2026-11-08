from pathlib import Path
import shutil,hashlib,json
A=Path(__file__).resolve().parents[1]
D=Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/addon_stress_refill')
files=['tables.docx', 'RESULT_MEMO_CN.md', 'PASTE_EN.md', '00_inputs.md', 'validation.json', 'all_input_inventory.csv', 'derived_file_inventory.csv', 'hourly_input_inventory.csv', 'rpc_response_inventory.csv', 'portal_response_inventory.csv', 'node_collection_counts.csv', 'A4_independent_header_checks.csv', 'A4_independent_summary_checks.csv', 'A4_header_recovery_status.json']
backup=D/"recovery_archive_20261014"
backup.mkdir(exist_ok=True)
for name in files:
 p=D/"out"/name
 if p.exists() and not (backup/name).exists():shutil.copy2(p,backup/name)
 shutil.copy2(A/"out"/name,p)
 assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((A/"out"/name).read_bytes()).digest()
for name in ["build_outputs.py"]:
 p=D/"code"/name
 if not (backup/name).exists():shutil.copy2(p,backup/name)
 shutil.copy2(A/"code"/name,p)
for p in (A/"out/rpc").glob("*.json"):
 dest=D/"out/rpc"/p.name
 if not dest.exists():shutil.copy2(p,dest)
shutil.copy2(A/"RECOVERY_STATUS.md",D/"RECOVERY_STATUS.md")
print("Final outputs saved and hashes verified:",D/"out")
