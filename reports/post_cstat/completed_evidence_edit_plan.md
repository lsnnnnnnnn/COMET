# E1–E3 已完成证据的论文修改计划

核对日期：2026-11-15。任务仅为只读核对和修改计划；本次未改论文或冻结源，未生成结果、图表或新实验。E4/E5 未读取进行中的结果或大 raw，不作提前结论。下列行号对应本次读取的文件快照，后续以原句定位。

## 1. 已核实的证据边界

优先依据不可变分析的 `summary.json` 和 `manifest.json`，并用 `reports/post_cstat/E{1,2,3}_completed_findings.json` 作交叉核对。四份 summary 的 SHA256 均与各自 manifest 的 `outputs` 一致；本次没有重扫 checkpoint、重算统计或调用 oracle。

| 套件 | 完成的条件日志 | 固定 cell 内独立完整 trial 数 | 主诊断 family 数 | 主诊断 complete-family coverage | 失败 / 不可评估 / 未知 frame |
|---|---:|---:|---:|---|---|
| E1 | 12,000，12 cells | 1,000 | 96 | 每个固定比较 1,000/1,000 | 均为 0 |
| E2 | 1,800，6 cells | 300 | 60 | 每个固定比较 300/300 | 均为 0 |
| E3 | 3,600，12 cells | 300 | 108 | 每个固定比较 300/300 | 均为 0 |

三套主分析的所有 `any_false_claim` 计数均为 0，所有 Holm undercoverage p 值均为 1。此处只是固定样本实现诊断的观察结果，不能写成数学有效性的实验证明、零真实错误率或检验功效证据。

E2 六个条件在同一 replicate ID 内共享配对 primitive vector；不能把 1,800 条件日志写成 1,800 个相互独立的随机向量。方法和两个置信水平也共享日志。96/60/108 是分别冻结的 cell×method 主诊断 family，不能将其当作额外独立 trial，也不要与旧 17 项比较合并。主结果为 `delta=.05`；`.10` 是同日志上的次级结果。

每个固定 E1 比较的 coverage Wilson95 为 `[0.996173241514445, 1]`，零事件的 Wilson 上端为 `0.0038267584855551213`；E2/E3 对应数值为 `[0.9873570287754538, 1]` 和 `0.012642971224546027`。均为 pointwise Monte Carlo 区间，不能在图注或摘要称为跨 cell/method 的联合区间。

## 2. 可以直接写入的精确结果

### E1：覆盖与 violation detection 要分开

主水平 COMET 的 whole-trial `true_violation_detected`：

| 图 | overlap | bounded | heavy |
|---|---|---:|---:|
| independent | moderate | 1,000/1,000 | 0/1,000 |
| independent | weak | 1,000/1,000 | 0/1,000 |
| cycle | moderate | 1,000/1,000 | 0/1,000 |
| cycle | weak | 1,000/1,000 | 0/1,000 |
| triangles | moderate | 1,000/1,000 | 0/1,000 |
| triangles | weak | 2/1,000 | 0/1,000 |

最后一项的 Wilson95 为 `[0.0005486435881207276, 0.007262807863492173]`。不能用“五个 bounded cells 有效”省略第六格，也不能将 heavy cells 的覆盖成功写成检测成功。

强有界基线是关键对照：在 independent/weak/bounded 和 cycle/weak/bounded，`graph_bernstein` 都检测 1,000/1,000，`graph_hoeffding` 都为 0/1,000；triangles/weak/bounded 的 COMET 与 graph Bernstein 均为 2/1,000。这里支持“在这些配置中实际残差范围与方差界决定可认证性”，不支持“COMET 相对充分匹配有界基线普遍提高检测”。E1 的 return/useful/discovery 端点是 N/A，不能用 E1 数据宣称有用策略返回。

### E2：局部问题不支付无关外部困难，但 generic 同样恢复该性质

固定查询为 `E2/policy0/auditor1`，即 constant-policy 的 audited first half；`normalizer=1`、子群质量 `0.5`、已知目标类直径 `0.5`。以下的 **normalized radius 是 raw radius / subgroup mass**，不是查询 API `normalizer` 从 1 改成了 .5。

| 方法 | outside hub=1 | hub=16 | hub=64 | 含义 |
|---|---:|---:|---:|---|
| pure local truncation | .03254654022611246 | .03254654022611246 | .03254654022611246 | local moments + support graph；两种 outside exposure 均相同 |
| local moments / global graph | .03254654022611246 | .09205551719217947 | .18411103438435894 | pure truncation；隔离 graph 成本 |
| global envelope / global graph，moderate outside | .049363202353544106 | .1396202205010991 | .2792404410021982 | pure truncation；外部 moment 与 graph 一起支付 |
| global envelope / global graph，outside exposure≈1e-4 | 2.215436337961385 | 6.266200231438349 | 12.532400462876698 | 相交后覆盖整个已知目标类 |
| COMET / matched generic | .021100648102250912 | .021100648102250912 | .021100648102250912 | eligible bounded 分支的额外收益；两种 outside exposure 均相同 |

局部可用 coloring count 均为 2；全局 count 为 2/16/64。raw radius 分别为上表值的一半，例如 pure local `.01627327011305623`、COMET `.010550324051125456`。COMET 的 median intersected width / feasible diameter 在六格均为 `.04220129670456116`。

E2 六个 cell 的 COMET-minus-generic mean-per-trial coordinate-width difference 在主水平均为 0，300 个配对 trial、2,000 次 bootstrap 的 pointwise95 区间均为 `[0,0]`。不要据此宣称 COMET 是优于信息充分匹配 generic 的新估计量。纯截断三层间的变化和 bounded dispatch 的收益应分开解释。

`E2_detailed_v1` 对 1,800 个 checkpoint 的独立详细核对状态为 `COMPLETE_CHECKS_PASS`，缺失、损坏和 mismatch 均为 0。该核对的 coordinate quantiles 是描述性分布；不能将 300×16 个坐标当作独立重复建立 binomial/Wilson 区间。

### E3：direct cancellation 的一个成功环境与其余零 power 必须同显

E3 是 **risk-response contrast**：负值代表风险改善，真 improvement 的记录规则是 `hi<0 AND truth<0`，NI 为 `hi<=0`。它不是 E5 的 utility-gain 下界为正端点；下文“improvement”应读作风险降低，不能借用成已验证的策略效用增益。

主水平、所有 cell、COMET 与 deduplicated joint-level comparator 的结果如下。宽度来自 `mean_per_trial_coordinate_width`，是每个 trial 内 16 个最终 contrast **相交区间**宽度的均值，再跨 trial 取均值；它不是 raw width，也不是固定单查询 median。

| 支持变化比例 | overlap / outcome | COMET mean width | joint-level mean width | COMET 真正 improvement detection | joint-level detection |
|---:|---|---:|---:|---:|---:|
| .02 | moderate / bounded | .000748958229148161 | .003104986189298664 | 0/300 | 0/300 |
| .02 | moderate / heavy | .002670180000931909 | .003104986189298664 | 0/300 | 0/300 |
| .02 | weak / bounded | .002679787304391235 | .003104986189298664 | 0/300 | 0/300 |
| .02 | weak / heavy | .003104986189298664 | .003104986189298664 | 0/300 | 0/300 |
| .10 | moderate / bounded | .001548618467181330 | .015501138219770283 | 0/300 | 0/300 |
| .10 | moderate / heavy | .008284096600818474 | .015501138219770283 | 0/300 | 0/300 |
| .10 | weak / bounded | .005786209989953796 | .015501138219770283 | 0/300 | 0/300 |
| .10 | weak / heavy | .013748484037242763 | .015501138219770283 | 0/300 | 0/300 |
| 1 | moderate / bounded | .006672383577134890 | .045045690605668993 | 300/300 | 0/300 |
| 1 | moderate / heavy | .048411439712565341 | .15487785272068716 | 0/300 | 0/300 |
| 1 | weak / bounded | .022137799838958309 | .13011565364190697 | 0/300 | 0/300 |
| 1 | weak / heavy | .087078950952777012 | .15487785272068716 | 0/300 | 0/300 |

成功 cell `support100-moderate-bounded` 的 COMET-minus-joint-level paired width difference 为 `-.03837330702853408`，pointwise bootstrap95 为 `[-.03837330702855763, -.03837330702851072]`。这是配对宽度比较，不是 improvement detection rate 的 bootstrap 区间。

direct 支付 16 个 distinct contrast；level comparator 支付 **20 个 unique levels（16 new + 4 shared baselines）**，不是 32。二者总 δ 相同。主水平每个 underlying level 分配 `.05/20=.0025`；每个 direct coordinate 分配 `.05/16=.003125`。16 个 derived differences 来自同一个 level 联合事件，不是再给 16 个 differences 追加 δ。报告 underlying 20 与最终 16，不能混称所有方法都用 `m=16`。

所有 12 个主水平 COMET-versus-generic 配对均为差 0、bootstrap `[0,0]`；matched contrast-aware generic 恢复相同结果。主水平 COMET 的 noninferiority 成功也仅发生在 `support100-moderate-bounded`（300/300），其余 11 格为 0/300；deduplicated level comparator 在 12 格均为 0/300。次级 `.10` 在 `support010-moderate-bounded` 有 6/300 improvement/NI，不能混入主水平的“其余为零”句中。所有主水平方法的 false-improvement 观察计数均为 0。

支持的主张是“direct contrast 在一个预声明环境中提供 level subtraction 没有的 sign certificate；减小变化范围虽缩窄区间，却未在其他 11 个主水平环境提高 sign power”。不要改写成“变化越小，认证越容易”或“paired contrast 普遍提高决策价值”。

## 3. 当前摘要与 evidence.tex 的必改项

| 位置 / 现有表述 | 修改动作 | 理由与可直接用的口径 |
|---|---|---|
| `main.tex:40`，`Detection is useful in five bounded cells` | 将 useful 改成精确 violation-detection 结果 | E1 未测 useful return。建议 `Violation detection reaches 1,000/1,000 logs in five bounded cells, 2/1,000 in the sixth, and zero in all six heavy-tail cells.` |
| `main.tex:41–44`，目前只写 E2、随后 `Complete-pipeline and remaining power results are still being collected` | 摘要补入已完成 3,600 条 E3 condition logs；将 pending 明确限定为 E4/E5 | E3 已完成，不能让读者以为 contrast/power 结果都仍待运行。E4 gap power 与 E5 pipeline 尚未完成，继续保留明确的收集状态。 |
| `evidence.tex:6`，`E1--E4 ... a finite family of 16 queries` | 加 E3 underlying20 exception | 可写 `E1--E4 audit 16 target coordinates on N=32768 rows; the E3 level-subtraction comparator jointly certifies 20 unique underlying levels to derive its 16 contrast intervals.` |
| `evidence.tex:70–73`，`.03254654/.02110065/2.2154--12.5324` 称 radius | 统一称 subgroup-normalized radius，说明除以 .5；或全部换 raw 数值 | 当前后文 line76 才标 normalized，前后口径易被误读为原始 estimand 的半径。保持表中 normalized 值可与 Figure2 对齐。 |
| `evidence.tex:123–127`，宽度接着称 `raw intervals` | 将这些观察结果改称 intersected contrast intervals；一般性警句也避免借 raw 暗示已测该量 | 已完成 E3 summary 的宽度统计来自最终 `lo,hi`，并非 `raw_lo,raw_hi`。若将来使用详细 raw export，须另标数据源。 |
| `evidence.tex:120–121`，`positive improvement` | 明确为 certified risk reduction，或紧邻定义 contrast 的负号方向 | 这里是 risk difference 的 `hi<0`，不是正 utility contrast，更不是 E5 useful return。 |
| `evidence.tex:129–130`，`Noninferiority ... may be easy for tiny raw changes` | 与当前观察分开，或改成主水平 NI 的实际结果 | 这可以是理论提醒，但当前 E3 主水平 tiny-support NI 全为 0。建议 `Noninferiority is reported separately; at the primary level it is certified only in the same full-support bounded cell.` |
| `evidence.tex:158–159`，`incomplete E4--E5 ... withheld` | 当前保留，只在两套固定分析完成后替换 | 本计划没有读它们的进行中结果，不能提前写结论。E6 DATA_BLOCKED 说明同样保留。 |

`evidence.tex:41–53` 的 E1 coverage、检测与强基线计数，`:62–68` 的 E2 coverage/matched equality，`:112–128` 的 E3 unique20、主水平 detection 与宽度数值均与本次 summary 一致，除上表口径外不需要回退为 pending。

摘要的建议尾段（建议文本，尚未写入论文；不涉及定理段落）：

> In 12,000 heterogeneous-graph logs, all 96 eligible primary diagnostics cover the complete family in 1,000/1,000 trials per fixed comparison. Violation detection reaches 1,000/1,000 logs in five bounded cells, 2/1,000 in the sixth, and zero in all six heavy-tail cells. A further 1,800 paired-condition logs isolate local evidence costs and confirm equality with the matched generic comparator. In 3,600 contrast logs, direct contrasts certify a risk reduction in 300/300 full-support, moderate-overlap bounded trials, versus 0/300 for equally budgeted subtraction of 20 jointly certified unique levels; the other eleven primary COMET cells have no risk-improvement detection. Gap-power and complete-pipeline results remain under collection in E4 and E5.

篇幅不足时可以压缩 E1 数字，但必须同时保留 heavy-tail 的零检测和 E3 的成功环境限制；E1 的检测不要重新称作 useful return。

## 4. 表 / 图与数据的对应计划

目前 `evidence.tex` 仅引用两张 `figures/design_v1/analytic_*.png`，没有插入 E1–E3 empirical figure，也没有新主实验结果表。以下为后续编辑建议，不表示本次已生成图。

| 论文载体 | 结果与数据源 | 要保留的轴 / 分母 / 标签 | 当前可用性 |
|---|---|---|---|
| 新 compact study/validity 表 | E1/E2/E3 `*_analysis_v1/summary.json`；本计划第1节 | rows、cells、fixed-cell trials、96/60/108、coverage、false claims、失败/未知；不能把 method×coordinate 计入 n | 可直接从已完成 summaries 制表 |
| E1 detection matrix / `fig1_core_validity_informativeness` | `E1_analysis_v1` 的 `family_coverage`、`endpoints.true_violation_detected` | 12 cells 全部保留，COMET 与 graph Bernstein/Hoeffding，pointwise Wilson；heavy 零 power 可见 | coverage/detection 面板已支持；当前未发现 `E1_detailed_v1`，宽度分布 / trial-max error-radius 面板不能填造 |
| E2 `fig2_query_locality` | `E2_detailed_v1/query_summary.csv`，主水平，policy0，auditor1 与 auditor0 分开 | y 为 radius / subgroup mass，x 为 outside hub 1/16/64；moderate/extreme 两行；三条 pure truncation 分层 + COMET bounded dispatch | 详细数据已完成且 mismatch=0；现绘图代码的轴名和 caption 已分开两种机制 |
| E2 小表 / supplement | 本计划第2节 E2 表；所有 methods/policies/auditors 保留在数值导出 | 不用 family-average width 替代不变局部 query。matched equality 的 pointwise pair CI 为 `[0,0]` | 已支持 |
| E3 12-cell 结果表 | `E3_analysis_v1` 的 `mean_per_trial_coordinate_width` 与 `extension_endpoints` | mean intersected width、at-least-one true-improvement/NI hits/300、Wilson、underlying m=16/20 | 已支持；本计划第2节给出精确数值 |
| E3 `fig3_paired_contrasts` | 现绘图接口要求 E3 per-query detailed 的 `E3/policy0/auditor0` median intersected width | support=.02/.1/1，四环境，direct/unique-level；caption 不得把单 query median 等同 family mean，也不得只画窄度来暗示 sign power | 当前未发现 `E3_detailed_v1`，不能把 summary mean 填进 median 图。可先用已支持的12-cell表；详细诊断完成后再渲染该图 |
| 已有 `fig:post-cost` / `fig:post-declining` | `results/post_cstat/design_v1/{fixed_overlap_costs,declining_overlap_costs}.csv` 与本目录 manifest | 216+216 algebraic configs、49-point grid、零 outcome draws、无 MC error bars | 已插入且 grid 已 reconciliation；保留为 deterministic cost 图，不要当作 E1–E3 经验支持图 |

经验图导出接口已经存在于 `experiments/post_cstat_empirical_figures.py`。后续渲染应传显式 completed analysis/detailed 路径和 fresh output；本任务没有运行它。E3 不得传缺失 detailed 后把 unavailable 面板写成已完成证据。旧 `paper/post_cstat/figures/manifest.json` 仍标记 illustrative/pending theory note，是早期归档；当前正文引用的是 `figures/design_v1`，其 manifest 为 reconciled deterministic grid。不要把旧归档 pending 标记误当作现用图仍缺理论输入，也不要直接覆盖旧文件消除历史。

## 5. 来源指纹与本次检查限度

| 分析来源 | summary.json SHA256 | analysis fingerprint |
|---|---|---|
| `results/post_cstat/E1_analysis_v1` | `3f23be62e71980dbbb1436c34b51106241d9bcbef822eb3754b3c935fe9142a7` | `61200f5800b78674bd832dbf6c28fdab841d909635769423dbab1616c4b360b2` |
| `results/post_cstat/E2_analysis_v1` | `3e03041302956432e2544fd470ce355c0307c67c317c3d02e6b17b7f698893e2` | `f50f03bf83d6e2fbadb5e152d111537d486f0a067b7b4013b6d7e85f060e1401` |
| `results/post_cstat/E2_detailed_v1` | `a16bc98db1c99ad11770fa74b9d109febe8405aa5a5ced09b9f4e8108926a4a9` | `624d3688829556f6ef27cc383a142aa6d50f673a1c3e301621d85ac238a5e6ee` |
| `results/post_cstat/E3_analysis_v1` | `8f46750a90e50e85ebeeac7180f4c5a4107479907a711a7fa6432cf8ec4bc29b` | `38ae5735741781cf8e382de2bfe5d1cc17c8cca783c176f7f6c5567480de6fcb` |

论文快照：`paper/post_cstat/main.tex` SHA256=`885be6d8234b173438052294d4b9befd48389f5e6c1eb4a21282a5526f8281a4`；`paper/post_cstat/sections/evidence.tex` SHA256=`1d8b312a5cb747dc9701fa6f128540a649dab9f5ce4b63292d38d8e5516fe8a7`。

本次验证是已有分析与论文的证据一致性检查，没有对全体原始日志作新独立复算，没有检查定理正确性或图像渲染版式。E4/E5 和外部 E6 的最终研究 verdict 仍需各自实际完成状态；E1–E3 不提供完整 return AND safe AND useful pipeline 结论。
