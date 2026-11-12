# COMET Gate C0 之后：研究优先级与实验验收说明

## 目前的研究状态（来自用户汇报，非独立代码审计）

- Gate C0 PASS；377 项测试通过；210 次 CPU pilot，30/30 coverage 的 Wilson 95% 区间为 [0.8865,1]，不能视为 95% coverage 的最终证据。
- 95%、N=8192、m=1：原 MOM 半径 1.41421，截断区间覆盖 100% 可行范围；精确二项 MOM 半径 0.43644，宽度 87.29%；有界图方差 Chebyshev 半径 0.04941，宽度 9.88%。
- m=16、N=32768：有界图方差区间宽度中位数为可行范围的 26.89%。
- 适用定理仍是独立外生宏块与 exact e；不包含一般自适应路径、互训 cross-fit、未知 scale/drift、长期部署安全。
- 最新本地 Gate C0 报告未随当前请求上传；已连接的 GitHub 账户访问给定 COMET SHA 与报告返回 404。因此以下是以用户报告、原始论文及之前 Gate C0 实验规范为依据的研究决策，不声称验证了最新代码。

## 为什么不直接给所有格子各跑1000次

1. 95% coverage 是置信区间统计有效性的必要验证，但**完全空泛区间也有 100% coverage**。
2. 当前 graph variance 的 m=16 宽度约 26.9% 可行范围，是否能支持“安全”或“违规”认证还依赖真实 constraint gap。必须直接研究 power、false-safe、false-violation、abstention。
3. Bounded graph variance 与 finite-p MOM 的假设不同，前者不能证明重尾 Y 的保证。强行合并容易误导论文贡献。
4. 增加相关图结构、弱 overlap、尾部与 auditor 数量，必须保持每个单元对照只变一个机制，避免归因困难。
5. 论文原始叙事是随反馈演化的动态审计；现有主定理覆盖的仅是独立外生块模型。后续模拟“闭环在线”可做 exploratory，不能写成 theorem-certified。

## 核心实验表

以下同一轮数据同时计算 90/95 区间；每核心格 1000 次独立重复（独立于先前 210 次 pilot）：

|格子|N|m|依赖|Overlap|Y|重点|
|---|---:|---:|---|---|---|---|
|A|8192|1|chi1|强|有界|基本有效性、非空泛|
|B|32768|16|chi1|强|有界|同时认证、多重比较|
|C|32768|16|chi4 clique|强|有界|图校正必要性|
|D|32768|16|chi1|弱|有界|exact-e 下真实弱 overlap|
|E|32768|16|chi4 clique|弱|有界|结构与 overlap 相互作用|
|F|32768|16|chi4 clique|强|有限 p=1.5 重尾|只有合法 MOM 参与|

每格另存所有方法的 coverage、Wilson、width/diameter、median |error|/radius、nonvacuity、abstention、false-safe 和 exact-e ratio tail。如果未满足任一证书的全部假设，标记 NOT_APPLICABLE，不输出伪 certified 结果。

**防止错误判断：** 不要把 1000 次中观察到的覆盖率必须 >=95% 作为单一通过标准。报告 Wilson 区间；用预注册的单侧精确二项检验排查 undercoverage，跨主要格子使用 Holm 调整。没有显著 undercoverage 不等于证明覆盖率正确。

## 论文最重要的两组非覆盖率实验

### A. 隐藏子群发现 / 独立认证

按用户组、度数、新用户、潜在 regime 的四重交互植入真实 counterfactual violation。合理控制 prevalence：2%、5%、10%、20%；改变效应大小，固定模型与真正的潜在结果均值。Discovery split 不得复用 certification outcomes；Top-1/5/10 规则在评估前冻结并按照实际 family size 支付统计预算。

测：找到 planted h 的频率、发现后独立认证率、null 下的 any false certified violations、空泛/放弃率与时间成本。仅仅“发现一个高分组”不足以证明审计有效。

### B. Policy repair

冻结 8/16/32 个候选策略，2–4 个效用/安全/公平性约束。比较 utility-only、DR point constraints、clipped DR point、COMET pessimistic certificate 和事后 oracle。指标包括 true utility、true max violation、false-safe selection、abstention、fraction certifiably feasible、oracle regret。

原命题的 comparator 要求 **C_j(q)+2r_j(q)<=alpha_j**；不能声称在所有真正可行的边界策略上都有相同 regret 保证。

## 大幅度额外改进（建议但不是阻塞 Gate C）

有界 Y + known exact e 的 graph Chebyshev 对 m=16 区间仍可能偏宽。可以在独立块模型下探索 block-Bernstein / bounded-variable concentration，使置信参数依赖 log(m/delta) 而非 Chebyshev 的 m/delta；必须有设计已知的 block range bound，且证明条件方差、独立性、目标对应的全部条件。任何由 outcome 选出的最短区间都需要额外多重性处理。这不是“替换常数”的轻易改动；应先写 proof，再实现。

更大的理论价值是建立 predictable martingale 版本以处理真正 adaptive pathwise counterfactual target，建议命名 `T1` 单独排期；当前 Gate C 不能假装已经完成。

## 数据阶段

Gate C 前半应优先合成。真实拓扑可在通过后使用 TGB `tgbl-wiki-v2` 做半合成：保留真实时间/节点结构，自行生成可核验的 exact e、合法的 exposure mapping 与 Y(s)。真实图结构本身不自动证明误差只有所画图的依赖。Open Bandit 的真实日志要核查 e 的口径、干预目标、跨时间依赖和 on-policy reference uncertainty；如无独立块证明，只能探索性报告。

## 交给 Codex 的启动方法

先把 `CODEX_COMET_GATE_C_MASTER.md` 放进实验仓库并要求 Codex 只做 **C-PREFLIGHT**：核对 C0 真实报告和证明、冻结 protocol、建立独立 oracle、核对 DGP、跑小规模预检并输出 PASS/BLOCKED。只有预检通过才真正启动每格 1000 次确认性重复。C-STAT 完成后再进入 auditing 和 repair。避免一次性开发并运行全部实验导致难以追责和复现。
