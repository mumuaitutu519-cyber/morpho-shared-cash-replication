# R25：相关文献与表图改造记录

本轮以 JIFMIM 的稳定币、链上借贷、去中心化交易与流动性论文为重点，结合此前用户提供的正式论文。已取得下面五份 PDF，另通过汉阳大学浏览器打开一篇出版商全文。这里记录的是具体核对的文献和借鉴内容，不宣称穷尽该刊所有相关论文，也不将题录或摘要访问计为全文下载。

## 本轮重点文献

| 文献 | 取得情况 | 表图与研究组织中可借鉴的内容 | 本文如何采用 |
|---|---|---|---|
| Saengchote (2023), *Decentralized lending and its users: Insights from Compound* | 用户提供的35页正式PDF已纳入阅读目录 | 先解释借贷制度、利率与参与者，再呈现描述统计、净存款回归与用户分组；附录A1按地址类型组织回归。回归表逐列列出模型，括号内报告Newey–West标准误。 | 将日度净存款、净市场供给放回正文，区分财库账户与整个金库。本文采用已确定的市场预测变量，不虚构COMP激励或直接照搬其控制变量。 |
| Aspris et al. (2026), *Is decentralized always better? How market structure affects trading costs for tokenized assets* | 大学仓库正式PDF，20页 | 第7–8页表1和表3按场所并列均值、中位数和SD；表2/5并列模型和括号内误差；第12页图2呈现交易规模分布。交易规模在经济解释中承担实质作用。 | 描述统计先行；并列4个资金配置模型；用请求规模比较退出能力。其交易成本结果不等同于本文的合约提款结果。 |
| Sakkas & Urquhart (2024), *Blockchain factors* | 大学仓库正式PDF，含封面14页 | 将链上变量转成明确的金融测量对象，再组织因子和资产定价结果，而不是以记录数量作为贡献。 | 文献定位说明链上数据与资金来源/提款能力的区别；不为增加回归数量而加做无关的收益因子模型。 |
| Yousaf, Abrar & Yarovaya (2023), *Decentralized and centralized exchanges: Which digital tokens pose a greater contagion risk?* | 大学仓库正式PDF | 第6页表1按DEX、CEX及其他资产分Panel报告描述统计；图1采用小多图；后续表格对应连通性问题。 | 本文描述统计按存款事件、账户日和市场日分Panel；引用时明确其收益连通性不同于共享现金。没有把TVP-VAR套进只有一个机构的资金队列。 |
| Huang (2024), *Liquidity dynamics between virtual and equity markets* | 大学仓库正式PDF | 表3/4按深度、紧度和韧性以及市场展开结果；图1–3分别展示不同流动性维度。 | 明确持仓、提款现金、覆盖率、净资金流各自的金融含义；绘图时分别展示水平和比例，避免混作一个“流动性”。 |
| Palazzi, Schich & de Genaro (2025), *Stablecoins as anchors?* | 汉阳大学Chrome配置下的ScienceDirect全文可读；PDF入口未成功得到有效PDF，未把验证HTML算作PDF | 全文按文献、概念框架、数据、方法和结果组织，含资产描述与动态关系分析。 | 加入稳定币信息流的期刊内定位；不将价格相关性或信息流证据当作财库退出约束的证据。 |

## PDF目录与定位

本地PDF：`reports/revision25/jifmim_reading/pdfs/`。

- Compound：https://doi.org/10.1016/j.intfin.2023.101807
- Aspris等：https://doi.org/10.1016/j.intfin.2026.102302
- Blockchain factors：https://doi.org/10.1016/j.intfin.2024.102012
- DEX/CEX contagion：https://doi.org/10.1016/j.intfin.2023.101881
- Liquidity dynamics：https://doi.org/10.1016/j.intfin.2023.101917
- Stablecoins as anchors：https://doi.org/10.1016/j.intfin.2024.102108

此前用户提供的其他JIFMIM论文及代表性表图截图保存在 `reports/jifmim_visual_review/`。Editorial Board是编委信息，不作为研究文章对标。

## 实际改动

1. 正文表1：94笔存款、319个账户日和319个市场日的N、均值、标准差、中位数、最小值、最大值。
2. 正文表2：资金归属结果集中在一张表中，附上各组资金规模；可行上下界保留，不把它称为统计置信区间。
3. 正文表3：原有金库配置方程复算，再并列无日历控制、HAC带宽比较及账户净存款扩展。系数三位小数，括号内稳健统计量两位。完整标准误、p值、Holm调整与协方差保留在复现数据。
4. 正文表4–6：提款尺度、8日毛/净提款、共享现金与规模比较。
5. 正文图1–5：月度毛/净资金流、持仓与提款能力时间序列、按事件/金额的归属构成、存款规模与退出能力、4月8日日内现金过程。删除原正文资金上下界须状图。
6. 核心附录压缩为5个模块：资金约束、账户对账、提款与日内现金、共享市场、回归诊断和复现。旧版全部探索材料另存，弱结果不删除。
7. 参考文献共28项：24篇期刊论文与4项制度/合约原始资料；其中6篇来自JIFMIM。学术引文优先采用JF/JFE/RFS/JPE/ROF/JFQA及目标期刊等来源，没有用无关文献凑数量。DOI元数据保留供核对。AJG等级不在稿件中作未经官方核验的断言。

## 结果边界

排版和证据组织已实质修改，但没有制造更显著的结果。原有金库回归仍不支持精确的系统性补充流动性结论；账户扩展中利用率的Holm值为0.0502，不写成5%显著。存款等额历史调用的94次成功是原有证据重新组织呈现，不宣称本轮重新独立采集了94次历史状态。独立机构跨链融资队列仍未验证出来。
