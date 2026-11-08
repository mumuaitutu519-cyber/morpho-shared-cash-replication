# R39 固定样本交付

先读 `R39_试跑报告.md`。

必需输出保持原文件名；历史结果已封样，新增公开字段单独追加，不扩展历史样本。`raw/` 在包根目录，包含继承原始响应、历史空字段链上核验、完整失败响应和首日公开字段。

离线复算（在解压包根目录）：

```sh
python code/r39_shared/analyze.py
python code/r39_shared/figures.py
```

Python依赖：numpy pandas pyarrow requests pycryptodome matplotlib。

采集脚本：`code/r39_shared/collect_public.py`。定时任务已在本机Codex中创建（ID r39），解压包本身不会自动安装调度。日历时刻为首尔14:00，对应UTC05:00。采集日志 `public_liquidity.log`。需本机Codex调度可用和T9挂载。

`shared_cash_results.tex` 是英文结果节片段，使用 graphicx，图片与片段同目录；不是整篇投稿稿件。`joint_execution.csv` 仅表头，表示D未运行，不能引用为已执行证据。

`SHA256.json` 是打包时文件快照。未来C采集追加后对应文件哈希会变化；固定A/B文件不随C更新。
