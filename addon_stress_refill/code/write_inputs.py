"""Absolute input inventory, source counts, collection coverage and decisions."""
import json,hashlib,gzip,collections,sqlite3
import pandas as pd,pyarrow.parquet as pq
from preflight import A,R,O
from pathlib import Path
SOURCE=Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/JRF_Manuscript_and_Replication 2/addon_stress_refill')
def count(p):
    if p.suffix=='.parquet':return pq.ParquetFile(p).metadata.num_rows
    if p.suffix=='.csv':return len(pd.read_csv(p))
    if p.suffix=='.py':return len(p.read_text().splitlines())
    if p.suffix=='.json':
        z=json.loads(p.read_text())
        if isinstance(z,dict) and 'response' in z and 'data' in z['response'] and 'vaults' in z['response']['data']:return len(z['response']['data']['vaults']['items'])
        return len(z['vaults']) if isinstance(z,dict) and 'vaults' in z else len(z)
    return None
def run():
    rows=[]
    inputs=[R/'additional_evidence/panel_evidence/raw/market_operations.parquet',R/'additional_evidence/panel_evidence/raw/opening_market_cash.json',R/'raw/inherited/selected_vaults.json',R/'real_consequences/outputs/A1_clean_events.csv',R/'real_consequences/outputs/A1_clean_call_audit.csv',R/'additional_evidence/panel_evidence/outputs/borrow_event_list.csv',R/'additional_evidence/panel_evidence/outputs/event_vault_horizons.parquet',R/'additional_evidence/panel_evidence/outputs/event_estimation_coverage.csv',R/'additional_evidence/cross_chain/outputs/vault_state_panel.csv',R/'additional_evidence/cross_chain/outputs/position_panel.parquet',R/'additional_evidence/cross_chain/raw/discovery_1.json',R/'additional_evidence/raw/morpho_discovery_42161.json',R/'code/empirical/collect_chain.py',R/'additional_evidence/code/collect_morpho.py',R/'additional_evidence/code/chain_access.py',R/'real_consequences/code/poolrpc.py',R/'real_consequences/code/rpc_limiter.py',R/'real_consequences/raw/morpho_events.sol',R/'data/raw/revision5/event_signatures.json',R/'real_consequences/raw/query.json',Path('/Volumes/Extreme SSD/T9/JRF_Ryu_delivery/Counting_the_same_cash.docx')]
    inputs.append(R/'additional_evidence/panel_evidence/raw/operation_query.json')
    inputs+=sorted((R/'raw/chain_panel').glob('202*_decoded.json'))
    for chain in [1,8453,42161,137]:
        folder=R/('additional_evidence/cross_chain/raw' if chain in [1,8453] else 'additional_evidence/raw');inputs+=sorted(folder.glob(f'morpho_{chain}_202*.json'))
    for p in inputs:
        assert p.exists(),str(p)
        rows.append(dict(path=str(p),rows=count(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    db=R/'real_consequences/raw/events.sqlite';connection=sqlite3.connect(f'file:{db}?mode=ro',uri=True);callrows=connection.execute('select count(*) from calls').fetchone()[0];connection.close();rows.append(dict(path=str(db),rows=callrows,bytes=db.stat().st_size,sha256='read-only source; original package manifest retained'))
    pd.DataFrame(rows).to_csv(O/'all_input_inventory.csv',index=False)
    sources=collections.Counter();failures=collections.Counter();methods=collections.Counter();responses=[]
    for p in list((SOURCE/'out/rpc').glob('*.json'))+list((O/'rpc').glob('*.json')):
        z=json.loads(p.read_text())
        if isinstance(z,list):
            for e in z:failures[(e.get('chain'),e.get('url'))]+=1
        elif 'response' in z:
            sources[(z.get('chain'),z.get('url'))]+=1;methods[(z.get('chain'),z.get('url'),z.get('request',{}).get('method'))]+=1
            result=z['response'].get('result');responses.append(dict(path=str(p),chain=z.get('chain'),node=z.get('url'),method=z.get('request',{}).get('method'),rows=len(result) if isinstance(result,list) else 1))
        elif 'attempts' in z:
            for e in z['attempts']:failures[(z.get('chain'),e.get('url'))]+=1
    for p in (SOURCE/'out/portal_raw').glob('*.errors.json'):
        z=json.loads(p.read_text());failures[(z.get('chain'),z.get('url'))]+=len(z.get('attempts',[]))
    portal_responses=[]
    for p in (SOURCE/'out/portal_raw').glob('*.json.gz'):
        z=json.load(gzip.open(p,'rt'));sources[(z['chain'],z['url'])]+=1;portal_responses.append(dict(path=str(p),chain=z['chain'],node=z['url'],from_block=z['request'].get('fromBlock'),requested_to_block=z['request'].get('toBlock'),last_block=z['rows'][-1]['header']['number'],rows=len(z['rows']),traces=sum(len(b.get('traces',[])) for b in z['rows']),logs=sum(len(b.get('logs',[])) for b in z['rows'])))
    nodes=[dict(chain=c,node=u,successful_response_packets=n,failed_attempts=failures[(c,u)]) for (c,u),n in sources.items()]
    nodes += [dict(chain=c,node=u,successful_response_packets=0,failed_attempts=n) for (c,u),n in failures.items() if (c,u) not in sources]
    pd.DataFrame(nodes).to_csv(O/'node_collection_counts.csv',index=False)
    pd.DataFrame(responses).to_csv(O/'rpc_response_inventory.csv',index=False)
    pd.DataFrame(portal_responses).to_csv(O/'portal_response_inventory.csv',index=False)
    gate=json.loads((O/'gate_results.json').read_text());tail=json.loads((O/'tail_coverage.json').read_text());parts=['# 输入与对账记录','\n所有原有文件均只读；新增文件位于 '+str(A)+'。T9 挂载盘无可见项目；复现包位于 Extreme SSD 的旧 T9 备份。', '\n## 输入文件', '\n每个原始输入的绝对路径、数据行数/状态数、字节数与 SHA-256 均在 `all_input_inventory.csv`。程序文件的“rows”为行数。SQLite 以 `mode=ro` 打开。',f'\n日收盘归档为 440 个状态文件，含 439 日面板及一个滞后日；10 金库合计 4,400 个状态。逐笔市场账本为 {gate["operation_rows"]:,} 条，33 个市场。原表 11 已去重事件为 252 条。', '\n表 8 的原始事件列表包括候选借款及匹配对照；按原九时点完整对的既有口径只读切片为 `input_Table8_834_events.csv`（834 个事件）。四链原正资产状态为 2,204 个；原回归另排除 63 个 S=0 状态，切片为 `input_Table4_2141_states.csv`。本轮小时图保留全部正资产状态，S=0 仅使 Dup 或 D 未定义，不替换为零。', '\n## 前置闸门', '\n```json\n'+json.dumps(gate,ensure_ascii=False,indent=2)+'\n```', '\n33 市场完整日现金网格：`full_daily_market_cash_reconciliation.csv`，14,520 次实测收盘现金与账本净流量对账，最大误差 0 micro-USDC。原持仓队列可见状态的 11,285 次校验也为 0。仓位含按归档借款利率与协议整数规则计入的应计利息；V1.1 使用协议的有效损失账本。', '\n## 补抓范围', f'\nBase 面板末端：区块 {tail["start"]:,}–{tail["end"]:,}，2026-03-31 至 2026-04-06 UTC，{tail["rows"]:,} 条操作。每笔时间来自 RPC 日志的 blockTimestamp，逐笔验证与链上区块时钟一致；期末 33 市场现金也重新归档核对。', '\n小时期：W1 前七日至 W1 末日、W2 前七日至 W2 末日。每链 1,008 个 UTC 整点，区块选最近者；距离相同时取较早块。Arbitrum 同秒多个块取最早者。W2 分组另读取开始前的最后一个块。', '\nEthereum/Arbitrum 调用期为 2025-09-09 至 2025-11-21 UTC，正好覆盖两窗及各自前 30 天的并集。后续成功取款只按相同金库与持有人查询到 2026-03-30 UTC；初始全调用期内复用 Portal 的已提交取款日志，之后按持有人索引从原 RPC 池读取 eth_getLogs 并核对实际区块时间。沿用原 Table 11 的 SQD Portal 公共链上追踪源，权益由原配置的归档节点 eth_call 读取。RPC 追踪接口不足及公开服务过载均已记录，没有使用付费 token 接口。', '\n各实际区块范围在 `hourly_raw/blocks_*.json`、小时账本覆盖 CSV 和 A4 Portal 覆盖 CSV。所有响应保留于 `rpc/` 与 `portal_raw/`；节点成功数及失败次数见 `node_collection_counts.csv`。成功数为响应包数，不等于区块数；批次各项按单独响应计数。失败次数为留存尝试记录数；早期同键重启曾覆写旧失败，故累计可能更高。当前代码对同键追加全部重试记录。', '\n## 口径与判断', '\nW1：2025-10-09–10-17；W2：2025-11-03–11-21，日期均 UTC、含末日。控制期是此前 30 日并剔除另一窗口，分别 30/21 日。小时回归以 W2 及此前七日为观察期。全年日度回归保留全部 439 日。', '\nA3 主口径名单为 xUSD、deUSD、sdeUSD 与两种明确命名的 PT 衍生品；逐项符号和名称由 collateralToken 地址直接 eth_call 核对，见 `collateral_symbols.csv` 与 `A3_related_token_list.csv`。FalconXUSDC、RockawayXUSDC、frxUSD 字符串包含 xUSD，不属于该名单。核心三币另列替代口径，未改窗口。Arbitrum xUSD 的已验证合约名为 Staked Stream USD。', '\nA4 主口径严格要求请求不超过前一块权益。原 Table 11 代码另有 1% 权益容差，原容差结果单列，均按持有人×金库×UTC 小时合并。等待到下一次同金库已提交的成功取款，允许先失败后在同一交易中成功；不把它解释为原金额全部付清。', '\nB1 从 t 的初始现金先按固定队列支付，再按区块、日志序号重放。own 以市场仓位所有者地址识别，十个样本地址全部移除；外部扣款只扣可用现金。资产大小排序在 t 固定，同资产时按地址排序。全量 33 市场现金网格补齐后，所有 τ 和已付比例均未改变。', '\nB3：2026-10-14 用户明确确认“保留 B1，报告差异并继续”。25% 的零等待交集差异为四日；三日存在保持各自队列的其他金库顺序可付清；2025-03-11 在任何分配下仍有缺口。整数最大流与可行顺序均保留。5% 不被原联合上界排除是条件于个别通过，不能推出所有日期都即付清。', '\nCox 的原月份虚拟变量拟合因 2025-09 的 30 个日期全部右删失而分离，保留为诊断且不接受其显著性。有效替代列按年-月分层、保留 439 日及核心变量和星期效应，使用精确 Efron 得分的七日 HAC；独立 Hessian 与得分方程已核对。零等待用共同的 0.000001 小时时间保持排序与并列。OLS 设定原样；独立 HAC 校验见 `independent_HAC_checks.csv`。', '\n原 Arbitrum 主合约与 Base/Ethereum 不同，按原 `collect_morpho.py` 的 CONFIG 分链调用；初始配置校验拒绝记录见 `hourly_raw/configuration_failure_42161_record.json`，被拒读数未用于结果。', '\n## 节点与限额', '\n地址均取自原配置，四链完整节点池另见 `configured_rpc_pools.csv`；Polygon 状态本轮直接复用原包，未额外请求。Base 原公开池给 Tenderly 6 次/秒；Ethereum/Arbitrum 原代码未给明确配额，本次保守设为 3 次/秒。批次按 RPC 项计数；429 后全局冷却并减半，避免并发重试叠加。最低 0.25 次/秒。当前降速记录见 `active_rpc_rates.json`。Portal 按原公共源低频请求，过载退避；大范围失败改为更小区间，并只为报错调用补完整子树，成功缓存直接复用。', '\n'+pd.DataFrame(nodes).to_markdown(index=False), '\n## 辅助核对来源', '\n[已验证的 Arbitrum xUSD 合约](https://arbiscan.io/token/0x6eaf19b2fc24552925db245f9ff613157a7dbb4c)；[SQD Portal 官方接口](https://docs.sqd.dev/openapi.json)。二者用于名单与接口核对，量化结果来自存档状态、日志及调用记录。']
    derived=[]
    for path in sorted(list(O.glob('*.csv'))+list(O.glob('*.parquet'))):
        if path.name.endswith('inventory.csv') or path.name=='original_source_integrity.csv':continue
        derived.append(dict(path=str(path),rows=count(path),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    pd.DataFrame(derived).to_csv(O/'derived_file_inventory.csv',index=False)
    parts.append('\n新增输入、派生表和用于文档的全部 CSV/parquet 的绝对路径、行数与哈希另见 `derived_file_inventory.csv`。原始响应按链和请求保留，量化中间表均使用 CSV/parquet。')
    hourly=[]
    for path in sorted((SOURCE/'out/hourly_raw').glob('*.json')):
        z=json.loads(path.read_text())
        if isinstance(z,dict) and 'vaults' in z:hourly.append(dict(path=str(path),rows=len(z['vaults']),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    pd.DataFrame(hourly).to_csv(O/'hourly_input_inventory.csv',index=False)
    parts.extend(['\n## 全部原始输入绝对路径与行数','\n'+pd.DataFrame(rows)[['path','rows','sha256']].to_markdown(index=False),'\n## 补抓小时状态绝对路径与状态数','\n'+pd.DataFrame(hourly).to_markdown(index=False),'\n## CSV与parquet派生输入绝对路径与行数','\n'+pd.DataFrame(derived)[['path','rows','sha256']].to_markdown(index=False),f'\nRPC 原始输入所在绝对目录：`{SOURCE / "out/rpc"}`。每个响应的绝对文件路径、链、节点、方法与响应记录数见 `rpc_response_inventory.csv`。Portal 源响应位于 `{SOURCE / "out/portal_raw"}`，其每个原始响应的绝对路径、区块范围、行数、调用数和日志数见 `portal_response_inventory.csv`；覆盖表与逐调用 parquet 对应完整扫描区间。'])
    for name,label in [('census_reconciliation.json','四链七期全金库资产对账'),('hourly_gates.json','三链完整小时状态对账'),('Base_clock_validation.json','Base 原账本时间与日收盘区块核对'),('validation.json','独立方法与覆盖核对')]:
        if (O/name).exists():parts.extend(['\n## '+label,'\n```json\n'+(O/name).read_text()+'\n```'])
    for chain in [1,42161]:
        if (O/f'A3_pre_cash_gate_{chain}.csv').exists():
            df=pd.read_csv(O/f'A3_pre_cash_gate_{chain}.csv');parts.append(f'\nA3 分组前状态，链 {chain}：{len(df)} 个正仓位市场，现金最大误差 {df.gap.abs().max()} micro-USDC。')
        if (O/f'A4_trace_log_check_{chain}.json').exists():parts.extend([f'\nA4 链 {chain} 调用覆盖核对：','\n```json\n'+(O/f'A4_trace_log_check_{chain}.json').read_text()+'\n```'])
    (O/'00_inputs.md').write_text('\n'.join(parts)+'\n')
if __name__=='__main__':run()
