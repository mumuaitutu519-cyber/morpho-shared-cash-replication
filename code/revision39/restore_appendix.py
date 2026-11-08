from pathlib import Path
import shutil,zipfile
src=Path('submission/revision38_user/R38_CN');dst=Path('submission/revision38B_pilot/zh');dst.parent.mkdir(parents=True,exist_ok=True)
shutil.copytree(src,dst,dirs_exist_ok=True)
for name in ['scaled_flows','flow_transformations']:
 shutil.copy2(Path('submission/revision37/zh/tables')/(name+'.tex'),dst/'tables'/(name+'.tex'))
a=(dst/'appendix.tex').read_text();anchor=r'\section{分布与资金流变换}'
insert=r'''\section{按期初权益标准化的财库流量}\label{app:scaled39}
为区分金额关系与比例调整，表\ref{tab:scaledflows}将日度存入、提取及净额分别除以前一日财库权益并乘100。样本仍为319天，解释变量、月份和星期效应与金额模型相同。净流量利用率系数为0.090，逐项$p$值约0.584；这一标准化关系不精确。金额结果不能据此解释为稳定的比例调整规则。
\input{tables/scaled_flows}

'''
# Use precise archived p, not a t-rounded approximation.
import pandas as pd
r=pd.read_csv('reports/revision28/all_regressions.csv');p=float(r[(r.model=='net_rate_HAC7')&(r.term=='utilization')].p.iloc[0]);insert=insert.replace('0.584',f'{p:.3f}')
a=a.replace(anchor,insert+anchor)
anchor=r'\input{tables/flow_transformations}'
extra=r'''第二种函数形式使用以USDC计的$\ln(1+x)$表示非负毛流量，使用$\operatorname{asinh}(x)$表示有符号净流量及其滞后。它保留零值和负值，系数单位不同于百万USDC金额模型。净流量利用率系数为0.1227，逐项$p=0.2106$；因此，原金额关系对流量表示方式敏感。表中同时保留原始、缩尾和非线性规格，以及新增检验族的调整结果。
'''
a=a.replace(anchor,extra+'\n'+anchor)
(dst/'appendix.tex').write_text(a)
# This is an appendix-restoration copy of the user's R38, not a claimed final main-text rewrite.
(dst/'本轮修改说明.md').write_text('''# R38附录恢复版\n\n以用户上传R38_CN为底稿；正文保留原样。\n恢复按期初权益比例的流量表，恢复非线性变换表C组，并补充统计含义。原始、缩尾、非线性及不显著结果一并保留。\n本轮新跑的共享现金、反馈和Ethena等待结果见独立试跑报告，尚未据此全面重写正文；该源文件不是最终投稿稿。\n所有用户原始文件原封保存在 submission/revision38_user。\n''')
print('restored net-rate p',p)
