# COMET：2026-11-12 GitHub 实际代码／理论审查和实验决策

审查锚点：实验仓库 `lsnnnnnnnn/COMET` commit `06a39b89e579aef57d14ae51e86d74ecf9b6b768`，科研代码／冻结配置 commit `ab4c74fbf1ae84c0e5ffd72d77ce5b48d3fba8cb`；报告 `reports/gate_C_report.md`、`gate_C_preregistration.md`、`gate_C_statistical_summary.md`，核心 `comet/gate_c_{contract,methods,simulation,statistics,truth}.py`，`theory/{theorem_to_code_contract,exact_binomial_mom,bounded_graph_variance,lower_bound,gate_c_heavy_tail_contract,proof_gap_report}.md`，以及仓库 `paper/sections/*.tex`。独立的 `COMET_overleaf` 仓库当前无法读取；纸稿依据实验仓库保存的 `paper/`。

## 结论

**严格限定在固定外生设计、相互独立 evaluation macro-block、充分 conditional dependency graph、精确 exposure propensity、固定／独立 pilot nuisance、固定有限 family 和已知条件 moment envelope 的模型时，现有 MOM、exact-binomial 分组和 bounded graph Chebyshev 推导经核对没有发现新的致命数学错误。** 这不是对所有函数、所有自适应部署历程、所有网络或一般现实数据的自动保证。当前 C-PREFLIGHT 的 12 个日志不能用于确认覆盖率；冻结的 6,000 个确认性种子未运行。472 通过的测试说明实现质量，但不替代数学证明和实证。

**作为论文，现有表述仍不成立：`paper/main.tex` 摘要、`paper/sections/01_introduction.tex`、`02_setup.tex`、`03_method.tex` 以及 `04_theory.tex` 的原广义定理将 adaptive path、mutual cross-fitting、未知 drift/coupling、可学习 tail scale 同已证明结果混在一起。尽管 Gate A 加入 scope notice，并明确说原广义定理 unproved，真正的投稿论文不能在正文中保留一个标为 theorem 的未证明结论。** 应将已证的独立宏块定理升级为主定理，原广义定理降级为单独明确标注的 future research question。

## 数学／代码核对

### 正确且有明确适用范围

1. **Exact-e DR**。对预先固定的 `mu_hat`，`Z=h[sum q mu_hat-f+q(S)/e(S)(Y-mu_hat(S))]` 在随机化和一致性条件下以 `M_D` 为期望，不要求 `mu_hat` 正确。代码 `comet/gate_c_methods.py::_score_arrays` 与 `gate_c_simulation.py` 的日志相符。此性质不适用于把 evaluation outcomes 偷偷用于训练同一 scoring path 的模型。
2. **Graph variance**。在 `Y,mu_hat∈[0,1]` 时 `v_u=h_u²∑_s q_u(s)²/e_u(s)` 是合法的条件方差上界；每 block 充分依赖图 + χ coloring 给 `Var(sum Z_b|D)≤χ_b∑v_u`；独立 block 汇总给 `V=N^{-2}∑χ_b∑v_u`；`sqrt(mV/δ)` 经 Chebyshev + union 给同一方法、同一 confidence level、同一固定 family 的 simultaneous CI。这是标准但正确的推导。
3. **Finite-p MOM**。两个 von Bahr–Esseen 步骤得到组矩常数 4；Markov 与失败率 `η=1/8` 得 `32^(1/p)`，针对 stable block means；exact binomial tail 选择 odd K，独立 but non-identical bad group indicator 可被 Bin(K,η) 支配；m=16,δ=.05 时 K=9。**这个改进没有改变原始有限矩的巨大常数。**
4. **Heavy-tail F**。对理想对称 Pareto `α=1.75,σ=.1,p=1.5`，`E|ε|^p=α σ^p/(α-p)`，代码推导的条件 score envelope 有效且由模型类／设计提供；图方差证书正确拒绝 F。此处指定了 noise law 和 tail scale，因此不代表真实数据能未知尺度自适应。
5. **Le Cam 下界**。明确是 exact clique-replication subclass 的期望绝对误差下界，常数 1/8；不是所有 sparse graph 的下界，也不是 simultaneous high-probability CI 下界。若要称之为反事实下界，应在正文中说明可通过 `S=q=e=1` 的退化 exposure 模型嵌入一般均值估计。

### 核心科学／表述缺口（按严重度）

- **P0：原 paper 主定理仍 unproved**。`04_theory.tex` 中仅在 Gate A scope paragraph 指出问题，却继续正式陈述泛 adaptive theorem。摘要与算法仍把 cross-fitting、drift、coupling 作为已有操作保证。应删除未证 theorem 的 theorem 环境。
- **P0：Dependent feedback 目前没有实验或定理**。主 simulator 的依赖是独立 clique record 的 χ 次完整复制，未模拟随反馈自适应变化的 context、slate 或真正邻居干扰。论文标题／核心主张要收窄，或先补新定理／新生成器。
- **P0：F 重尾证书全部空泛**。按当前 F 参数，q∈{.1,...,.9} 的 MOM raw half-width 解析值约 5.28–5.96；支持目标直径 all=1/group1=.5。固定 B=128、m=16、χ=4、p=1.5，仅增 n0 以达 all 的 r<.5，按现有半径公式需要 N 约 3,800 万至 5,500 万。不可将其作为已经有实用 heavy-tail inference 的证据。
- **P0：Power / repair 尚未实验**。B 的 70% detection 是两次日志中 candidate-level 计数，16 个 candidate 相关；不能作为独立重复的 70% power。A 格真值 .2375、阈值 .2、gap .0375、95% r .04941，所以非空泛区间仍会 abstain。
- **P1：真正 weak overlap 尚不充分**。D/E 的 e1=(.01,.02) 在每个固定设计仍有正下界。定理无需全局 uniform e floor，但实验仅覆盖固定有限 e。另做 e_min(N)→0 或随机重尾 exposure design 的独立预注册敏感性试验；每次须给已实现的条件 envelope，不可以只用 integrated moment。
- **P1：当前 auditors/policies 太简单**。B–F 的 m16 是常数 q1 的 8 个点 × all/context1 两个 auditor；未验证 contextual q、复杂隐藏 subgroup、calibration、spillovers、实际 cost/utility tradeoff。
- **P1：局部 q 的全局可实现性**。当 exposure `S_i=g_i(A)` 来自 joint slate/network assignment，随意指定每单位 `q_i(s)` 未必能由同一合法 joint target policy 诱导（例如两件商品竞争一个唯一展示位，却都指定 shown probability=1）。要么明示 estimand 是 exposure-marginal functional 而非全局可执行策略值，要么强制 `q_i(s)=P_{A∼Q}(g_i(A)=s)` 并给出 joint-law 构造／检查。
- **P1：没有独立 nuisance pilot 的经验能力验证**。fixed `(0.5,0.5)` 使 DR 数学上无偏、协议上安全，但不能支持已实际实现且测试了 learned cross-fitting 的印象；增加 pilot-trained mu_hat 的严格独立 split 是较容易的下一步。
- **P1：非平凡覆盖与证书选择**。所有方法分别 95% 不表示可以看 outcomes 后选最短证书仍为 95%；必须 design-only selection（证明）或交叉方法联合预算。
- **P1：现实数据外推**。TGB 半合成只有随机化机制与真实图拓扑被保留时才可能证明设计条件；原始图边并不自动等于充分的 stochastic dependency graph。Open Bandit / KuaiRand 的一般时间依赖不能未经证明套独立宏块 theorem。

## C-STAT（已有冻结确认性协议）：现在可以执行，但必须严格冻结

官方六格 A–F 各 1000 独立 replication，共 6000，90%/95% 共用同一 log；17 项预注册 95% undercoverage 诊断 Holm 校正。原始 `configs/gate_C_frozen.json`、`configs/gate_C_seed_manifest.json`、候选 family、oracle、科学算法均不得按确认性 outcomes 修改。单方法 within-family 的 coverage 只以 `(cell,replicate)` 为独立单位，不把 16 个 candidate 当 16 次独立重复。原本 `experiments/gate_c_preflight.py` 明确只能 preflight：需要新 confirmatory-only runner，重用同一冻结 science source，用相同算法从 manifest 获取 `phase=confirmatory` 的种子，另存 `results/gate_C/confirmatory/`，以及独立 schema/provenance。**禁止通过改原 frozen config 中 `phase_authorized` 或改旧 runner 的 phase 名称来蒙混通过。**

需要特别注意资源：B–F 每次约 16 candidates×7 methods×2 levels=224 records；A 每次 14 records；6,000 次共计 **1,134,000 条 candidate records**。原 preflight runner 最后把全部 checkpoint 读入内存；确认性版本应改为分块流式汇总、压缩持久化，不能一次性加载所有 records。测试 checkpoint 恢复、source fingerprints、数值完全一致；并检查磁盘剩余空间和单元／进程峰值内存。

**主终点**：95% full-family coverage，逐方法分别报告 successes/1000、Wilson CI、17 个预注册 undercoverage lower-tail p 和 Holm。90% 次终点。**实用性端点**：raw vs feasible-intersected width、nontrivial `some/all/marginal`、correct safe/violation/abstain、candidate-specific signed error、ratio `|error|/radius`、processing cost。适用状态中 F graph method 保留 `NOT_APPLICABLE`，IPS/DM/DR 保留 `POINT_ONLY`；不得填充假 CI。`full_feasible_range` 只是 deterministic class range，不是有效统计收敛 baseline。零例假安全不能等同于未来安全证明。

无 outcome-dependent stopping：可因资源故障而暂停再 resume；不能先跑部分 confirmatory logs 看结果再改变方法参数、挑好看的 cells 或删除失败 run。Holm 没有拒绝欠覆盖不等于统计上证明达到 95%；理论负责有效性，模拟只是排查假设／实现错误。

## 在完成 C-STAT 之后应做的三组真正推动论文的实验

**D1：违规幅度—认证功效。** 独立注册新的种子／模型版本。由生成器设置独立于数据的 true signed gaps `γ∈{0, ±.025, ±.05, ±.10, ±.20}` 以及相对已知理论半径的 `γ/r∈{.5,1,2,4}`；设 2%/5%/10%/20% subgroup prevalence、m=1/16/64、χ=1/4/8、e=strong/weak。每个 replication 统计 `any false-safe`、`any false violation`、`any correctly certified violation` 以及 abstain，另画每候选功效曲线；用 replication 级 bootstrap/Wilson，不将候选视为独立样本。加入 all-null 和 boundary null，防止只有强替代下好看。

**D2：Discover–freeze–certify。** 生成四维 hidden subgroup，effect 嵌入真实 `μ_u(s)`；发现阶段只用独立 pilot blocks，冻结 Top-L, L=1/5/10，认证阶段用 fresh independent blocks，按实际 L × policy × constraints 计算 family budget。比较 coarse predefined auditors、in-sample search（明确 invalid）、split search naive graph CI、合法 graph certificate。报告 subgroup recovery precision/recall/IoU、认证 power、null FWER、宽度与样本成本。不能用 evaluation labels 或 oracle 选择候选。

**D3：安全策略 repair。** 必须设计两个 outcome channels 或至少 distinct utility/cost potential outcomes，使 safety cost 与 utility 有冲突，不能用单一 M 的简单阈值包装成复杂决策问题。预冻结 Q 大小 8/16/32、2–4 个 constraints、真正可行及不可认证的策略、一个 truly-safe fallback 和无证书可行的对照。一次性为全 Q×(utility+constraints) 支付联合 confidence budget。比较 utility-only、point-DR constraints、clipped/SN point constraints（无 theorem）、COMET pessimistic selection、hindsight oracle（仅测量）。主要输出 true utility、true violations、false-safe selected policy、abstention、regret vs robust-margin comparator 和 vs truly feasible oracle，并解释二者不同。

## 可选但建议的加强实验

- **依赖结构非复制**：构造 block-local independent edge shocks、randomized slate 或邻居 exposure。每个 score 的 stochastic primitive support 必须可列举；共享 primitive 产生 conflict edge，验证任意无边不相交集 independent，块间独立。真实网络邻接不自动作为充分图；需要从 primitive 的依赖构造图，报告 χ 与实际收益。
- **Weak overlap**：附加 e_min decreasing with N、条件 J_p 与 runtime/nonvacuity，区分 `q>0=e` 的非识别。
- **重尾**：保留原 F 负面结果；附加多个 α/scale/p/N 的可行性地图与 honest sharpness 方法，先用 design-only algebra 防止昂贵无用实验。可研究 design-only η,K 优化，或者带完整偏差预算的截断／robust score，但不得把未证明方法称为 certified。
- **独立 pilot nuisance**：在独立 pilot 上训练 mu_hat；独立 pilot 且 clip 到 [0,1]，固定 evaluation family；相较固定 0.5 分析区间、误差与 power。普通 cross-fit/estimated e 只能作为 exploratory，直到新 theorem 成立。
- **Rate**：固定 Pareto 误差斜率不需等于 p worst-case upper rate；用 N-dependent Le Cam rare-event family 检查最坏率，但明确这不就是 COMET CI 的 sharpness proof。
- **真实图**：通过门槛后才做 TGB 半合成，不要先下载大量数据；Open Bandit/KuaiRand 如果不满足独立块条件，报告描述性 OPE 不能声称 certified。

## 论文结构重写

1. **Abstract & Introduction**：第一屏改成现阶段确实证明的 exogenous block graph-dependent model、simultaneous moments 和 abstention；不要说已经处理 adaptive deployment/long-run feedback。若还想保留 adaptive 动机，单独写 future extension。
2. **Setup**：新主目标 `M_D(q,h;f)=N^{-1}∑ h_u[∑ q_u(s)μ_u(s)-f_u]`，D 的合法生成信息、精确 e、frozen Q/H、条件独立、充分图；明确完整 assignment exposure 和 q 实现条件。把原 pathwise `M_W` 放在 Motivation/Unproved target，与主 theorem 彻底区分。
3. **Method**：将原 cross-fitting (未证明) algorithm 换成 actual permitted fixed/independent pilot nuisance，明确两条 certified 方法（finite-p MOM vs bounded graph mean）；真实运行的 `CERTIFIED / NOT_APPLICABLE / POINT_ONLY / ABSTAIN`。
4. **Theory**：`thm:gate-a-clean` + exact-binomial corollary + bounded graph theorem 是正文主结果，附显式常数和半径，说明与 standard MOM/Chebyshev 的关系；原 adaptive theorem 从 theorem 环境删掉。下界只限 clique-replication expected risk。策略 repair proposition 继续保留，但前提条件不能扩大。
5. **Experiments**：正文用已运行的确认性实验数值；将预想中的 DCSBM/PA/TGB/Open Bandit/KuaiRand 标成 `future` 或在实际执行后再写 results。主表必须含 family coverage、width、non-vacuity、power、abstain、method applicability。展示 F 空泛及 E 重叠+依赖导致拒绝的负面结果。
6. **Discussion / limitations**：明确 unknown tail-scale 无分布自由有限样本估计保证、互训 leakage、隐藏 shocks、非真实历史适应性、exposure mapping／policy compatibility、closed-loop safety。
7. **Related work／novelty**：不要声称 DR、finite-p MOM、graph coloring 或 pessimistic selection 本身新；与 ICML 2021 off-policy confidence sequences、anytime OPE、2024 weak-overlap OPE、ICML 2025 uniform MOM 及 graph-dependent concentration 建立对照。需要补的是有效应用级 discover/repair、非复制图结构或 adaptive 新定理，才有较强原创性。

## 我的科研决策

**允许推进冻结的 C-STAT。不要在这之前修改原科学配置，也不要在纸稿中展示尚未获得的结果。** 同时并行准备一个 `paper/rewrite_proposals/` 分支的诚实定理版本（不直接覆盖独立 Overleaf 仓库）。如果确认性实验显示 MOM heavy-tail 仍全部空泛、graph-dependent 的强情境几乎全部 abstain，应如实写成适用性边界，不应只靠覆盖率或更多重复包装为成功。要达到一篇有竞争力的方法论文，下一关键不是更多 smoke tests，而是完成真正独立发现-认证、policy repair 和更真实的已证明依赖结构，或提出能处理 adaptive path 的新理论。
