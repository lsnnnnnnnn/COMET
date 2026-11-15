# 尚未抽样的服务器补充实验迁移

本方案只迁移 ANCHORS 1,600 units 和 negative controls 100 units。E1–E5 留在本机原环境，E0/C-STAT 新抽样仍为 0。此次子任务没有 SSH、服务器抽样、协议冻结或结果同步操作。主进程提供的服务器为 `shengen@10.200.13.23`，工作目录拟用 `/data1/shengen/COMET_POST_CSTAT_20261115`，Python 3.12.3 / NumPy 1.26.4 / Linux x86_64，tmux 可用；这些信息未由本子任务远程复核。

本机只读检查时，旧 `ANCHORS_protocol.json` 的 fingerprint 为 `44440532c1238832e2d356967d96ab9e6aabc7282b7d7355e988e8fb4ab6cfb6`，有 1,600 个 planned IDs、0 checkpoint；旧 `negative_controls_protocol.json` 的 fingerprint 为 `43dedc67e060653d60b7b96f7032633c29b4e06882df5473ec4d9a19b314cdf9`，有 100 个 planned IDs、0 checkpoint。启动服务器前应再次核对该零抽样状态，并将旧 freeze 明确登记为 **superseded before any draw**，保留文件原样。

## 新服务器协议

1. 使用同一份已提交科学源，在仓库内新增 `configs/post_cstat/ANCHORS_server_v1.json`、`negative_controls_server_v1.json`。保留 DGP、阈值、gap、sample size、全部方法/levels、grid、种子/domain、planned IDs 和 raw-debug IDs；更新实际服务器 `production_environment` 并记录原协议 fingerprint、迁移动机与零旧 outcome 事实。两个方案只使用同一批 1,700 个已预算单位。
2. 在服务器实际运行 `environment_signature()` 取得完整环境字典，不手填未知的 platform 字符串。另存 Python/NumPy/SciPy/psutil 版本及 BLAS thread 设置。ANCHORS 用 SciPy roots，资源检查用 psutil；每个科学进程限制为单 CPU thread，并由主进程协调所有主机合计至多两个科学 worker。
3. 提交新 config 后，在服务器调用原 `--freeze`，输出新文件，例如 `ANCHORS_server_v1_protocol.json`、`negative_controls_server_v1_protocol.json`。不覆盖旧 freeze，也不手改冻结 `sources`、`config` 或 `fingerprint`。新 manifest 中 `/data1/...` 绝对路径是其科学 provenance 的一部分。
4. tmux 中顺序执行原 ANCHORS 和 negative 控制入口即可；仍是一 worker、完整 trial 的 checkpoint/resume。没有必要为这 1,700 units 引入新调度器。保存 tmux session 名、实际命令、PID/开始结束时间、exit code、stdout/stderr、每次 invocation 和准确 remaining IDs。不能仅因 session 存在就声称任务仍运行。

历史 C-STAT 的跨平台 Pareto 字节兼容失败保留为历史证据。它不授权重跑旧确认性实验，也不要求尚无 outcome 的新服务器补充协议伪装成旧 macOS 环境或逐字节复现旧平台。新协议的每个 study 均在所声明服务器环境中完成，不混合不同环境的 trial。

## 绝对路径与离线读取

`CheckpointStore` 用 `file_hashes(manifest['sources'])` 校验科学源；简单回传 manifest/checkpoints 后，本机不存在服务器绝对路径。**不能把 manifest 的 source keys 改成本机路径**：其 fingerprint 和 checkpoint 中的 fingerprint/code hash 都依赖原字节。

新增独立 `experiments/relocated_sources.py` 提供 `relocated_source_checks(manifest, remote_prefix=..., local_prefix=...)`。它先验证完整 manifest fingerprint，再逐文件严格映射远端相对路径到本机仓库、核对每个 SHA-256；拒绝 `..`、非规范路径、prefix 外路径、symlink 逃逸和未登记远端源。随后仅在 context 内包装 `comet.checkpoint_store.file_hashes`，读取本机相同内容并保留原远端 key。`check_sources=True` 原校验保持启用，finally 恢复函数；不修改 manifest/config/checkpoint。新 server config 文件也必须回传到本机同一相对路径并保持同 SHA。

它只处理离线源内容读取，不映射运行中的 `_source_stamps`/stat 路径，不适配估计器，也不用于在本机继续远端抽样。

本机仅核验服务器 source 的示例（尚未执行）：

```sh
.venv/bin/python -m experiments.relocated_sources --protocol results/post_cstat/remote_20261115/ANCHORS_server_v1_protocol.json --remote-prefix /data1/shengen/COMET_POST_CSTAT_20261115 --local-prefix /Users/shengenli/Documents/ChatGPT/COMET --receipt reports/post_cstat/ANCHORS_server_source_verification.json
```

ANCHORS 的原 `analyze_anchors()` 会首先校验 `production_environment == environment_signature()`。因此 Linux 协议在 macOS 调用原入口会如实拒绝，路径映射不能消除该约束。按主进程决定，**ANCHORS 在服务器用原 `--analyze` 生成不可变 summary.json/summary.csv/manifest.json 后回传**；本机可核验 source/checkpoint 内容并使用这些已签 hash 的分析产物，不冒充服务器环境。

negative controls 的原分析器不要求当前分析环境等于生产环境，可在本机严格映射下调用原函数。它会照常产生本机分析 manifest，另附 source relocation receipt：

```sh
.venv/bin/python -m experiments.relocated_sources --protocol results/post_cstat/remote_20261115/negative_controls_server_v1_protocol.json --remote-prefix /data1/shengen/COMET_POST_CSTAT_20261115 --local-prefix /Users/shengenli/Documents/ChatGPT/COMET --receipt reports/post_cstat/negative_server_local_analysis_relocation.json --analyze-negative --results results/post_cstat/remote_20261115/negative_controls --output results/post_cstat/remote_20261115/negative_controls_analysis_local_v1
```

## 最小 receipt 与回传清单

迁移 receipt 至少记录：旧/新 protocol 文件 SHA 和 fingerprint、同一 planned-ID 集合的 SHA/数量、旧 study 的零 checkpoint 事实、source Git SHA/逐文件 SHA、新 config SHA、实际生产环境、迁移理由、种子/domain 是否保持、两端根路径、实际 tmux 命令和退出状态。路径映射和本机分析 receipt 另存，不能重签原远端协议。

服务器结果回传保留单一 canonical mirror：两份新 manifest/config、逐 run checkpoint、cell metadata、invocations/日志、失败与预选 raw debug、ANCHORS 原分析输出，以及一份按相对文件名列出的 **压缩文件 bytes SHA-256 + size** 清单。同步不覆盖既有不同 bytes；同步后对照该传输清单校验。不要把已有科学 `checkpoint_inventory_sha256` 当文件 bytes SHA：原分析器计算的是 `[run_id, digest(payload)]`，其 payload 及原 source key 都保持不变。本任务没有改写任何 inventory。

只保存一个回传 checkpoint 树；不要在全局预算目录里复制多个同 ID 的镜像。全研究最大配置量为 29,600 primary + 1,600 anchors + 100 negatives = 31,300，新总量仍低于 32,000。服务器原 budget scanner 只看服务器 results root，不能自动看见本机 E1–E5 的 units/bytes；主进程须用两端清单合并监控总 units 和 1.5 GiB 新产物 cap，并为未完成本机产物预留空间。原 free-disk 2 GiB 和 RAM 检查不改。
