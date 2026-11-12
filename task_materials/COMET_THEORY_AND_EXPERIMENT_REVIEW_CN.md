# COMET 论文：理论审查与实验方案（中文）

**审查对象**：用户提供的 `__Counterfactual_Moment_Auditingunder_Weak_Overlap_and_Dependent_Feedback.zip`，尤其是 `sections/02_setup.tex`、`03_method.tex`、`04_theory.tex`、`05_discover_repair.tex`、`06_experiments.tex`、`appendix.tex` 和长稿对应章节。压缩包包含 LaTeX/PDF 和 TODO，没有实验源码、真实结果。本文为静态理论审查与研究设计建议，不是已经完成的实验或形式化证明验证。

## 0. 一句话判断

最合理的主线是：**在有限 p 阶反事实 score moment、已声明且足够的图依赖结构、受控时间依赖下，对冻结的多策略×多审计函数族给出可核查的同时置信区间，再把它们用于隐藏群体认证和保守策略选择。**

与其宣传“COMET 比 DR 的点估计普遍更准”，不如证明“哪些条件下 95% 区间不会失效；什么时候证据不足必须 abstain；这种保守性带来什么收益/代价”。真正的困难包括区间常数、未知高阶矩、适应性反馈下的目标定义、跨块的独立性、以及 graph 有无遗漏 latent shock。

## 1. 理论漏洞排序（必须先修）

### P0-1：路径依赖 estimand 和独立块 MOM 的证明模型没有自然兼容

**位置**：`02_setup.tex` 的 `M_W`，`04_theory.tex` 的 uniform theorem，`appendix.tex` 第 87–126 行。

`M_W=(1/N)sum E[Z_u|F_{t(u)-1}]` 是由实际部署历史决定的随机对象。若本轮动作/结果改变下一轮 contexts、logging policy 或 q，那么 future conditional means 本身会随过去随机数据改变。附录“条件化到所有 design 和 nuisance training 数据之后，将 B 个 block means 替换成独立同分布边际副本”不能未经证明就推出相对于原始 realized-path target 的集中不等式。条件化到未来设计变量可能也会暴露过去 action/outcome。

**推荐修复**：

- 主定理先限定为 **offline/exogenous 或 conditional-independent macro-block** 模型：在一个合法的、不会包含当前评估 outcome 及其下游结果的 sigma-field 下，block scores 独立，block target 条件确定；或固定总体 target。
- 单独写 **adaptive/prequential** 版本，使用 martingale-difference 条件与 predictable truncation/robust mean，明确哪些结论尚待证明。
- 真实图和 bandit 结果若达不到已证明模型，则用“实证/敏感性验证”，不能硬套同一个 certified 标签。

**必要实验**：独立块数学对照；自适应但已知模型的合法案例；将 future-dependent target 错当 fixed target 的 negative control。

### P0-2：cross-fitting 不等于“对所有 block 条件独立”

**位置**：`03_method.tex`、附录第 60 行、第 90–92 行、第 141–160 行。

互为训练集的 cross-fit folds 可能使某个 evaluation block 的预测器依赖另一块的 outcome。若证明一次性条件化所有 nuisance fitted models，不代表评价 scores 仍保留所需独立性。甚至 exact logged propensity 也不能修复严重的 in-sample outcome leakage：exact e 仅消除了符合条件下的代数 DR remainder。

**修复**：将“独立 nuisance pilot + 完全隔离的认证数据”作为严格定理/实验主路径；guarded time/entity cross-fitting 作为工程对照，除非给出独立的依赖概率证明。提供简单反例与单元测试。

### P0-3：conditional finite-p envelope、weak overlap 和定理矩界有张力

**位置**：`02_setup.tex` 第 63–73 行、`04_theory.tex` graph-moment lemma。

设置中只假定 window-average 的 oracle-score p moment，而 lemma 使用了统一 conditioning sigma-field 下的 centered score 条件 p moment。二者不自动等价。

更细致地说，若 `e(X)` 可以任意接近 0，且 q 对该稀有动作有固定正质量，则条件于 X 的重要性权重 p moment 含 `e(X)^(1-p)`，可能没有统一有限上界，即使对 X 积分后的无条件矩有限。例如 e~Beta(a,b) 且 `a>p-1` 时 `E[e^(1-p)]` 有限，但 `sup_x e(x)^(1-p)` 仍无限。

**修复**：分别陈述三种情形：(A) 随机设计、无条件有限 p-moment 的 graph model；(B) 条件设计、由已知 e 和 bounded Y 推出**有限样本可计算但可能很大的** ν_p；(C) 固定有限 `e_min` 的弱但非零 overlap。不要将 A 的矩界直接代入 B 的定理。要明说 ν_p 可能依赖 N/设计，从而影响所谓固定率。

### P0-4：可计算的 95% CI 还没有完全闭合

**位置**：`03_method.tex` 的 `r_W`、`04_theory.tex` 中 `C_p`。

当前 half-width 含 `C_p`、`nu_p`、`r_nuis`、`r_coup`、`r_drift`。但许多情况下：

- `C_p` 不是一个已经实现的显式常数；
- `nu_p` 从重尾 observations 中的经验 plug-in 不自动是高概率上界；
- `r_nuis` 的真实 μ/e 误差通常不可观测；
- `Delta_W` 由未知的 counterfactual block means 构成，不能简单由样本 drift proxy 上界；
- coupling failure `epsilon_coup` 在目前证明里是**额外失效概率**，不是加在数值半径上的 `r_coup`。

**修复**：把 certified mode 与 empirical/sensitivity mode 分开。保守主模式使用已知 exact e、独立 pilot、已证明的 finite-p/graph/time 模型和显式 ν_p。在 bounded Y 的 OBD 二分类情形，可以利用已知 q、e、界限 `[0,1]` 计算条件矩上界。对于完全未知的 p 和 ν_p，不应该直接宣传 distribution-free 自适应 95% 覆盖。

可以尝试用 von Bahr–Esseen（常数 2）两次、Markov 1/8、K 个 MOM 组多数事件得到可运行的保守常数。之后研究是否通过额外假设/新理论把它收紧。**图中的宽度、abstention 和保守性必须展示，不能只报 coverage。**

### P0-5：下界证明确实有一个错误不等式，但易于修复

**位置**：`appendix.tex` 第 187–197 行。

原文称 `E|X-E X|^p <= E|X|^p`，对 1<p<2 一般不成立。反例：X~Bernoulli(0.1)，p=1.5，中心矩约 0.11384，大于原点矩 0.1。

令 n=N/χ；ε=1/(2n)，a=ν_p(2ε)^(-1/p)，P0=δ0，P1=(1−ε)δ0+εδa。则中心矩不超过 `2ε a^p=ν_p^p`，两点均值差 `εa=(ν_p/2)n^(-(p−1)/p)`；n 次采样乘积分布 TV=`1-(1-ε)^n` 不会接近 1。完成 Le Cam 可以保留阶数。一定要说清：这是 χ 个完全相同拷贝所组成的 clique subclass 下界，不是每一类稀疏图的精确下界。

### P0-6：没有观测到依赖，不代表不存在依赖

**位置**：`02_setup.tex` 的 conflict graph，附录第 162–179 行。

同 slate、同 user、明确网络邻居等可给出一张由设计构建的图，但未观测的公共冲击、永久 user random intercept、或长程共同状态也会引入边。只凭 ID 就说“图是完整依赖图”，没有统计保证。跨块的同一用户如果长期带有未建模 random intercept，加入有限 guard gap 也未必能独立。

**修复**：graph 是 **declared sufficient dependency model**，不是“日志可自动证实的真图”。严格实验使用可控真图；故意删边和引入永久隐藏冲击做 negative control。真正的 χ 是图色数，用 greedy coloring 时用实际使用的颜色数或可证明上界，不可把近似着色当最优色数。

### P0-7：时间 coupling 必须明确以失效概率计价

若 stationary β-mixing 且有可信的 `β(ℓ)` 上界，则 block coupling 失败概率可以控制为 O((B−1)β(ℓ))。如果目标是 95%，不能同时使用 `δ_stat=0.05` 又保留额外 `ε_coup>0` 却仍声称 95%。应满足 `δ_stat+ε_coup<=0.05`，或者有另一项经过证明的数值误差界。`β(ℓ)` 只靠 autocorrelation 或数据拟合通常不可能获得严格的有限样本上界。

### P0-8：群体比例分母和 estimand 需要统一

**位置**：`03_method.tex` ratio certificate。

若 h 是评估窗口内已观测、pre-action 的二元 slice indicator，且目标确实是**这条 realized path 上的平均**，那么 `π_W=(1/N)∑h_u` 已经知道，没必要假装需要估计 `E h`。如目标变成总体分布上的 `E h`，需要另一个 population-level concentration statement。更重要的是，群体规模非零不意味着 q 所需的稀有 exposure 有效支持；仍需检查 q/e 分布、矩界和 abstention。

### P0-9：policy repair 只保证已认证的 target，不保证改变策略后的整个未来路径

**位置**：`05_discover_repair.tex` 的 proposition。

命题代数本身在 simultaneous CI event 上成立。但该 event 对应哪种 `V(q), C_j(q)` 非常重要。如果是 observed logging-history 的 one-step intervention moment，则只能声称“在该参考分布/窗口下、对被冻结候选库的高概率约束可行性”，不能自动说新 policy 上线后用户反馈改变、图演化改变时始终安全。建议在动态 simulator 中**分别画出 logged-path certified risk 和 closed-loop deployed risk**，将后者作为额外诊断，不冒充主 theorem。

### P0-10：slate 概率不能用 item softmax 直接替代

**位置**：`06_experiments.tex` 的 `(1−epsilon)Softmax + epsilon UniformTopK`。

Softmax 通常给单个 item 的分布，而 UniformTopK 是整个 K-slate 的分布。两个概率空间必须先统一。采用明确的 complete-slate logging policy（例如 Plackett–Luce + uniform slate mixture），再对 local exposure mapping `S=g(A)` 求**真正的边际 probability e_u(s)**。小 M/K 的枚举单元测试是必做事项。若 S 包含邻居 exposure，还要对联合 assignment 求和。

### P0-11：有限 p-moment 的速率是上界，不等于所有模拟的真实斜率

对 t-分布自由度 ν>p，实际可能有 ν 比 p 更强的矩性质；误差随 N 的斜率可能比理论保证的 `−(p−1)/p` 更快。用固定 ν 的图只能说明随 N 缩小的趋势，不能强迫拟合斜率恰好等于理论 p。真正对准 minimax rate，应使用随 n 改变的 rare-contamination Le Cam 两点困难实例，并在 P0/P1 上比较最大风险。

### P0-12：novelty 应与更强先前工作正面对照

现有工作有：Waudby-Smith 等的 adaptive/时变 OPE confidence sequences，Mineiro 的 heavy-tail changing-mean confidence sequence，ICML 2025 的 uniform finite-p MOM，以及 dependency graph concentration。COMET 可以新在 **已知局部干扰图下的反事实 moment 族认证 + 多策略/多 auditor + abstention/repair 的统一实现与误差分解**，但不该泛称此前不支持 adaptive time-varying OPE 或 weak overlap。建议至少纳入一个与该类 CS 方法同假设的强基线，明确哪些场景你的方法适用/不适用。

### P0-13：即使证明修好了，理论创新点也可能偏“已有模块的组合”

这是论文层面的风险，不等于研究不值得做。当前定理可概括为“DR score + 图着色的 von Bahr–Esseen + 独立 block MOM + union bound”；下界是经典 heavy-tail two-point lower bound 的 clique replication；discover/certify 是样本分割；repair 是标准悲观优化。单独看，这些部件都比较成熟。顶会审稿人可能追问：**哪一个结论是已有方法不直接给出的？**

建议选一条主线并集中强化，而不必全部做：

- **方向 A（优先考虑、理论难度最高）**：真正针对 adaptive/pathwise conditional target，证明允许每轮局部图依赖的有限 p-moment prequential certificate（例如 martingale + predictable robustification）。这样比只会处理 offline independent blocks 的故事更完整，但要正面比较已有 anytime-valid OPE/重尾 CS。
- **方向 B（更易落地）**：对于 bounded rewards + known exposure e，构造实际可计算、无需 oracle tail scale 的 graph-aware simultaneous radius；探索比 `max χ` 更细的 per-block/fractional-coloring design effect，证明在异质图上显著更紧而仍有 valid coverage。
- **方向 C（应用与算法贡献）**：在可证明条件下给出 hidden-auditor discovery、ratio abstention 与有限 policy library repair 的统一 simultaneous guarantee，且实验展示一个基础 OPE CS 无法处理的 interference/local dependency 实例。

不要在摘要中同时夸大 A、B、C。必须有一个新的、可复现且不是仅仅“组装”的核心优势。

## 2. 实验主架构：先数学可证，后真实复杂

### 三层环境

| 层级 | 数据和模型 | 主要用途 | 能否称理论 CI |
|---|---|---|---|
| A | 独立 macro-block；已知 cliques χ；exact e；独立 pilot；已知 ν_p；固定/合法条件目标 | 主定理 finite-sample coverage、rate、下界 | 是，只要所有条件和常数闭合 |
| B | DCSBM/PA 真实结构；有限记忆或已知 Markov coupling；局部 interference；可声明 drift bound | 图/时间结构与改进的外推 | 按是否满足并证明条件逐项判断 |
| C | 忽略全局 latent shock、错误 graph、crossfit leakage、未知 drift、错用 e | 识别假设边界和假安全 | 不可以，必须标记违规对照 |

### 主实验 S1：四个机制组合的 coverage

1. strong overlap + light-tailed Y：所有合理方法接近 nominal，COMET 可能更宽。
2. weak overlap + bounded Y：拆出 importance-weight induced heavy tails。
3. strong overlap + heavy-tailed Y：拆出 outcome-induced heavy tails。
4. weak overlap + heavy-tailed Y：叠加最难情形。

建议固定比较 90%/95%，每个最关键 cell 至少 1000 independent replications；其他 sweep 至少 300 repetitions；调试先 50–100。对于 `R=1000`，95% 左右的经验覆盖率二项标准误差约 0.69 个百分点，90% 左右约 0.95 个百分点，应显示 Wilson 95% 区间。不要凭一次 50 次抽样声称“显著覆盖更好”。

建议 N={8192,16384,32768,65536}；B=128，n0=N/B；χ∈{1,2,4,8,16}；p∈{1.2,1.5,1.8,2.0}；q/h finite family 16 个。`δ=.05, |Θ|=16` 时 `K=ceil(8 log(640))=52`，需 `B>=104`；分成 52 组时不能无说明丢弃不整除 block，必须按证明处理 2/3 块不等组或调整 B。对 N、χ、p、epsilon **分开 sweep**，不要全因子组合造成巨大计算量。

**每个方法至少报告**：mean estimate/median absolute error、90/95 marginal coverage、90/95 simultaneous FWER coverage、mean/median CI width、worst-case policy-auditor coverage、issued certificate fraction、abstention 原因、ESS 与 N_eff、q/e 高分位数、时间内存、Monte Carlo uncertainty。

### 主实验 S2：χ 是否是真实统计惩罚

把每个独立 latent sample 复制 χ 次构成 clique，保留 N 原始记录但只有 n=N/χ 个独立源。理论 graph coloring 的 χ 可精准构建。固定 N、改变 χ={1,4,16}，比较若误把行数当独立样本的 Wald/iid MOM/time-only 与 graph-time 的 CI coverage/width；再转而以 N_eff 作横轴，检查曲线是否更接近重合。加上 clique hard-instance lower bound，而不是只画趋势。

### 主实验 S3：理论速率与最困难实例

固定 p 和 ν，在 P0=δ0、P1=(1−ε)δ0+εδa 中令 ε=1/(2n)、a=ν(2ε)^{-1/p}，n=N/χ。对 n={256,512,1024,2048,4096,8192} 多次采样，在两个分布上计算 `max(E_P0 |Mhat−0|, E_P1|Mhat−εa|)`；对照 n^{-(p−1)/p}。此实验用于证明下界阶数在构造子类中不可避免，而不是假设任意 Student-t DGP 都有同样斜率。

### 主实验 S4：分解组件消融与负例

比较 DM / IPS / SNIPS / ordinary DR / clipped DR / switch DR / iid MOM-DR / time-only MOM / graph-corrected mean / graph-time MOM / 已有的有效 martingale/CS 基线（同条件下）。对各个 ablation 标注其 CI 是否有已证明的保证。隔离变量：exact e vs estimated e、correct vs misspecified mu、正确图 vs 删除边、足够时间隔离 vs 无隔离、MOM vs mean、正确 ν envelope vs 不合格经验 plug-in、认证独立 nuisance training vs 行级交叉拟合、低 drift vs 未声明 drift。**不能因为 empirical coverage 在某些 cell 超过 nominal，就在所有模型上声称 valid。**

### 主实验 S5：Discover–Certify hidden subgroup

设置对 fixed one-way/group bins 不可识别的组合条件，例如 `(group=1) AND (degree in top 20%) AND (new user) AND (pre-action observed regime=high)`，通过生成器校准真实支持率为 2–8%；额外设 0.2–1% 的难例。植入显著效应与完全无效的 null。使用 depth≤4 tree 或解释性规则在 discovery 上找 top L；冻结 L 个规则，在独立认证窗口检验并付 log L penalty。

对照：固定 slices、直接在训练集报告最大差异（错误基线）、普通 row-wise split、graph/time-separated split。指标：发现规则与真 subgroup 的 Jaccard、发现集上的效应、认证集效应与置信区间、null familywise false alarm、power、abstention、随 drift 的复验情况。**最有价值的图**是“发现上看似很严重的 violation，独立 cert 上是否真的仍显著”。

### 主实验 S6：Pessimistic repair

事先冻结候选 q library（混合探索、群体偏移、阈值等）及风险限制 alpha。对照 utility-only、只用点估计约束、clipped-DR 约束、静态安全保守 policy、COMET 的 `maximize Vhat−rV subject to Chat_j+rCj<=alpha_j`。看真实效用、真实约束超标幅度、false-safe probability、拒绝认证比例，以及相对“带 2r margin 的保守可行比较策略”的 utility gap。

如果 fairness constraint 是 `|group gap|<=alpha`，需要两个方向同时控制或严格有效的 absolute-bound，不能只将有符号 gap 的一侧当完整 fairness 约束。额外展示：随着 N_eff 提升，证据是否足以允许更多 utility 较高的 q；和随着有效 overlap 降低，COMET 是否正确地更常 abstain。

## 3. 数据集优先级与可信边界

### TGB-v2：中高优先，强调图真实而反事实真值为模拟

`tgbl-wiki-v2` 优先，review-v2 次之。保留真实 graph/time/id/degrees，但自行定义 randomized policy + potential outcome + oracle truth。必须明确：TGB 本身没有为你的假设提供随机化 logged exposure 概率，原始 edges/negatives 不是因果 potential outcomes。使用官方版本和时间 split，并单独报告人工 logging/exposure 模型的参数。

### Open Bandit Dataset：高优先，强调真实 propensity 而 Y 为二元

同一 campaign/position 上 random↔BTS 评价。它提供 item-at-position 的 behavior propensity（对完整 slate 的 joint e 未必充分）；真实 target-policy on-policy sample mean 有抽样误差，不能直接视为无误差 truth。要对时间和上下文分布作检查，且处理 BTS target action probabilities 可能通过 MC 近似的误差。此数据主要验证 importance-weight tails 和真实运营环境下的 interval width/abstention，**不能给它贴上“有精确真值的 95% coverage 实验”**。

### KuaiRand：P1 补充，可延后

官方说明随机替换片段占比约 0.37%，并非所有推荐 impression 都来自完全已知随机策略。重点是重复用户、序列 feedback、随机曝光部分的 holdout 验证与不可认证时的正确拒绝。watch time 重尾分析需明确是否截断、归一化及其对 estimand 的改变。主论文篇幅紧张时可放 appendix。

## 4. 推荐的主图与主表

- Figure 1：四种机制下 90%/95% 覆盖率 + Wilson error bars + certificate issuance/abstention。
- Figure 2：固定 N 不同 χ 的 coverage/width；对照 N vs N_eff。
- Figure 3：finite-p fixed DGP 经验率（注明可快于理论），加上 Le Cam 随 N 变的难例下界。
- Figure 4：graph/time/nuisance/drift/moment envelope 各项消融；违规条件标红或标记 invalid。
- Figure 5：hidden subgroup 的 discovery 过拟合 vs cert replication、null FWER/power。
- Figure 6：policy repair 的真实 utility vs max violation、feasibility/abstention frontier。
- Table 1：主 estimator 对照，标注 certified/sensitivity/heuristic。
- Table 2：假设表：哪些能从 logging 协议核查、哪些必须声明不可检验。
- Table 3：TGB semi-synthetic vs OBD（truth 类型、q/e、coverage/width/abstention）。

## 5. 我的执行优先级

**第一轮（最关键）**：修 proof/model 断层和下界错误 → 实现 exact e、独立 pilot、已知 ν 的 oracle-model 95% CI → 运行四机制×图 clique 主 coverage，含置信区间与 abstention。没有这一步，其他结果即使很多，也撑不起主 theorem。

**第二轮**：Graph/time/弱 overlap/重尾 消融和 Le Cam lower bound → 独立 discover–certify → 以 CI 为约束做 pessimistic repair。

**第三轮**：TGB-v2 semi-synthetic → OBD → KuaiRand（可选）→ 修正文稿和写可复现实验 Appendix。

在实验完成之前，不修改 abstract 让它声称已经证明通过 95% coverage 或得出真实收益；所有数值必须来自独立重复试验和固化配置。

## 6. 相关文献与官方数据资料（建议 Codex 核查并补 BibTeX）

1. Waudby-Smith, Wu, Ramdas, Karampatziakis, Mineiro. *Anytime-valid off-policy inference for contextual bandits*. https://arxiv.org/abs/2210.10768
2. Mineiro. *A lower confidence sequence for the changing mean of non-negative right heavy-tailed observations with bounded mean*. https://arxiv.org/abs/2210.11133
3. Høgsgaard, Paudice. *Uniform Mean Estimation for Heavy-Tailed Distributions via Median-of-Means*. https://proceedings.mlr.press/v267/hogsgaard25a.html
4. Janson dependency graph inequalities（核查原始论文、特别是 fractional chromatic number 与适用的 bounded/finite-p 假设）。
5. Official TGB docs: https://tgb.complexdatalab.com/docs/linkprop/
6. Official Open Bandit: https://github.com/st-tech/zr-obp ; https://huggingface.co/datasets/zozonext/open-bandit
7. KuaiRand: https://kuairand.com/

**与 Codex 实施指令配套文件**：`CODEX_COMET_MASTER_TASK.md`（英文、逐阶段 Gate、具体文件结构/公式、单元测试、结果验收标准）。
