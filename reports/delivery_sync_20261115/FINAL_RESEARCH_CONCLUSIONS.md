# COMET 最终研究结论

这轮工作支持的结论是：**在精确曝光、合法残差矩和充分条件依赖图等声明条件下，可以审计异质固定设计上的目标特定 signed moments，并将全部风险、效用与服务约束放入同一个有限策略选择契约。** 在所测试有界流程中，确实得到非 baseline、安全且正效用增益的返回。它不支持“COMET 是普遍更优的新估计器”：同信息、同调参、同 dispatch 的 generic 与其相同，合法独立强基线有时更窄，有限矩环境的检测也有明确负结果。[研究verdict](../research_verdict.md)

本文件是交付阶段的证据整理，不是新研究。复用已完成 findings 和结果，不新增实验、统计检验或哈希核验；不修改论文、协议或历史结果。已完成的主研究与补充研究单位、未实施的 E6 状态见[交付研究verdict](../research_verdict.md)。

## 1. 主定理到底解除什么，仍然依赖什么

已解除的是“必须有独立重复宏块、每块同均值”的限制：允许行均值异质、固定设计异质和一个全局连通图。误差半径明确支付**截断偏差、图调整集中、范围**三项，覆盖原始未截断目标，而非静默改成截断后的新目标。查询可用active支持的诱导图与实际矩，paired contrast可抵消共同项；允许在固定设计信息上选择合法阈值/有界分支。[主定理与证明](../../paper/post_cstat/sections/theory.tex)、[完整推导](../../theory/global_residual_truncation.md)

| 仍需成立的前提 | 不能偷换成的结论 |
|---|---|
| 精确且有支持的曝光law，以及给定曝光的识别/随机化条件 | 有一个schema或inverse weight就识别反事实；未知e可当已知 |
| 合法raw residual p-moment，1<p<=2，含nuisance误差 | 把未知尾尺度、centered noise moment直接当合法raw residual moment |
| 整个保留score向量的充分条件依赖图；source模型真实且完整 | 原始网络、低相关或声明的source IDs自动发现hidden dependence |
| training/discovery与certification随机源分离，family与预算在认证结果前冻结 | evaluation-fit nuisance、outcome-selected query或阈值无需额外代价 |
| 所有实际用于选择的risk/utility坐标均支付联合预算，design mass已知且为正 | 只预算risk、漏utility或随机分母；fixed-slice覆盖保护另一个发现family |
| 有限、兼容的策略库与已知service/capacity条件 | 条件unsafe-given-return自动控制、未来分布/长期部署安全、无限类公平保证 |

这里使用的是实数算术证明和预声明浮点padding，不是形式化向外舍入。着色数是可用的已验证proper coloring数，不声称求出最小chromatic number。[条件与数值范围](../post_cstat/claim_ledger.csv)

下界只针对显式 subgroup/exposure/clique 两点子类，并有整数/饱和条件；不是任意图、任意family size的sharp minimax置信宽度定理。gamma>2r是充分检测条件，不是必要条件。[下界范围](../../theory/query_specific_cost_lower_bound.md)

## 2. E1–E4：覆盖成功没有消除证据成本与检测失败

所有以下coverage均是**每个固定cell/method对完整family**的计数；方法、坐标和两种confidence levels共享日志，不增加独立trial数。主水平为95%；Wilson与paired bootstrap是pointwise Monte Carlo区间，不是跨全部方法/cells的联合保证。

| 套件 | 主要已观察终点 | 独立分母与不确定性 | 本地结果 |
|---|---|---|---|
| E1 | 96项主比较各coverage1000/1000；COMET五个bounded cells各检测1000/1000，triangles/weak/bounded为2/1000；六个finite-moment cells均0/1000 | 每cell1000完整trial；1000/1000 coverage的Wilson95=[.996173,1]，0/1000上端=.003827 | [E1完成分析](../../results/post_cstat/E1_analysis_v1/summary.json) |
| E2 | 60项主比较各coverage300/300；固定first-half问题的pure local normalized r=.03254654、COMET bounded dispatch r=.02110065，在六outside条件保持不变；global困难不能冒充local困难 | 每条件300完整trial；六条件在replicate内配对。radius是设计值；coverage Wilson95=[.987357,1] | [E2逐查询详细CSV](../../results/post_cstat/E2_detailed_v1/query_summary.csv) |
| E3 | 108项主比较各coverage300/300；full-support/moderate/bounded direct risk-reduction300/300，对20 unique levels subtraction为0/300；其他11主格COMET无risk-improvement detection | 每cell300完整trial；16direct contrasts vs20unique levels同总delta，不能用候选数倍增n。0/300 Wilson上端=.012643 | [E3完成分析](../../results/post_cstat/E3_analysis_v1/summary.json) |
| E4 | 192项主比较各coverage300/300；primary query仅moderate/bounded的gap=-.10安全认证298/300、+.10/+.20违规认证各300/300；weak bounded与两finite-moment环境均无COMET主查询决定 | 每gap300完整trial；298/300 Wilson95=[.976022,.998170]。family-any detection不能替代primary gap power | [E4完成findings](../post_cstat/E4_completed_findings.md) |

E2三层pure truncation才单独隔离moment/global-graph/local-graph成本，进一步的bounded dispatch收益另计。E3缩小变化同时缩小signal，图中单查询median不是正文family-mean width，也不能只看窄度宣称更高sign power。E4四环境COMET的2r分别为.1741848221、1.0586421075、.7999574788、2.3290257819；超出既定gap窗口的边界保留原值，不移入成功区。[E2逐查询详细CSV](../../results/post_cstat/E2_detailed_v1/query_summary.csv)；[E3完成分析](../../results/post_cstat/E3_analysis_v1/summary.json)；[E4详细r/2r](../post_cstat/E4_completed_findings_detailed_supplement_v1.md)

有限矩样本由声明的Pareto-source模型与合法moment envelope产生；计算机32-bit采样有有限最大值，不能把这些MC样本字面描述为无穷方差随机变量。它们也没有证明未知尾尺度可从日志安全估计。[DGP与范围说明](../../paper/post_cstat/sections/evidence.tex)

### 候选／坐标级描述量：不等同于独立 trial 指标

候选级在这里指冻结 family 中的一个审计问题／最终contrast坐标，不是一条独立实验日志。下面直接读取已保存 group CSV 的聚合字段，展示坐标分布的 median、q25/q75 与 IQR；没有重新聚合或检验。每个 trial 的多个坐标共享数据、可相关，因此**不对坐标记录数建立独立 binomial CI**。前面的 coverage/error/detection，以及后面的 E5 return 指标，仍用完整独立 trial 作分母。

| cell / method | 坐标描述量 | median | q25—q75 | IQR | 观测坐标记录数 | 独立 trial 分母 | 保存字段来源 |
|---|---|---:|---|---:|---:|---:|---|
| cycle-moderate-bounded / comet_local | 相交宽度 / 已知可行直径 | 0.04258696511578963 | 0.03902986285625812—0.050069879360021254 | 0.011040016503763135 | 16000 | 1000 | [E1 group CSV](../../results/post_cstat/E1_detailed_v1/group_summary.csv)：`feasible_width_ratio_*` |
| triangles-weak-heavy / comet_local | 相交宽度 / 已知可行直径 | 0.721157054685819 | 0.5819500807828613—0.7691031396819525 | 0.18715305889909128 | 16000 | 1000 | [E1 group CSV](../../results/post_cstat/E1_detailed_v1/group_summary.csv)：`feasible_width_ratio_*` |
| support100-moderate-bounded / comet_local | 最终contrast相交宽度 | 0.006312361371539068 | 0.00450957497564998—0.008437603929147072 | 0.003928028953497092 | 4800 | 300 | [E3 group CSV](../../results/post_cstat/E3_detailed_v1/group_summary.csv)：`intersected_width_*` |
| support100-moderate-bounded / deduplicated_joint_level_difference | 最终contrast相交宽度 | 0.04347270189122179 | 0.03978937640954528—0.04969945027145886 | 0.00991007386191358 | 4800 | 300 | [E3 group CSV](../../results/post_cstat/E3_detailed_v1/group_summary.csv)：`intersected_width_*` |

以上均为主水平95%的保存描述量。E1的16000条记录来自1000个trial内各16个坐标，E3的4800条记录来自300个trial内各16个最终contrast；不是16000或4800次独立重复。E3 level-subtraction底层仍支付20个unique levels的联合预算。这里的group median既不是E3正文的mean-per-trial coordinate width，也不是Fig3固定单查询的median；IQR只描述坐标分布，不是置信区间。

## 3. 强基线：优、平、劣与等价应按条件和指标说

- **等价：** fully matched generic与COMET相同，不能作为独立估计器胜利。
- **COMET并非最窄：** IID bounded的独立DR-EB mean intersected width为.01055，COMET为.01748；IID finite-moment的Catoni为.15246，COMET为.17416，后者双方检测都是0/200。
- **部分指标COMET较优但不是普遍优势：** bounded IID的Catoni/scalar betting宽于COMET，检测仍同为200/200；E1/E4中graph Bernstein可恢复所列COMET检测，而Hoeffding在部分weak/small-gap环境未检测。
- **E5 global不是最强matched bounded comparator：** 它是pure global-envelope truncation；与COMET之差同时含localization/envelope与bounded dispatch，不可单独归因为图处理。部分heuristic给出更多oracle-safe-useful返回，但有unsafe且没有联合置信保证，不能声称COMET在所有经验端点支配它们。

各比较的适用模型、精确宽度/计数与图表见[强基线矩阵](STRONG_BASELINE_MATRIX.md)及[强基线与负控findings](../post_cstat/supplementary_completed_findings.md)。68项eligible主anchor比较各200/200 coverage，Wilson95=[.981155,1]；次级90% scalar betting的一次199/200未覆盖保留，不能称所有日志“零失败”。

Fixed-DGP cycle scaling中，N=8192/32768/131072时COMET mean intersected widths：bounded为.03424/.01666/.00821，finite-moment为.19071/.12153/.07664；每个N的所有适用方法分别检测200/200与0/200。这是描述性scaling，不是minimax rate验证。[强基线与负控findings](../post_cstat/supplementary_completed_findings.md)

## 4. E5：把返回、风险、收益与弃权分开

本节主水平每cell有500个独立完整three-split trials，actual joint family每次均为47个risk+utility坐标。32项certificate比较覆盖各自family各500/500、Holm flags0；其中只有global/COMET/matched提供primary discovered-family返回保证。fixed-slice的500/500只是own-family coverage。所有精确计数、Wilson、均值scope及全部8arms结果见[E5完整findings](../post_cstat/E5_completed_findings.md)和[E5精确计数与Wilson](../post_cstat/E5_completed_findings.json)。

下表COMET的R（返回）=SU（return AND safe AND useful），unsafe和infeasible均为0；Abstain以500−R的互补计数列出，不是另抽样。NB+表示非baseline AND安全有用 AND strictpositivegain，为独立重建的posthoc描述端点。

| cell | R | unsafe / infeasible | SU及pointwise95 CI | Abstain | baseline R | NB+ | Global SU |
|---|---:|---:|---|---:|---:|---:|---:|
| cycle-moderate-mixed | 500/500 | 0 / 0 | 500/500 [0.9924, 1.0000] | 0/500 | 0/500 | 500/500 | 351/500 |
| cycle-moderate-null | 500/500 | 0 / 0 | 500/500 [0.9924, 1.0000] | 0/500 | 0/500 | 500/500 | 454/500 |
| cycle-weak-mixed | 340/500 | 0 / 0 | 340/500 [0.6379, 0.7194] | 160/500 | 0/500 | 340/500 | 0/500 |
| cycle-weak-null | 238/500 | 0 / 0 | 238/500 [0.4326, 0.5198] | 262/500 | 7/500 | 231/500 | 0/500 |
| independent-moderate-mixed | 500/500 | 0 / 0 | 500/500 [0.9924, 1.0000] | 0/500 | 0/500 | 500/500 | 340/500 |
| independent-moderate-null | 500/500 | 0 / 0 | 500/500 [0.9924, 1.0000] | 0/500 | 0/500 | 500/500 | 411/500 |
| independent-weak-mixed | 411/500 | 0 / 0 | 411/500 [0.7861, 0.8530] | 89/500 | 0/500 | 411/500 | 44/500 |
| independent-weak-null | 497/500 | 0 / 0 | 497/500 [0.9825, 0.9980] | 3/500 | 265/500 | 232/500 | 17/500 |

0/500 unsafe的pointwise Wilson95上端为.00762434，不是零真实风险，也不是条件unsafe-given-return自动受delta控制。utility/gain与risk-excess均值以actual returns为分母；service_all在500trials上平均并对弃权记0，不能把它误当已返回策略违反服务下限。原值与value_count来源：[E5精确计数与Wilson](../post_cstat/E5_completed_findings.json)。

| cell | 返回中mean utility | 返回中mean gain（含baseline零增益） | 返回中mean max risk excess | mean service_all |
|---|---:|---:|---:|---:|
| cycle-moderate-mixed | 0.24750 | 0.05447 | 0.00000 | 0.45000 |
| cycle-moderate-null | 0.24320 | 0.05947 | 0.00000 | 0.45000 |
| cycle-weak-mixed | 0.24145 | 0.04842 | 0.00000 | 0.30600 |
| cycle-weak-null | 0.23712 | 0.05340 | 0.00000 | 0.21280 |
| independent-moderate-mixed | 0.24752 | 0.05449 | 0.00000 | 0.45000 |
| independent-moderate-null | 0.24318 | 0.05946 | 0.00000 | 0.45000 |
| independent-weak-mixed | 0.24283 | 0.04981 | 0.00000 | 0.36990 |
| independent-weak-null | 0.20972 | 0.02599 | 0.00000 | 0.39430 |

**这些结果的研究含义：**
- 四个moderate cells有500/500真正NB+；weak cycle mixed/null为340/500与231/500，weak independent mixed/null为411/500与232/500。weak independent null的497个SU中有265个baseline，不能把497都叫repair。
- status quo每cell可SU500/500，但全部baseline、strictgain0、没有证书；Abstain reference每cellR=SU=0。NI型有用返回与策略改进是不同问题；selector要求utility noninferiority，严格正gain是完成后的oracle描述端点，不自动继承一个严格正收益定理。
- fixed-slice own coverage仍500/500，却在两个moderate mixed cells各unsafe500/500，weak cycle mixed为82/500、weak independent mixed为459/500。保护别的问题不能替代primary约束。
- Point/In-sample在cycle weak mixed可SU481/500，高于COMET340/500，同时unsafe19/500；在independent moderate mixed有unsafe1/500。研究支持置信契约下的安全返回取舍，不支持所有oracle性能指标的统一支配。
- COMET发现AND认证真违规在两个moderate mixed cells各500/500，weak mixed各0/500；安全返回并不等于已认证planted violation。

以上逐项均来自[E5完整findings](../post_cstat/E5_completed_findings.md)及[完成的独立endpoint重建](../post_cstat/E5_diagnostics_v1/diagnostics.json)；32项coverage、47个坐标、每个策略候选和64000个复核frame都不是额外独立样本。主研究的概率分母始终是500个完整trial。

## 5. 反例与未验证范围也属于最终结论

负控中wrong-e、evaluation nuisance leakage、遗漏clipping bias的invalid heuristic各false-safe25/25；hidden shock false-violation13/25，Wilson95=[.334985,.699687]。全部invalid interval coverage0/25；它们不是certificate。合法known-range/bias参考可以width1且无检测；honest refusal的coverage/error是NA，而不是0/25。schema不能据此宣称自动识别隐藏违约。[强基线与负控findings](../post_cstat/supplementary_completed_findings.md)

E6没有真实协变量实验结果，fixtures、loader与source-selector图证明都不能充作外部实证。因此本轮结论不包括真实ACS验证、跨数据分布泛化，或selection对income的因果效应，也不称“E1–E6全部完成”。[E6与交付范围](../research_verdict.md)

## 6. 主张落到哪里

完整追踪见[主张—证明—代码—结果—图表矩阵](CLAIM_PROOF_RESULT_MATRIX.md)（[CSV](CLAIM_PROOF_RESULT_MATRIX.csv)）；强对照另有[比较矩阵](STRONG_BASELINE_MATRIX.md)（[CSV](STRONG_BASELINE_MATRIX.csv)）。它们列出具体proof文件、API、完成结果和论文图表，而不是仅写“后续GO”。

最终可支持的研究命题是：**给定可审计但不可由schema替代的概率条件，目标特定支持/矩/图和完整联合family决定哪些反事实结论可认证；在所测有界流程中，遵守这套联合约束证书的返回中观察到了非baseline正收益；严格正gain本身仍是posthoc oracle统计。** 不能支持的命题是：独立新估计器的普遍优势、任意图上的sharp最优置信成本、重尾下的普遍检测能力、未知假设的自动验证、条件返回风险或未来部署安全。
