from pathlib import Path
import zipfile,shutil,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/revision35';P=R/'submission/jifmim35/en';D=R/'delivery/R35_distribution';D.mkdir(parents=True,exist_ok=True)
inputs=['reports/revision25/analysis_daily.csv','reports/revision24/deposit_post_state_audit.csv','reports/revision27/owner_day_panel.parquet','reports/revision28/daily_analysis.csv','reports/revision28/all_regressions.csv','reports/revision28/search_family32.csv','reports/revision31/focal_tests.csv','reports/revision32/focal_results.csv']
files=[R/f for f in inputs]+[R/'code/revision35_analysis.py',R/'code/revision35_manuscript.py']+[f for f in O.iterdir() if f.is_file() and not f.name.startswith('._') and f.suffix in {'.json','.csv','.md'}]
with zipfile.ZipFile(D/'R35_distribution_evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in files:z.write(f,str(f.relative_to(R)))
 z.writestr('README.md','''# R35 distribution and functional-form evidence
Run `python code/revision35_analysis.py` from the extracted root with pandas, numpy, scipy, statsmodels and pyarrow installed. It recomputes raw descriptive tables, independently checks interpolated quartiles, reproduces the three original daily models and runs the fixed flow transformations on the same 319 dates. Full coefficients, covariances, caps and all transformed inputs are included. The 12 new focal tests use HAC7; HAC14 is a fixed sensitivity. Holm60 includes the earlier 48-test record. The original R34 evidence archive remains the source for funding and execution replay; these records are not changed by distribution transformations.

The manuscript-generation script additionally expects the previous R34 LaTeX source at submission/jifmim34/en. For compilation alone, use the separate complete R35 source archive.
''')
(D/'R35_修改说明.md').write_text('''# R35 分布、分位数与变换

两张主要描述统计表均补齐N、均值、标准差、Min、P25、P50、P75、Max。分位数由原始样本重算并独立校验，未用缩尾后的数替换原始资金记录。其他账户增加仅针对正额存取款日的分布，避免零值日占比很高时只看到一排零。

94笔匹配存款偏度4.61，日度毛存款和毛提款偏度2.13、2.17；日度净存款含负值且偏度为-1.04。不能把所有流量直接取自然对数。持仓规模和金库资产在原有相应回归中已经使用自然对数。

新做固定的P1/P99缩尾：毛存款和毛提款各影响4个日期，重新计算净额及其滞后，保留319个观察。主要美元净流量系数由0.3771变为0.3578，点态p=0.0024，完整60项探索家族Holm p=0.1419。没有把点态显著等同于所有调整后都显著。

另做ln(1+USDC毛额)和asinh(USDC净额)比较，净额p=0.2106，说明关联对功能形式并非完全稳定。净额不能直接取ln，ln(1+x)和asinh也不能不加区分地解释成百分比效应。原始资金界限和历史提款请求完全不变。

英文正文增加分布说明，附录新增完整功能形式表；主回归仍回答美元净资金问题。没有根据显著性选择变换。本轮仅修改论文，未投稿、付款或确定新的目标期刊。
''')
print(D)
