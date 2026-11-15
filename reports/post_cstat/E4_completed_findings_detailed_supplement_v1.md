# E4 detailed 补充与 E1–E4 图注核对（v1）

本文件补充旧 `E4_completed_findings.{json,md}` 当时为 NA 的逐查询半径，保留原报告。只读已完成 detailed/summary、绘图代码、图注与实际 PNG；未读 raw、未调用 oracle、未新写测试或修改源码/论文。

## E4 主查询与精确 r/2r

确认预声明主查询为 `E4/policy0/auditor0`：fixed first3277 /32768 rows，action1 policy，质量与 query normalizer 均为 **0.100006103515625**，active rows=3277，可用 coloring count=2。其 radius 已处于归一化子群目标尺度；`radius==normalized_radius`，不能再除以质量。

以下均为主水平 delta=.05。每一行 r 在同环境六个 frozen gaps 以及每个 gap 的300条日志上均为 min=median=max；不存在依据实测 gap 改半径。JSON 同时保留次级 delta=.10。每格为 **r / 2r**：

| 环境 | COMET / generic | Graph Bernstein | Graph Hoeffding | Global envelope + graph |
|---|---|---|---|---|
| moderate-bounded | 0.08709241106946453 / 0.17418482213892905 | 0.08709241106946453 / 0.17418482213892905 | 0.15297497051887793 / 0.30594994103775586 | 0.418964312750732 / 0.837928625501464 |
| weak-bounded | 0.5293210537441797 / 1.0586421074883594 | 0.5293210537441797 / 1.0586421074883594 | 3.783941335888465 / 7.56788267177693 | 2.115308362851165 / 4.23061672570233 |
| moderate-heavy | 0.3999787394215726 / 0.7999574788431452 | NA | NA | 1.880533136111175 / 3.76106627222235 |
| weak-heavy | 1.1645128909556162 / 2.3290257819112323 | NA | NA | 5.53450469613694 / 11.06900939227388 |

Fig4 的线/注记采用正确主查询 COMET 的 `2*max(per-gap median normalized_radius)`。此处六格值相同，故就是上述2r。只有 moderate/bounded 的2r=.17418482213892905位于[-.10,.20] gap grid内；另外三环境分别为1.0586421074883594、.7999574788431452、2.3290257819112323，图上注记1.06、.8、2.33与精确值对应。

gamma>2r 是 coverage event 上的充分条件，不是必要条件。moderate/bounded 在gamma=.10已检测300/300，虽小于2r，完全允许；gamma=.20大于2r。其他三环境没有任何预声明正 gap 超过COMET的2r，不能把线移入窗口，亦不能据此声称必要信息下界。

## 四张图的 caption 与统计映射

| 图 | 实际映射 | 核对结论 |
|---|---|---|
| Fig1 core validity/informativeness | A：summary complete-family coverage与whole-trial Wilson；B：detailed group `feasible_width_ratio`的坐标median/IQR；C：COMET whole-trial any/all nontrivial与family-any violation detection；D：trial内先max(error/radius)，再取trial间p90/max | 实图与caption一致。B的IQR是坐标描述量；C的检测是family-any，不能借到E4主查询power。 |
| Fig2 query locality | constant policy0，auditor1(first half)与auditor0(global)分开；`normalized_radius`，outside hub1/16/64与两种outside overlap；三种pure truncation与COMET bounded dispatch分开 | 实图、轴名和caption一致；local graph收益与bounded branch收益没有混为一谈。 |
| Fig3 paired contrasts | 固定`E3/policy0/auditor0`，`intersected_width` **median**，3个changed-support比例×4环境，3条方法曲线 | **只画median，没有IQR/errorbar/shaded band**。绘图代码是`ax.plot`，未读取q25/q75；实PNG同样没有IQR。当前正文caption已写median-only，与bundle caption一致。 |
| Fig4 power boundary | summary的`primary_certified_violation`/`primary_certified_safe`；2r也只选`E4/policy0/auditor0` | 主查询选对，未误用`true_violation_detected` family-any端点；Wilson为独立完整trial的pointwise区间。阴影/zero线与safe/null区分一致。 |

Fig3 数据源保留q25/q75，并不表示图已画IQR。作为数值定位，full-support / moderate / bounded 的单查询median：COMET **0.011856132161399309**；joint-level **0.06278905355150827**。正文的.006672383577134890/.045045690605668993是16个contrast的mean-per-trial coordinate width，再跨trial均值；两种统计量不同，不能用正文均值去对图的单查询median。

## 来源与检查限度

- E4 detailed状态：`COMPLETE_CHECKS_PASS`，7,200个checkpoint已核对，mismatch/missing/corrupt均为0。
- 四图的PDF、PNG、bundle captions SHA256均匹配图manifest；四套analysis和八个detailed CSV输入也与图manifest一致。
- 图generator当前SHA256与图manifest的`code_sha256`相同。本核对查看了实际四张PNG，没有重画图或重跑统计。
- E4 detailed summary SHA256：`4046da84b907000085f784f45eae0fe441576153654502c81f1468e7e58454bd`。
- E4 detailed analysis fingerprint：`c1f8173e17bab9cb9243c5e34e09325b0471b40de58aea373cc8170ffcd44bbe`。
- 配套精确JSON：`E4_completed_findings_detailed_supplement_v1.json`。

本文件只核对已有图/证据对应和补充已完成的半径，不替代原证明、完整analysis receipt或E5的最终结果。
