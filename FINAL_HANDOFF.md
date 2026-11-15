# COMET post-C-STAT 最终交接（2026-11-15）

当前本地工作区：`/Users/shengenli/Documents/ChatGPT/COMET`。分支：`codex/query-specific-graph-auditing`。本轮从实际HEAD `254a482d4f82c79ba8ed9c0e57c886611a681ade` 继续，保留其在指定科学起点 `ca5bb878cf9635fac4381d03281df0bc8a900daa` 之后的交接更新；没有reset、清理历史结果、push或同步Overleaf。

**已交付主证明、API、确定性核对、解析预算、E1–E5、强基线/scaling、负控、统计、实际图表、ledger和完整本地论文。唯一未执行的研究路径为E6：官方ACS数据在两端均403，1,000个单位尚未冻结/抽样。不能声称E1–E6全部完成。所有本轮实验和监督进程均已结束，没有仍在后台运行的实验。**

## 首先打开

| 成果 | 路径 |
|---|---|
| 最终本地PDF（24页） | `paper/post_cstat/COMET_post_cstat_20261115.pdf` |
| 完整LaTeX入口 | `paper/post_cstat/main.tex` |
| 研究判断与局限 | `reports/research_verdict.md` |
| proof-code-experiment ledger | `reports/post_cstat/claim_ledger.json`、`.csv` |
| 精确剩余IDs | `reports/post_cstat/remaining_run_ids.json` |
| 最终实际进程检查 | `reports/post_cstat/final_process_state.json` |
| PDF逐页核对 | `reports/post_cstat/final_pdf_qa.json`、`pdf_qa/` |
| 最终资源与单位预算 | `reports/post_cstat/final_resource_budget.json` |
| 可用API与固定数组示例 | `docs/post_cstat_api.md` |

PDF SHA256：`59fed09dccecba4c25920a44784c706d8c53d438ae0fcb77cf98bca17c892943`。编译两遍通过，无Overfull/未定义引用；24页全部render和视觉检查。主图1–5依次为validity/informativeness、query locality、paired contrasts、primary-query power、完整pipeline；解析maps与强基线/负控放附录。旧九页稿仍在 `paper/rewrite_proposals/cstat/`，未被新稿覆盖。

大规模checkpoint、详细聚合和raw-debug文件保留于本地 `results/post_cstat/`；并非所有大数据文件都加入Git。仅复制Git仓库不足以替代这些本地数据。不要执行 `git clean`。各manifest保留完整source/config/input哈希；图bundle固定生成当时的代码SHA。早期E5布局版本v1/v2保留，论文使用v3；它们的科学输入相同。

## 科学单位与保留状态

| 研究 | 完成预算单位 | 独立误差/覆盖分母 |
|---|---:|---|
| E0历史 | 6,000日志，1,134,000记录 | 原六格每格1,000；本轮新增0 |
| E1 | 12,000 | 12格×1,000完整日志 |
| E2 | 1,800 condition logs | 300个paired primitive vectors跨六条件，不能称1,800独立向量 |
| E3 | 3,600 | 12格×300完整日志 |
| E4 | 7,200 | 24格×300完整日志 |
| E5 | 4,000 | 8格×500完整三split trial |
| ANCHORS | 1,600 | 8格×200完整日志；IID强比较与scaling合并预算 |
| negative controls | 100 | 4格×25完整日志 |
| E6 | 0/1,000，未冻结 | 四组各250，仅保留拟定ID |

新主研究完成28,600/29,600，加补充1,700，实际完成30,300个新单位。至多3次未完成的操作性partial attempt另作保守计数；完成+partial上界30,303，未来含E6的整套上界31,303，低于32,000。方法、两个levels和多个坐标共享日志，不能乘进独立样本数。

E5每完整trial使用training4,096/discovery8,192/certification32,768行，共45,056；4,000 trial合计180,224,000行。标签暴露分split为4,328,656、8,650,671、34,614,972个单位。in-sample arm复用认证标签，不得到另一份独立认证样本。全部记录与value scope在 `reports/post_cstat/E5_diagnostics_v1/diagnostics.json`。

## 核心结论

- 主证明允许异质均值与一个连通的充分条件score图，`1<p<=2`；半径支付显式锐利clipping bias、graph concentration和range。相关文件为 `theory/global_residual_truncation.md`、`query_specific_cost_lower_bound.md`。scope不是最终独立宏块MOM。
- E1主96比较均1,000/1,000完整family覆盖；COMET五个bounded cells各检测1,000/1,000，triangles/weak/bounded仅2/1,000，六个finite-moment cells均0。E2主60、E3主108、E4主192比较均300/300覆盖，未观察到错误声明。Wilson只在固定比较内pointwise；不能把多方法或坐标合并成独立trial。
- E2在相同pure truncation中隔离local moments/graph收益。E3 full-support/moderate/bounded的direct risk-reduction为300/300，对照20个去重joint levels相减为0/300；其他11格的COMET正收益检测为0。小步长同时缩放信号和半径。
- E4必须看 `E4/policy0/auditor0`，不能把family-any discovery当该查询power。moderate/bounded在gap-.10 safe298/300，gap.10/.20 violation各300/300，其余三个环境主查询均无认证。`2r`为充分非必要边界。
- E5的32个预声明coverage比较各500/500，实际每trial family都是47。COMET=matched generic在四个moderate cells各安全有用返回500/500；weak cycle mixed/null为340/238，weak independent mixed/null为411/497（均以500为分母）。所有COMET unsafe/infeasible返回观察计数为0，零计数Wilson95上界每格.00762434；不等于真实风险为0，也不提供同delta的条件unsafe-given-return保证。
- E5非baseline且安全且strict utility gain：moderate各500，weak cycle mixed/null为340/231，weak independent mixed/null为411/232。null中的7/265个baseline返回另列。strict gain是posthoc描述诊断。status quo虽oracle-feasible但全baseline、strict gain0、无证书；总弃权的有用返回为0。完整结果见 `E5_completed_findings.md/.json`。
- E5 global是pure truncation ablation；与COMET的差异同时包括localization和bounded dispatch，不能单归因图。最强fully matched baseline得到同样信息与dispatch，代数及结果均相同。没有独立新估计器优越性主张。
- IID强比较中bounded DR-EB比COMET窄（.01055/.01748）；finite-moment Catoni也更窄（.15246/.17416），两者均未检测违规。所有68主anchor比较200/200覆盖。**保留一条secondary90% scalar-betting失覆盖，199/200**；runner failed_units=1计入该置信失败，analysis execution failure=0，checkpoint1599COMPLETE+1COMPLETE_WITH_CONFIDENCE_FAILURE。不得删掉或改称全部零失败。
- finite-moment scaling即使N=131,072仍0/200检测。负控invalid arms均HEURISTIC、覆盖0/25；wrong-e/leak/missing-bias各false-safe25/25，hidden shock false-violation13/25。honest refusal的coverage/error为NA，不是0风险。

各完整分析为 `results/post_cstat/E{1,2,3,4,5}_analysis_v1/`；E1–E4独立明细位于对应 `_detailed_v1/`，均零mismatch。E5独立重建12,000 families/64,000 frames，`RECONSTRUCTED_RECORDS_MATCH`，无重采样或原oracle调用。补充分析为 `ANCHORS_server_v2_analysis_v1/` 和 `negative_controls_server_v2_analysis_v1/`。完整数字复核在 `reports/post_cstat/final_numeric_review.md`。

## 环境、tmux及操作性优化

E1–E5保持原CPython3.12.2/NumPy1.26.4/macOS27.2 arm64生产环境，不能把运行时缺少某个环境gate解释为允许迁移。E5现已全完成，无待续IDs。

用户要求长任务用服务器tmux后，仅将零outcome的两套补充实验作environment-only预修订。实际服务器 `shengen@10.200.13.23`（amax）；独立目录 `/data1/shengen/COMET_POST_CSTAT_20261115`。Python3.12.3/NumPy1.26.4/Linux5.15 x86_64/glibc2.39。snapshot Git `f5ba837fadd83ba7264645e023164ec5dd297584`是local `abdeab0`的独立source-only快照，不冒充同一Git历史。旧服务器目录未改。

准入fixture禁止生产RNG，22,413个numeric leaves按原rtol5e-12/atol5e-13核对、23,255个exact leaves核对，零不一致。六个跨平台data digest不同被保留，并展开每条确定性观测、验证各自host内byte hash后作数值对照；不要求新的跨平台transcendental bitwise equality，也未放宽E0旧合同。准入记录 `server_admission.json`、`server_fixture_comparison_v2.json`。

tmux会话 `comet-post-cstat-20261115` 串行完成两套补充及分析，最终pane dead=1、exit=0；没有科学子进程。1,718个返回文件、25,676,424 bytes逐项hash匹配，见 `server_return_verification.json`。1718是文件数，不是trial数。

E1原144+fast11856完成；原144字节保留。E5原197+fast2836=3033后停，剩余967按**全冻结ID排序index modulo2**分为互斥两进程，保持原模型/seed/environment和全部已完成字节。3033文件完整hash快照为 `E5_before_shards_snapshot.json`，最终仍全匹配。所有来源、缓存等价fixture、partial accounting见 `command_log.md` 与 `operational_invocations/`。单个shard COMPLETE只代表该partition；全E5 COMPLETE由4000-ID完整分析确认。

全局最多两个科学CPU worker，无GPU/paid compute。资源receipt使用包含完整既有Git等在内的保守上界（含64MiB交付余量）约1.23GiB，低于1.5GiB；磁盘余量约82GB，大于2GiB。并发RSS是采样观察，非精确peak。原 `wall_seconds` 是runner的monotonic计时；与进程日历elapsed分开，不声称断线期间持续计算。

原协议/来源有绝对路径。离线回传核对使用 `experiments.relocated_sources` 严格验证同SHA并保持原manifest/fingerprint，不伪造环境、不跳check_sources；ANCHORS分析已在其真实服务器环境完成。不要重写旧protocol路径或修改冻结source来“修正”历史DRAFT字样；production stage由已冻结runner/config定义。

## 测试、输入与历史保留

354项新增确定性测试通过；新增9项relocation测试通过。绘图width/percentage布局修改后相关5项重验通过，并用实际生成图/PDF视觉核对。没有重跑旧485项测试或28,884,898检查。固定数组fixture和bootstrap分析不计为新的outcome抽样。

E0最终只读核对见 `E0_final_preservation.json`：6000个压缩文件逐项SHA匹配旧index，历史确认目录、配置、seed manifest和九页提案对ca5bb878的Git byte diff为空。历史源/上下文哈希及全部新冻结源哈希均匹配。A的r=.015005043614373761、gamma=.0375>2r是确定性解析对照；未并入旧17项。

输入保存在 `task_materials/post_cstat/`。override/master/SCOPE/THEORY/CLAIM均已完整读；只有 `EXPERIMENT_BLUEPRINT.json`找不到，用户明确回复“先别管了”，receipt为 `INPUT_RESOLUTION.md`。没有编造或声称读过缺失blueprint。旧D1–D5已按override映射执行，没有另加旧Cartesian grid。

## 唯一剩余：E6及恢复命令

`remaining_run_ids.json` 的 `suites.E6.remaining_ids` 是完整1000-ID列表；其他研究remaining都是空数组。当前E6 IDs为拟定保留、未冻结、未消耗seed：

- `comet-post-cstat-v1/E6/moderate-loggerindependent/0000` 至 `/0249`
- `comet-post-cstat-v1/E6/moderate-loggercycle/0000` 至 `/0249`
- `comet-post-cstat-v1/E6/weak-loggerindependent/0000` 至 `/0249`
- `comet-post-cstat-v1/E6/weak-loggercycle/0000` 至 `/0249`

只选过官方 `https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pca.zip`。两端均未取得有效archive；最新服务器receipt是 `reports/post_cstat/E6_server_download_20261115T042857Z/receipt.json`。4861-byte错误body及其hash不是ACS archive/hash。没有代理绕行、替代数据集、prepared数据、E6freeze或E6实验。

以后仅在该实际官方archive可用并记录真实来源/SHA后，在上述服务器目录执行（ACTUAL_SHA256须替换为真实官方archive的hash）：

```sh
cd /data1/shengen/COMET_POST_CSTAT_20261115
python3 -m experiments.semisynthetic_selective_labels --prepare \
  --archive data/acs_ca2018/csv_pca.zip --sha256 ACTUAL_SHA256 \
  --output data/acs_ca2018/prepared
```

由 `configs/post_cstat/E6_template.json` 新建 `E6_v1.json`，填真实archive_sha256、保持原ID/seed/科学设计，设置真实生产environment（`experiments.post_cstat_runner.environment_signature()`），删除template_status并改schema为E6实际版本。先commit该实际config，再冻结；不得使用fixture假冒ACS、减少replications或把错误body当archive。

```sh
git add configs/post_cstat/E6_v1.json
git commit -m 'Freeze E6 actual official archive and server environment before outcomes'
python3 -m experiments.e6_runner --freeze --config configs/post_cstat/E6_v1.json
python3 -m experiments.e6_runner --status --list-ids

tmux new-session -d -s comet-e6-resume \
  -c /data1/shengen/COMET_POST_CSTAT_20261115 \
  'env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -m experiments.e6_runner --run > reports/post_cstat/E6_stdout.txt 2> reports/post_cstat/E6_stderr.txt'
```

确认实际run receipt COMPLETE且remaining为空后：

```sh
python3 -m experiments.e6_runner --analyze --output results/post_cstat/E6_analysis_v1
```

准备和freeze会核对来源、实际archive SHA、无标签certifier view、household-protected exact split可用性、来源与输入哈希；失败不得消费logging seed。保留其拒绝状态。如果E6终于完成，再生成实际real-covariate图表、更新ledger/verdict/本地论文并重新编译/视觉检查；保持独立Overleaf不动。

本次没有留下自动重试、计划任务或科学后台进程。恢复需要实际外部数据状态改变，不能靠再次运行已完成ID取得新结果。
