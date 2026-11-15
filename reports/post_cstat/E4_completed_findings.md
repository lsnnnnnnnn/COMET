# E4 已完成结果：主查询 gap power 与 family-any detection

本报告仅从已完成 `results/post_cstat/E4_analysis_v1/summary.json` 提取，源哈希与 manifest 一致。未读取 raw 或重放 oracle，未改论文/冻结源，新增科学抽样为 0。

## 完成状态与统计口径

- 7,200 / 7,200 条件日志，24 cells × 300 个独立完整 trial；192 个预声明主水平 cell×method 比较。
- failed / unassessable / unknown frame 均为 0；全部主比较 complete-family coverage 为 300/300。
- 192 个 Holm undercoverage p 值均为 1，显著标记 0。所有主查询与 family-any 的假安全、假违规观察计数均为 0。
- 以下表格均为主水平 `delta=.05`（95%）；`.10` 是同日志上的次级水平，单独保存在 JSON。
- 每个适用 cell/method 的分母为 300。方法、16 个坐标、置信水平不增加独立重复数。Wilson 区间为 pointwise Monte Carlo 区间，不能替代联合证书或证明零错误率。

## 端点定义

`S`：预声明主查询被认证安全（upper <= threshold）；`V`：主查询被认证违规（lower > threshold）。`FS/FV`：主查询的假安全/假违规。真 gap <= 0 包括 gap=0，均属于 safe/null 一侧；不能把 gap=0 当作正 gap 检测功效。

`D`：16 坐标 family 中至少一项真实违规被认证，即 summary 的 `endpoints.true_violation_detected`。它不等于主查询 V，尤其不能用其他坐标的违规来填补主查询 gap power。下表每格是 **S / V ; FS / FV ; D**，各数均是 hits/300 的分子。`NA` 表示 heavy 环境没有报告该 bounded-only comparator，绝不是 0/300。

COMET=`comet_local`；generic=`generic_matched`；GB=`graph_bernstein`；GH=`graph_hoeffding`。表中 GB/GH 为 local/同信息版本，未替换为 global ablation。

### moderate-bounded

| 真 gap | COMET | generic | GB | GH |
|---:|---|---|---|---|
| -0.10 | 298 / 0 ; 0 / 0 ; 300 | 298 / 0 ; 0 / 0 ; 300 | 298 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 |
| -0.03 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 |
| +0.00 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 |
| +0.03 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 |
| +0.10 | 0 / 300 ; 0 / 0 ; 300 | 0 / 300 ; 0 / 0 ; 300 | 0 / 300 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 |
| +0.20 | 0 / 300 ; 0 / 0 ; 300 | 0 / 300 ; 0 / 0 ; 300 | 0 / 300 ; 0 / 0 ; 300 | 0 / 300 ; 0 / 0 ; 300 |

### weak-bounded

| 真 gap | COMET | generic | GB | GH |
|---:|---|---|---|---|
| -0.10 | 0 / 0 ; 0 / 0 ; 297 | 0 / 0 ; 0 / 0 ; 297 | 0 / 0 ; 0 / 0 ; 297 | 0 / 0 ; 0 / 0 ; 0 |
| -0.03 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 0 |
| +0.00 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 0 |
| +0.03 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 0 |
| +0.10 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 0 |
| +0.20 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 300 | 0 / 0 ; 0 / 0 ; 0 |

### moderate-heavy

| 真 gap | COMET | generic | GB | GH |
|---:|---|---|---|---|
| -0.10 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| -0.03 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.00 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.03 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.10 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.20 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |

### weak-heavy

| 真 gap | COMET | generic | GB | GH |
|---:|---|---|---|---|
| -0.10 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| -0.03 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.00 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.03 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.10 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |
| +0.20 | 0 / 0 ; 0 / 0 ; 0 | 0 / 0 ; 0 / 0 ; 0 | NA | NA |

## 可支持的结论

1. **主查询认证只在 moderate/bounded 的远离阈值配置出现。** COMET 与 generic 在 gamma=-.10 认证安全 298/300；gamma=.10、.20 认证违规各 300/300。gamma=-.03、0、.03 均未对主查询给出安全或违规认证。weak/bounded 与全部 heavy 配置中，COMET/generic 的主查询安全和违规认证均为 0/300；这些未认证结果不能隐去。
2. **充分匹配的有界强基线恢复同样的主查询决策。** GB 在全部 12 个 bounded cells 的主查询四项计数和 family-any D 均与 COMET 相同；GH 仅在 moderate/bounded、gamma=.20 认证主查询违规 300/300，其余适用 cells 的主查询 S/V 均为 0。不能将这些结果写成 COMET 对充分匹配 GB 的检测优势。
3. **family-any detection 很高并不代表目标 gap 被检出。** moderate/bounded 的六个 gap 中 D 全为 300/300，包括主查询 S/V 都为 0 的 -.03、0、.03。weak/bounded 的 gamma=-.10 为 297/300，其余五格 D 为 300/300，但六格主查询 S/V 全为 0/300；因此 gap-power 图必须使用 `extension_endpoints.primary_certified_violation`，并同时画 primary safe。全部 heavy 的 D 为 0/300。
4. **匹配 generic 的等价结论继续成立。** 24 cells × 两水平的 48 个 COMET-minus-generic paired mean-width comparisons 全部为差 0、pointwise bootstrap95=[0,0]（2,000 次重采样）。选定方法的 primary/family-any 端点和 mean intersected width 也逐行一致。

## Pointwise Wilson95 与次级水平

| 已观察计数 | Pointwise Wilson95 | 本报告中的例子 |
|---:|---|---|
| 0/300 | [0, .012642971224546027] | 所有观察为零的主查询 false-safe/false-violation；大量未认证 cells |
| 298/300 | [.9760224167496929, .998169851642088] | moderate/bounded、gamma=-.10 的 COMET/generic/GB primary safe |
| 297/300 | [.9710165066376601, .9965933815622847] | weak/bounded、gamma=-.10 的 COMET/generic/GB family-any D |
| 300/300 | [.9873570287754538, 1] | complete-family coverage 及观察检测率为1的固定比较 |

次级 delta=.10 中，COMET moderate/bounded、gamma=-.10 的 primary safe 为 300/300；gamma=.10/.20 的 primary violation 仍为 300/300，其余 COMET 主查询认证为 0/300。不得把次级的 300/300 混写为主水平的 298/300。JSON 完整保留了两水平四个指定方法的全部 24 cells，包括 NA。

## 详细半径与解释限度

详细诊断状态：`NOT_AVAILABLE_AT_REPORT_GENERATION`。本次 summary 不含 primary query 的逐查询半径或 design-only 2r boundary，所以这些量记为 NA；不能将 family-mean intersected width 除以二冒充 primary radius，也不从已观察 power 反推或调整 gap。

E4 测量固定 family auditing，不测 policy return、safe-useful return 或 discovery pipeline；这些端点为 N/A。所有失败/空区间本应保留在 trial 分母；本完成分析中实际失败与未知均为零。零 false decision 与 Holm 非拒绝不能证明证书数学成立，亦不能把几乎不输出主查询结论描述成成功服务。

## 源指纹

- summary SHA256: `70df695d73f615eef27048fac8441530375de5827bcaa21c389bee3097e308f4`
- analysis fingerprint: `b568ae1733754eace7bea6b94fbb8cf27ab5fb13b0752a6b6eded343c2a0123e`
- protocol fingerprint: `10f304e204939844e4a9ee14572b672002238477b421bc44a47e3fe1d93e6b6a`
- checkpoint inventory SHA256: `a5c387ecac2b1785d93c1051b51f60324655ddfd54ee7e5b2e8abe417ffc8286`

配套 JSON 保存原 summary 的每个适用端点 hits、完整 trial denominator、unknown、rate 和 pointwise Wilson95；未合并旧17项检验或修改任何冻结分析。
