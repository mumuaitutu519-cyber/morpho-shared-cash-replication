from pathlib import Path
import json,pandas as pd,datetime,hashlib
ROOT=Path(__file__).resolve().parents[2];O=ROOT/'outputs';v=json.loads((O/'validation.json').read_text());k=pd.read_csv(O/'k_curve.csv');d=pd.read_csv(O/'market_totals_daily.csv');m=pd.read_csv(O/'market_decomposition.csv');a=pd.read_csv(O/'historical_missing_field_audit.csv');fail=pd.read_csv(O/'api_failures.csv');c=pd.read_csv(O/'public_liquidity_daily.csv');cv=pd.read_csv(O/'public_liquidity_by_vault.csv');vaults=json.loads((ROOT/'raw/inherited/selected_vaults.json').read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def pct(x):return f'{100*x:.2f}%'
def tab(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)
kt=k.pivot(index='k',columns='group',values='duplication_ratio_median');kd=pd.read_csv(O/'k_curve_daily.csv');kp=kd[kd.group.eq('all')].pivot(index='date',columns='k',values='median');gain=(kp[10]-kp[8]).median()*100
failcounts=fail.groupby('error').size();cashrows=[]
for _,r in m.iterrows():cashrows.append([int(r['rank']),r['name']+' '+r['market'][2:10],pct(r.cash_share_median),pct(r.duplication_share_median),pct(r.within_market_duplication_ratio_median),f'{r.positive_vaults_median:g}',f'{r.cash_million_usdc_median:.6f}',int(r.n_within_market_ratio_days)])
text=f'''# R39 共享现金试跑结果

生成时间：{now}。A、B 已完成；C 已完成首日采集并启动定时运行，未来序列尚待积累。D 未执行。历史分析封样为 2025-01-16—2025-11-30 的319个日收盘、固定10个金库、31个市场。

## 主要结果及写作判断

1. 全样本逐日重复率的中位数为 **{pct(v['median_duplication_ratio'])}**。cbBTC/USDC（9103c3…）的现金份额中位数为 **{pct(v['cbbtc_cash_share_median'])}**，重复份额中位数为 **{pct(v['cbbtc_duplication_share_median'])}**。两种份额**逐日相减后**的中位差为 **{v['cbbtc_daily_difference_median']*100:.2f}个百分点**。因此，重复金额集中确实存在，但现金本来就高度集中；不能仅凭98.50%宣称异常的重复集中。
2. 固定剔除该 cbBTC/USDC 市场后，逐日重复率中位数为 **{pct(v['exclude_cbbtc_median'])}**。每日剔除重复金额最大市场的结果同为 **{pct(v['exclude_largest_median'])}**，因为319天的最大市场均是同一个 cbBTC/USDC 市场。两项检验在本样本没有形成不同的删减。
3. 穷举后的8金库主口径为 **{pct(kt.loc[8,'all'])}**，9金库为 **{pct(kt.loc[9,'all'])}**，10金库为 **{pct(kt.loc[10,'all'])}**。k=10与k=8的日度统计量先相减、再取中位数，增加 **{gain:.2f}个百分点**。此前58.83%是某一个固定8金库组合，不能代替全部45个8金库子集的结果。因此不采用“k=8后基本不动”作为已证明的结论。
4. k=8时，含Spark子集为 **{pct(kt.loc[8,'with_spark'])}**，不含Spark子集为 **{pct(kt.loc[8,'without_spark'])}**；不含Spark的全部9个金库为 **{pct(kt.loc[9,'without_spark'])}**。结果说明问题也存在于其他金库之间，但规模依赖组合构成，不能写成“与选哪些金库无关”。

建议主线：**同一市场现金被多个金库的单体现金指标同时计入，组合可用现金需要按市场重新合并。** 引言同时呈现现金集中和头寸重叠。历史结果的对象是重建单体现金基准，不能称为已经测得“全行业披露夸大比例”。

## A：计算路径与市场分解

对每个日期、每个市场，先计算 S_m=Σ_v min(P_vm,M_m)、J_m=min(Σ_v P_vm,M_m)、D_m=S_m−J_m，再计算市场现金份额、重复份额和D_m/S_m。所有表中中位数均对日度量汇总，金额以百万USDC表示。M来自全部固定31个市场的现金，包括当日这10个金库没有头寸的市场；并非只用正头寸面板中的现金。

- 现金HHI：每日Σ_m现金份额²，319天中位数 **{v['cash_hhi_median']:.6f}**。
- 重复HHI：每日Σ_m重复份额²，319天中位数 **{v['duplication_hhi_median']:.6f}**。
- 三项总量恒等式最大偏差：S为0、J为0、D为0微USDC；所有D_m≥0。
- 与上一轮10金库日度S、J逐日核对：最大差额均为0 USDC。
- 固定删除只删除完整市场ID `0x9103c3b4e834476c9a62ea009ba2c884ee42e94e6e314a26f04d312434191836`，不删除其他同名抵押品市场。
- S_m=0时D_m/S_m未定义，留空，不作为0纳入中位数；各市场有效天数见末列。现金份额、重复份额、正头寸金库数和现金水平均有319天。

{tab(['序','市场／ID前缀','现金份额','重复份额','市场内重复率','正头寸金库数','现金百万USDC','市场内比率有效天数'],cashrows)}

图 `fig_market_shares.pdf` 按重复份额中位数排序。中位数相同的市场用完整market ID升序打破并列，不根据结果再选其他市场。

## B：全部子集曲线

严格枚举掩码0—1023，即1024个集合；其中空集1个、非空子集1023个。k=1—10对应1023个非空子集，不是1024个非空子集。空集没有重复率。

主线：每一天先对该组子集重复率取中位数，再对319天取中位数。P10、P90及图中阴影：每一天先对该组子集取P10、P90，再分别对319天取中位数，反映子集构成差异，不是置信区间。CSV另外提供 `time_p10_of_daily_medians`、`time_p90_of_daily_medians`，即日度子集中位数的时间分布分位数，避免混淆两种离散程度。所有分位数使用NumPy默认线性分位数规则。

{tab(['k','全部子集数','全部','含Spark','不含Spark'],[[i,int(k[(k.k==i)&(k.group=='all')].subset_count.iloc[0]),pct(kt.loc[i,'all']),pct(kt.loc[i,'with_spark']),pct(kt.loc[i,'without_spark']) if pd.notna(kt.loc[i,'without_spark']) else '不适用：无此子集'] for i in range(1,11)])}

k=1所有S>0的子集日期重复率严格为0。S=0的子集日期留空，逐日有效子集数在 `k_curve_daily.csv`。`subset_manifest.csv` 给出每个掩码的完整金库地址；`subset_daily_ratios.npz` 保留每个子集、每一天的重复率。

## 原始缺口、失败与最终覆盖

历史GraphQL空值或未列示头寸未直接赋零。本轮对79,130个字段执行历史区块只读核验：511个市场现金字段、78,619个金库—市场头寸字段。511个现金状态实际返回供给与借款均为0；78,619个位置实际返回供给份额为0。它们据此记为观察到的零，原始GraphQL空值和链上返回分别保留。最终319天×10金库×31市场没有未解决状态，A/B剔除日期0天、未识别金额0（就上述固定字段而言）。这不代表对GraphQL所有非空字段重新进行了一遍独立链上估值。

接口失败明细见 `api_failures.csv`：dRPC限流254次；PublicNode要求历史请求个人令牌112次。PublicNode在识别到权限要求后停止，未获取令牌或绕过访问限制；停止时最多2个在途请求可能没有形成可保存的最终响应，另见 `collection_interruptions.json`。改用既有公开Tenderly端点后，所有剩余历史字段取得有效返回。失败没有被成功结果覆盖，366份已记录失败响应均保留在raw中。最终完整状态不意味着此前没有接口失败。

所有日期的区块高度见 `raw/inherited/withdrawal_capacity.csv`，历史GraphQL的x为次日00:00 UTC，对应前一日收盘；RPC使用该收盘最后一个区块。市场以Base链、原生USDC地址和完整market ID匹配。同名抵押品不合并。

## C：公开字段每日采集

已设置Codex定时任务 `r39`，每日 **UTC 05:00／首尔14:00**。脚本为 `code/r39_shared/collect_public.py`；运行需要Codex本机调度可用、T9挂载及网络可达。今日首份采集时间为 {c.iloc[0].collection_utc}，此后固定时刻运行。历史A/B不会随正向采集扩展。

- 今日GraphQL公开 underlying 合计：{c.iloc[0].graphql_public_sum_usdc:,.6f} USDC。
- 今日REST withdrawable_assets 合计：{c.iloc[0].rest_public_sum_usdc:,.6f} USDC。两个接口分别加总，不拼接填补；对应数据区块并不完全一致。
- 今日联合上界、差额和差额比例：**缺失**。Extrafi已报totalAssets与公开市场头寸相差 **433,208.022341 USDC**，涉及1金库、1采集日。该数是未对账资产，不是已证明的遗漏现金。当天十金库联合比较被剔除，其他公开字段原样保留。
- 每金库的state.timestamp、state.blockNumber、REST last_indexed_block分别保存。GraphQL状态时间不是统一的当前时间；REST接口只返回索引区块，没有另行伪造updatedAt。
- HTTP/GraphQL失败或必需字段缺失会记录每次响应并重试一次；仍失败则标为缺失。输入已返回但资产对账失败另记为质量缺口。今日接口失败0次，但存在上述质量缺口。
- 同日重复运行已验证不增加CSV行或覆盖原始响应。当天首次采集记录保持不变；不拿之后的不同状态冒充同一固定时点。
- 每次运行日志打印公开合计、J和差额比例；缺失会显示null或空字段。

## 公开展示检索

在Morho官方金库列表（https://app.morpho.org/vaults）关闭仅V2、筛选Base和USDC后，实际看到Gauntlet USDC Prime、Spark USDC Vault、Steakhouse USDC等金库的Liquidity并列显示。截图与DOM记录在 `raw/display_evidence/`，访问日期2026-09-08，逐份记录UTC时间和网址。截图中页面顶部加总的是 **Total Deposits**，不能写成Total Liquidity。

已找到并列展示；本轮检索**未找到已核实的、将这固定10个金库可提款字段直接加总的站点或管理人报告**。LiqPilot页面宣称可比较流动性，但访问所得是等待数据状态，不作为实际加总证据。“未找到”不表示“不存在”。这项定向检索在找到直接并列展示后收束，未声称穷尽所有网页。

## D：未执行的可选项

本机PATH、`/Users/sunhan/.foundry/bin/anvil`、`/opt/homebrew/bin/anvil`均未找到anvil；固定日期各金库最大持有人的历史权益也尚未核验。因此本轮没有进行联合提款执行，未生成模拟成功记录。`joint_execution.csv`只有规定表头，0条执行记录；`joint_execution_status.json`明确标记未运行。没有把S、J的会计核算当作执行证明。

## 复算与封样

- 只复算A/B：在包根目录运行 `python code/r39_shared/analyze.py`，再运行 `python code/r39_shared/figures.py`。依赖numpy、pandas、pyarrow、requests、pycryptodome、matplotlib；这两步不重新访问网络。
- 当天C采集：`python code/r39_shared/collect_public.py`；CSV按UTC日期幂等，失败日志保留。
- `input_manifest.json`保存继承文件原位置和SHA256；raw/inherited为原样归档，包括来源接口原有UTC采集时间。历史响应中更长的保留序列仅作为原始档案，本轮只读取指定319天。
- `market_decomposition_daily.csv`、`market_totals_daily.csv`和`k_curve_daily.csv`保存日度分子、分母或聚合路径；每个市场完整ID、金库完整地址可追溯。
- `shared_cash_results.tex`为据本轮结果开始撰写的英文主线段落，尚非整篇新稿。全文后续整合以共享现金为主线；日度利用率回归及其旧附录不进入该主线稿，本轮没有新增或恢复这些分析。
- 固定窗口、10金库集合与31市场清单写入 `sample_freeze.json`。后续新想法仅记录，不执行。
'''
(O/'R39_试跑报告.md').write_text(text.replace('Morho','Morpho'))
freeze={'frozen_at_utc':now,'start_date':'2025-01-16','end_date':'2025-11-30','n_days':319,'chain_id':8453,'asset':vaults[0]['asset']['address'],'selection':'top 10 historical totalAssets at 2025-01-16 close in the previously fixed Morpho GraphQL Base native USDC V1 universe','vaults':[{'address':x['address'],'name':x['name'],'baseline_assets':x['baseline_assets']} for x in vaults],'markets':sorted(m.market.tolist()),'excluded_dates':[],'future_public_collection_is_separate':True,'prohibited_extensions':['new regressions','Ethena tests','new vaults','longer historical window']};(O/'sample_freeze.json').write_text(json.dumps(freeze,indent=2))
tex=r'''\section{Shared market cash and portfolio liquidity}
The sum of vault-level cash measures counts the same market cash more than once when several vaults supply to that market. We quantify this overlap for the ten Base native-USDC V1 vaults with the largest historical assets at the 16 January 2025 close. The fixed sample contains 319 daily closing states through 30 November 2025 and 31 underlying markets.

For market $m$ on date $t$, cash is $M_{m,t}=\mathrm{SupplyAssets}_{m,t}-\mathrm{BorrowAssets}_{m,t}$, and $P_{vm,t}$ denotes vault $v$'s supply position. We compare the sum of standalone cash measures, $S_t=\sum_{v,m}\min(P_{vm,t},M_{m,t})$, with the joint cash upper bound, $J_t=\sum_m\min(\sum_vP_{vm,t},M_{m,t})$. The duplication rate is $(S_t-J_t)/S_t$ for $S_t>0$. Market identity is specific to the chain, loan asset, and market identifier.

The median daily duplication rate is 58.19\%. The cbBTC/USDC market accounts for a median 98.50\% of duplicated cash and 94.41\% of market cash. The median daily difference between these shares is 3.13 percentage points. Thus, the concentration of duplication accompanies a highly concentrated cash base. Daily cash-share and duplication-share Herfindahl indices have medians of 0.8928 and 0.9703, respectively. Excluding this market leaves a median duplication rate of 32.09\%. Excluding each day's largest contributor gives the same result because cbBTC/USDC is the largest contributor on every sample date.

\begin{figure}[htbp]\centering
\includegraphics[width=\linewidth]{fig_market_shares.pdf}
\caption{Market cash shares and duplication shares}
\label{fig:marketshares}
\par\small\textit{Notes:} Each bar is the time median of a daily share in the fixed ten-vault sample. Markets are ranked by their median duplication share; market-ID order resolves ties. Market cash includes cash held in the fixed markets even on dates when the selected vaults have no position.\end{figure}

To assess dependence on vault composition, we enumerate all 1,023 nonempty subsets of the fixed ten-vault universe. For each subset size and date, we take the median duplication rate across subsets, and then take the time median. This statistic is 52.86\% for eight vaults, 56.86\% for nine vaults, and 58.19\% for all ten. The median daily increase between the ten- and eight-vault statistics is 4.63 percentage points. For eight-vault subsets, the corresponding median is 55.19\% when Spark is included and 31.72\% when it is excluded. The complete nine-vault portfolio excluding Spark has a median duplication rate of 34.47\%. Shared-cash overlap therefore extends beyond Spark, while its magnitude remains sensitive to portfolio composition.

\begin{figure}[htbp]\centering
\includegraphics[width=.95\linewidth]{fig_k_curve.pdf}
\caption{Duplication rates across all vault subsets}
\label{fig:kcurve}
\par\small\textit{Notes:} Lines show the time median of daily within-group subset medians. Shaded bands show the time medians of daily within-group P10 and P90 values. The grouping indicates whether a subset includes Spark. Only subsets with positive standalone cash enter the daily distribution. No ten-vault subset excludes Spark. These bands describe subset dispersion.\end{figure}
'''
(O/'shared_cash_results.tex').write_text(tex)
print('report and manuscript section written')
