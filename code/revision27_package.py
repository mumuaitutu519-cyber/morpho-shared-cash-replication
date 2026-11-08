"""Portable retained-input update; preserve original raw-funding archive separately."""
from pathlib import Path
import json,zipfile,hashlib,shutil,re
R=Path(__file__).resolve().parents[1];T=R/'submission/jifmim27/en';O=R/'reports/revision27';D=R/'delivery/JIFMIM27';D.mkdir(exist_ok=True)
assert json.loads((O/'fee_residual_summary.json').read_text())['status']=='PASS_RESIDUAL_CLOSED'
shutil.copy2(T/'manuscript.pdf',D/'R27_english_with_appendix.pdf')
shutil.copy2(R/'delivery/JIFMIM26/JIFMIM_GUIDE_CHECK.md',D/'JIFMIM_GUIDE_CHECK.md')
shutil.copy2(R/'reports/revision25/JIFMIM_READING_CN.md',D/'JIFMIM_READING_CN.md')
shutil.copy2(O/'FINAL_REVIEW_CN.md',D/'FINAL_REVIEW_CN.md')
source={str(p.relative_to(T)):p for p in T.rglob('*') if p.is_file() and not any(v.startswith('.') for v in p.relative_to(T).parts) and 'build' not in p.relative_to(T).parts and p.suffix in ['.tex','.bib','.pdf','.json','.md'] and p.name!='manuscript.pdf'}
with zipfile.ZipFile(D/'R27_LaTeX_source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n,p in sorted(source.items()):z.write(p,n)
 z.writestr('README_R27.md','Compile manuscript.tex with XeLaTeX/latexmk. Main text and appendices are included. Tables retain genuine inference and the full test-family results are preserved in Appendix F. Times New Roman is required. No author identity or public submission has been added.\n')
files={str(p.relative_to(R)):p for p in O.iterdir() if p.is_file() and not p.name.startswith('.') and p.suffix in ['.csv','.json','.parquet','.md','.log']}
files.update({str(p.relative_to(R)):p for p in (O/'raw').iterdir() if p.is_file() and not p.name.startswith('.')})
files.update({str(p.relative_to(R)):p for p in (R/'code').glob('revision27_*.py') if not p.name.startswith('.')})
for n in json.loads((O/'fee_source_manifest.json').read_text()):files[n]=R/n
for n in ['reports/revision6/domain_6_receipts.json','reports/revision21/daily_flow_stock_reconciliation.csv','reports/revision22/fee_residual_daily_audit.csv','data/raw/revision5/metamorpho_MetaMorpho.sol']:
 files[n]=R/n
for item in json.loads((R/'reports/revision6/domain_6_receipts.json').read_text())['items']:
 for key in ['file','header_file']:
  files[item[key]]=R/item[key]
for p in (R/'data/raw/revision22/fees').iterdir():
 if p.is_file() and not p.name.startswith('.'):files[str(p.relative_to(R))]=p
for name in ['sqd_fee_probe.body','sqd_fee_probe.json']:
 p=R/'data/raw/revision22'/name
 if p.exists():files[str(p.relative_to(R))]=p
base=R/'delivery/JIFMIM26/R26_evidence_update.zip';manifest={}
with zipfile.ZipFile(base) as prior,zipfile.ZipFile(D/'R27_evidence_update.zip','w',zipfile.ZIP_DEFLATED) as z:
 for n in prior.namelist():
  if n in files or n=='README.md':continue
  data=prior.read(n);z.writestr(n,data);manifest[n]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 for n,p in sorted(files.items()):
  assert p.exists(),n
  data=p.read_bytes();z.writestr(n,data);manifest[n]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 readme='''# R27 retained-input evidence update
This includes the R26 owner/rate inputs and the R27 exact-claim, second-account and raw-fee update. Original 94-deposit funding witnesses, historical request records and earlier full reconstruction remain in R24_reviewer_evidence.zip (delivery/JIFMIM24); this is explicitly an update, not a replacement for that original archive.

Offline runs from the extracted root, Python with pandas, numpy, scipy, statsmodels, pyarrow, requests and pycryptodome:
1. python code/revision27_audit_fees.py
2. python code/revision27_ethena_funding.py
3. python code/revision27_owner_audit.py
4. python code/revision27_verify_closed_shares.py
5. python code/revision27_build_panel.py
6. python code/revision27_estimate.py
Existing raw Ethena boundary responses prevent new network calls in step 2. The baseline R26 owner panel is retained as the non-claim-variable input to step 5; R26 scripts can rebuild it separately. Scripts ending collect*, exits, states or checks are network collection/validation routes and are not needed to rerun the above estimates. Revision27 presentation editing scripts operate on a separate manuscript tree and are not part of empirical replay.

Complete raw log ranges are defined by fee_census_coverage.json and ethena_log_coverage.json. Error responses and preliminary probes are archived for provenance, never counted as complete coverage or withdrawal failures. The fee census covers all 170 initially discrepant dates, not every date in the chain's history. Owner addresses are not assumed to represent independent people. The second account has an observed ordinary wallet funding path, not a second CCTP cohort.

Raw fee-pair classification, direct holdings/claims, and cash/execution results are separate validations. The main manuscript focuses on supported findings; the complete explored regression family and controls remain unchanged. No journal PDFs, personal credentials, public posting or submission are included.
'''
 z.writestr('README.md',readme);z.writestr('R27_INPUT_MANIFEST.json',json.dumps(manifest,indent=2))
for name in ['R27_LaTeX_source.zip','R27_evidence_update.zip']:
 with zipfile.ZipFile(D/name) as z:assert z.testzip() is None
(D/'README_CN.md').write_text('''# R27交付

R27_english_with_appendix.pdf：英文正文与附录合并件。正文聚焦有支持的资金归属、提款规模差异、财库净资金投入和实际支付证据；整组探索回归移入附录，未筛选删改原模型控制变量或重新定义显著性检验家族。

R27_LaTeX_source.zip：可编辑英文源文件，用XeLaTeX编译manuscript.tex。
R27_evidence_update.zip：R26输入加R27新增原始费用日志、Ethena资金链、准确份额转换和全部回归输出。原94笔资金优化与执行记录仍见delivery/JIFMIM24/R24_reviewer_evidence.zip。没有将增量包称为全部旧记录的替代。

本轮未投稿、未付款、未公开上传数据。JIFMIM官方要求125美元投稿费，与先前免费偏好不同。作者信息、声明和公共数据安排仍需由作者落实；研究结论不保证期刊录用。
''')
manifest2={p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in D.iterdir() if p.is_file() and not p.name.startswith('.') and p.name!='manifest.json'}
(D/'manifest.json').write_text(json.dumps(manifest2,indent=2));print(json.dumps(manifest2,indent=2))
