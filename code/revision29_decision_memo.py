from pathlib import Path
import pandas as pd,json,zipfile
R=Path(__file__).resolve().parents[1];O=R/'reports/revision29';D=R/'delivery/JIFMIM29';D.mkdir(exist_ok=True)
p=pd.read_csv(O/'holder_capacity_changes.csv');p=p[(p.named_identity_before=='Ethena')&(p.claim_micro_before>0)]
lines=['# R29：资金补充与其他持有人退出能力——方向检验','', '结论：值得沿这一方向加强论文，但现阶段应定位为可核验的流动性补充案例，不能写成已识别的一般性救助机制或因果效应。','', '## 1. 新增的直接证据','', '严格匹配13,812笔Spark财库存入与共同市场供给，共5,931.328百万USDC；对应交易内市场现金增量可独立核对。完整现金递推与380个历史快照完全一致。此金额是累计毛周转，不是新增净资本，也不是全部已识别的跨链资金。','', '按存款金额超过操作前市场现金这一规则选出全部8笔，共194.183百万USDC。对这些事件查询前一区块和当一区块结束时的直接账户状态，保留区块内其他操作信息。','', '|区块|Spark存入（百万USDC）|Ethena原提款能力|后提款能力|其份额是否不变|','|---|---:|---:|---:|---|']
for r in p.itertuples():lines.append(f'|{r.deposit_block_before}|{r.deposit_micro_before/1e12:.6f}|{r.cap_before/1e6:.6f}|{r.cap_after/1e6:.6f}|是|')
lines+=['','2025年10月4日区块36399032：约48.853百万USDC注资后，Ethena提款能力由约48.357百万增加至61.070百万，恢复到全部持仓。该区块无其他共同市场事件；Ethena份额不变，资产变化仅约0.575 USDC。状态比较仍是相邻区块结束状态，而非完整交易内状态重放。','', '对三组Ethena非零持仓事件，均使用固定的注资前完整持仓金额进行历史只读withdraw调用：第一组前后均返回流动性错误，第二组由流动性错误转为成功，第三组前后均成功。六次结果均保留原始RPC记录，不是实际发送提款交易。','', '## 2. 时间顺序改变经济解释','', '10月4日Ethena在13:39、13:53和13:56 UTC已分别提取30百万USDC。Spark在13:56:43注入18百万，14:16:51再注入48.853百万。不能说这些后来的注资支持了此前已完成的提款。观察更符合提款后的现金补充，后一次注资恢复了剩余持仓的退出选项；是否支持翌日实际提款需要另行识别。这里也未识别操作是自动规则还是自由裁量。','', '## 3. 支付来源与提款能力不是同一结论','', '319个日度资金分配问题中，当天新Spark供给对借款及Spark金库以外市场提款的联合资金贡献下界均为零。即存在由其他现金支付这些交易的可行分配。该结果不能等同于Spark无经济作用，因为日初现金不按历史来源归属，且其他持有人经Spark金库提款不在这一目标集合。','']
f=O/'continuous_lp_summary.json'
if f.exists():
 s=json.loads(f.read_text())
 if s['success']:lines += [f"后续敏感性检验在整个既定研究期连续保留资金来源，不逐日重置。联合下界为{s['lower_usdc']/1e6:.6f}百万USDC，整数端点分配满足现金约束；目标值差异为{s['objective_gap_usdc']:.9f} USDC。这是改变观察边界后的首次资金使用下界，不是可以归因于Spark存在的新增支付，也不应与日度下界混为同一估计对象。",'']
 else:lines += ['连续观察窗口的优化未在本轮计算限制内完成，因此不报告其紧下界。可行分配本身不能被当作最小必要贡献。','']
lines += ['## 4. 对论文的决定','', '建议把新增主证据集中在：实际存入确实增加市场现金；相同份额持有人的提款能力如何随现金补充变化；固定请求在前后历史状态能否执行。原有跨链资金归属作为来源识别模块保留，但不能将这批全部财库操作都重新标为跨链资金。','', '这比仅报告低覆盖率更直接，却尚不足以升级为普遍的新理论。下一阶段如扩展研究，应固定全部大额外部提款的选取规则，再检验后续现金补充的发生与规模，并核实操作规则。不能仅围绕上述成功事件选择样本或规格。','', '本轮未改写既有稿件、未投稿。CSV、代码、原始历史调用和资金分配证据保留于配套档案；研究设计与后续敏感性分别标记。']
(D/'R29_方向检验与修改建议.md').write_text('\n'.join(lines))
with zipfile.ZipFile(D/'R29_direction_evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in O.rglob('*'):
  if f.is_file() and not f.name.startswith('._'):z.write(f,f.relative_to(R))
 for f in (R/'code').glob('revision29_*.py'):z.write(f,f.relative_to(R))
print(D)
