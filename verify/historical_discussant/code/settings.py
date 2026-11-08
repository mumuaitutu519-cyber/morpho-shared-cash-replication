from pathlib import Path
import os

OUT = Path(__file__).resolve().parents[1]
PROJECT = OUT.parents[1]
R = Path(os.environ.get('COUNTING_REPLICATION_ROOT', '/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/Replication_Package'))
ADD = PROJECT / 'addon_stress_refill/out'
PE = R / 'additional_evidence/panel_evidence/outputs'
RAW = R / 'additional_evidence/panel_evidence/raw'
MANUSCRIPT = Path(os.environ.get('COUNTING_MANUSCRIPT', '/Users/sunhan/Library/Group Containers/group.com.apple.coreservices.useractivityd/shared-pasteboard/items/261E3B88-F105-451A-8115-D57556AD7038/WKZhangKangRyuSun_Zhang_111_Sun.docx'))
for name in ['data', 'tables', 'logs', 'package']:
    (OUT/name).mkdir(exist_ok=True, parents=True)
