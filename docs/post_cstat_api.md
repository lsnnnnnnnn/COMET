# COMET post-C-STAT API

核心入口是 `SignedQuery`、`SourceGraph`、`AssumptionContract` 和 `make_plan`。目标为

\[
M_D=\frac{1}{Na}\sum_u\left[\sum_s d_{us}\mu_{us}-o_u\right],
\]

其中 `coefficients=d`、`offset=o`、`normalizer=a>0`；策略水平取 `d=h*q`，paired contrast 取 `d=h*(q1-q0)`。归一化量必须是已知固定设计量，例如已知 subgroup mass；此 API 不认证估计得到的分母。

## 调用者必须建立的条件

- `exposure[u,s]` 是实际 logging law 的精确条件概率；不能把估计 propensity 或错误声明当成已知 e。非零 `d[u,s]` 必须有 `e[u,s]>0`。
- `1<p<=2`，且 `residual_moments[u,s]` 是合法的 **raw** 条件矩上界 `E[|Y_u(s)-muhat_u(s)|**p | D]`。它不是围绕未知真均值的 centered moment，也不是从 evaluation labels 估出的无保证经验矩。若确知 `Y∈[0,1]`，可用 `bounded_residual_moments(0, 1, fit, p)`。
- `graph` 必须在合法条件化 D 下对完整随机 score 全局充分：若使用 source-incidence 构造，基础随机源须联合独立，每行的 assignment/outcome 须由其列出的源和 D 生成。所有共享源都必须列出，包括跨行 logging dependence；共享同一源的所有行连成 clique。
- nuisance、候选策略、auditors、阈值和 tuning 必须固定于 evaluation outcomes 之前，或由合法独立训练/发现得到。`AssumptionContract` 的布尔值和 provenance 是调用者的声明；shape、source-ID 分离和 proper coloring 的检查不能发现 hidden shared shocks，也不能从 schema 证明独立性。

## 最小固定数组示例

下面只是无抽样的接口演示，不是实验、功效证据或协议冻结。声明模型为：每行独立 logging atom，成对行共享一个 response atom，不同 atom 联合独立，潜在结果有界于 `[0,1]`。实际使用时须以真实模型和真实日志替换这些声明与固定数组。

```python
import hashlib
import numpy as np
from comet.audit_pipeline import freeze_discovered_family
from comet.queries import SignedQuery
from comet.source_graph import SourceGraph
from comet.residual_truncation import (
    AssumptionContract, bounded_residual_moments,
    make_plan, certified_decision,
)

n, p = 8, 2.0
# Exact dyadic logging probabilities; heterogeneous fixed rows are allowed.
e = np.tile([[0.75, 0.25], [0.5, 0.5]], (n // 2, 1))
fit = np.full((n, 2), 0.5)                 # fixed before evaluation
b = bounded_residual_moments(0, 1, fit, p) # same legal bounds for all methods
q = np.full((n, 2), 0.5)
query = SignedQuery("risk/all", q, 0, channel="risk")
family = freeze_discovered_family([query])
graph = SourceGraph.from_sources([
    {("logging", u), ("response", u // 2)} for u in range(n)
])
contract = AssumptionContract(
    exogenous_design=True, exact_exposure=True,
    conditional_randomization=True, independent_nuisance=True,
    frozen_family=True, sufficient_source_graph=True,
    valid_residual_moments=True,
    graph_provenance="declared independent atoms; pair-shared response",
    moment_provenance="known Y in [0,1], fixed midpoint fit",
    conditioning_provenance="fixed contexts, nuisance, queries and tuning",
)
grid = tuple(2 ** (j / 4) for j in range(-24, 25))  # reconciled 49-point grid
common = dict(
    exposure=e, nuisance=fit, residual_moments=b, graph=graph,
    contract=contract, p=p, delta=0.05, multipliers=grid,
    outcome_bounds=(0, 1), mean_bounds=(0, 1),
)
plan = make_plan(query, **common, family_size=family.family_size,
                 method="comet_local")  # design-only; no observed Y here

actions = np.array([0, 1, 1, 0, 0, 1, 0, 1], dtype=np.int64)
outcomes = np.array([0., 1., 1., 0., 1., 0., 0., 1.])
data_hash = hashlib.sha256(
    actions.astype("u1").tobytes() + outcomes.astype("<f8").tobytes()
).hexdigest()
metadata = dict(data_digest=data_hash, seed_namespace="explicit-doc-fixture",
                code_hash="doc-not-a-frozen-protocol", config_hash="doc-fixture",
                numerical_guard=1e-10)
certificate = plan.evaluate(actions, outcomes, **metadata,
                            family_digest=family.digest)
decision = certified_decision(certificate, threshold=0.4)
print(certificate["lo"], certificate["hi"], decision)
```

`family_size` 必须覆盖选择时真正使用的全部 risk **和** utility 坐标；可先 `freeze_discovered_family(all_queries)` 去重，再以其实际大小给每个坐标分配 `delta/m`，不能只支付最终被选坐标。`channel` 和 `normalizer` 不同的坐标不会被当作同一坐标去重。拟合、发现或 policy selection 的正确条件化仍需独立证明。

`make_plan` 从合法全局图取该 query 非零支持的 induced graph；保留支持内共享源边，并使用已验证 proper coloring，未声称最优着色。`multipliers`、矩、图和支持的选择须只依赖 D；`tuning="outcome_based"` 等非 `design_only` 值会拒绝。有界方法须共享相同真实 residual range、e、fit、图、支持和置信预算。

`method="generic_matched"` 与 `"comet_local"` 在相同输入下使用相同代数、D-only bounded/truncation 分支和 endpoints；这是明确报告的等价，不是新颖性或胜出证据。可单独使用 `truncated_local`、`graph_hoeffding`、`graph_bernstein` 等已实现分支，后两者需要真实 outcome bounds。

## Direct paired contrast 与联合 level subtraction

复用上例的固定输入和同一日志：

```python
from comet.paired_contrasts import make_paired_queries, make_joint_level_family_plans

q0 = np.full((n, 2), 0.5)
q1 = q0.copy()
q1[::2] = [0.25, 0.75]  # unchanged rows have zero direct coefficients
paired = make_paired_queries("risk/policy-step", q1, q0, auditor=np.ones(n))
direct, level1, level0 = paired

direct_plan = make_plan(direct, **common, family_size=1, method="comet_local")
direct_certificate = direct_plan.evaluate(actions, outcomes, **metadata)
joint = make_joint_level_family_plans([paired], **common, method="generic_matched")
level_result = joint.evaluate(actions, outcomes, **metadata)
level_difference = level_result["contrasts"][direct.query_id]
assert joint.underlying_family_size == 2
```

Direct 路径对 `h*(q1-q0)` 的支持/矩/图直接认证。Level comparator 对整个预定 family 的 **unique levels** 统一分配 `delta/k`，再作 `[L1-U0, U1-L0]`；共享 baseline levels 会去重。两条路径在示例中各自使用同一总 delta，未对它们作新的联合保证。不能把两个分别 95% 的水平区间直接称为 95% contrast。受约束 slate/network 等策略还需证明 joint policy 可实现性，仅有合法 row marginals 不足。

## 解释输出

`status="CERTIFIED_UNDER_DECLARED_ASSUMPTIONS"` 仅在真实假设下解释；它不是独立性检测结果。`empty_intersection=True` 是需保留的失败，`certified_decision` 对空集/非认证输出返回 `ABSTAIN`，不能修成非空后记作成功。未知矩、非零 query 系数缺乏支持、非法条件化或数值失败均不能产生有效认证。

实现使用普通浮点及显式 numerical guard，未提供 outward-rounded machine proof。`query.target(mu)` 只供事后 oracle 评估；不得向估计器或 selector 传入未知真均值。应用 policy update 时还应报告 return **AND** safe **AND** useful，以及服务下限/容量约束；总弃权不能充当决策价值。
