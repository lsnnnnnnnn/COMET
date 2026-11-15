# COMET post-C-STAT research verdict

本轮已完成 E1–E5 的28,600个主研究单位，以及1,600个强基线/scaling单位和100个负对照单位，共30,300个完成单位。E6的1,000个单位仍为 `DATA_BLOCKED_NOT_FROZEN`，没有消耗其日志种子。所有完成的失败、空泛区间和次级未覆盖日志均保留。不能把本交付描述为“E1–E6全部完成”。

## 正确性与主张范围

主证明覆盖异质固定设计、精确且受支持的曝光、独立训练/发现信息、合法raw residual p-moment及整个score向量的充分条件依赖图，范围为 `1<p<=2`。显式半径包含锐利截断偏差常数 `(p-1)^(p-1)/p^p`、图集中项和范围项；不需要独立重复宏块或相同均值。query-specific支持/矩/着色成本、direct paired contrast、design-only调参和完整risk+utility联合选择事件均有对应证明/API/确定性核对。

下界限定于显式subgroup/exposure/clique两点子类，包含整数与饱和条件；它不是任意图、任意m的精确minimax置信宽度结论。零曝光下的抵消contrast与两个level的不可识别性分开。IID Catoni使用特殊两状态balanced-target/midpoint模型中另行证明的centered-moment界；没有把一般raw moment冒充centered moment。独立局部复核见 `post_cstat/local_appendix_math_review.md`。

证明是实数算术结论。实现使用预声明普通浮点padding；没有宣称机器验证的向外舍入。schema和source-ID检查不能证实隐藏独立性、真实e或未知尾尺度。可选predictable固定时域备忘为DERIVED_NOT_IMPLEMENTED，不进入主实证主张。

## 覆盖、信息量与决策价值

E1/E2/E3/E4/E5及anchor的主级比较数分别为96/60/108/192/32/68；各固定比较的完整family覆盖分别为1,000/1,000、300/300、300/300、300/300、500/500、200/200，主级均未观察到错误声明或Holm undercoverage flag。E5 fixed-slice覆盖的是其自身restricted family，不提供discovered primary-family的返回保证。不能把这些比较或其中的坐标合并成独立重复量；Wilson区间都是固定cell/method的pointwise Monte Carlo区间。

必须保留一个实际覆盖缺口：anchor次级90% IID-bounded scalar betting覆盖199/200。对应checkpoint是 `COMPLETE_WITH_CONFIDENCE_FAILURE`；runner failed_units=1、analysis execution-failed_units=0。它没有被删除或重跑。

E1中COMET在五个bounded cells各检测1,000/1,000，在triangles/weak/bounded仅2/1,000，六个finite-moment cells均0/1,000。E4主查询只在moderate/bounded的明确gap取得认证；不能用同日志其他问题的family-any发现率代替主查询power。E2的三层pure-truncation比较隔离local graph成本；额外bounded dispatch收益另算。E3仅full-support/moderate/bounded获得direct risk-reduction300/300，对照joint-level subtraction0/300；缩小变化范围虽能缩窄区间，不提供免费sign power。finite-moment scaling即使N=131,072仍未检测违规。

E5每trial实际联合family都是47个坐标。COMET及matched generic在四个moderate cells中各返回且安全有用500/500；weak cycle mixed/null分别340/500、238/500，weak independent mixed/null分别411/500、497/500。所有COMET返回的unsafe/infeasible观察计数为0；每固定500-trial单元的零计数Wilson95上界为.00762434，不是“真实风险为零”或条件unsafe-given-return自动受delta控制。

其中非baseline且安全、strict utility gain的计数，在四个moderate cells各500/500；weak cycle mixed/null为340/500、231/500，weak independent mixed/null为411/500、232/500。后两null结果分别含7和265个baseline返回。strict-gain拆分是独立重建的posthoc描述诊断，不是新增的预注册主假设。status quo虽oracle-feasible，但全部baseline、strict gain为0且没有证书；always-abstain的有用返回为0。

E5同时报告全部返回事件、效用、服务、风险违规、发现AND认证和数据预算。moderate mixed的发现AND认证各500/500，weak mixed各0/500；能安全返回不等于能认证planted violation。独立重建12,000个family、64,000个method/level frames，零不一致，无重采样或原oracle调用。完整trial的三split共45,056行，4,000trial合计180,224,000行，方法共享；in-sample重复使用认证标签，不得到另一份独立样本。

四类负控的错误输入严格为HEURISTIC。wrong-e、nuisance leakage及遗漏bias各false-safe25/25，hidden shock false-violation13/25；所有invalid arms覆盖0/25。合法range/bias参考可以完全空泛，honest refusal的coverage/error是NA。这些结果不能解释为schema自动发现隐藏问题。

## 同信息强比较与研究贡献

Fully matched generic与COMET代数相同，并在所有完成单元得到相同结果。没有独立的新估计器优势。IID bounded DR empirical Bernstein区间更窄（.01055对COMET的.01748）；IID finite-moment Catoni也更窄（.15246对.17416），但两者均未检测违规。

E5的global reference是pure `truncated_global_envelope` ablation。COMET相对它的差异同时包括localization和bounded dispatch，不能单独归因于图处理，也不能把该global arm称为最强bounded competitor。E2才通过同engine的分层比较隔离graph成本。

证据支持的贡献是：可审计signed-moment接口、目标特定证据成本、抵消对比、范围明确的障碍及完整联合选择契约。在所测试bounded流程中，确有非baseline安全且有正收益的返回；重尾和弱overlap的限制也有明确负结果。Learn-then-certify及图着色/截断工具的已有先例已注明，文献核对不被表述为穷尽性SOTA证明。

## 交付与剩余项

本地完整LaTeX改写采用新全局图scope，包含五张实际主图、解析maps、强基线/负控附图、完整证明、冻结配置表和实际选择表。详细结果、两个levels、所有方法及NA保留在CSV/JSON与proof-code-experiment ledger中。独立Overleaf未修改或同步。原九页C-STAT提案及6,000日志/1,134,000记录保留，旧17项未改变，本轮旧确认性新增抽样为0；最终6,000压缩文件SHA逐项匹配旧index。

剩余外部验证只有E6。官方ACS CA2018同一来源在本机与服务器都返回403，错误body不被当作archive，未换数据集。离线loader、source-selector图证明、freeze gate、runner与analyzer已完成并用fixtures核对，但没有真实协变量实验结果。缺失blueprint已获用户明确豁免；没有伪称读过或恢复了该文件。精确保留IDs、实际进程状态和恢复命令见根目录 `FINAL_HANDOFF.md` 与 `post_cstat/remaining_run_ids.json`。
