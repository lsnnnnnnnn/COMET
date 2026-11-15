# COMET 审阅入口

本交付仅同步已有研究、核查E6恢复条件并整理最终证据。30,300个完成新单位没有重采样、换种子或改协议；旧C-STAT本轮新增抽样为0。

- [最新研究分支](https://github.com/lsnnnnnnnn/COMET/tree/codex/post-cstat-delivery-20261115)
- [下载 review_bundle.zip](deliveries/20261115_sync/review_bundle.zip)
- [研究结论与E5完整端点](reports/delivery_sync_20261115/FINAL_RESEARCH_CONCLUSIONS.md)
- [主张—证明—代码—结果—图表矩阵](reports/delivery_sync_20261115/CLAIM_PROOF_RESULT_MATRIX.md)
- [同信息强基线比较](reports/delivery_sync_20261115/STRONG_BASELINE_MATRIX.md)
- [24页论文PDF](paper/post_cstat/COMET_post_cstat_20261115.pdf) / [LaTeX入口](paper/post_cstat/main.tex)
- [E6契约、官方/镜像/缓存核查及BLOCKED原因](reports/delivery_sync_20261115/E6_recovery_audit.md)
- [交接与剩余1,000个保留ID的恢复步骤](FINAL_HANDOFF.md)
- [实际同步记录](reports/delivery_sync_20261115/SYNC_VERIFICATION.md)

## 研究结论先看什么

新主定理允许异质均值和一个连通的充分条件score图，解除独立重复宏块/共同均值限制；精确支持曝光、合法raw residual moment、真实充分图、独立训练/发现和完整risk+utility预算仍必需。

同信息、同调参、同bounded dispatch的generic与COMET代数及结果相同。独立强基线有时更窄；部分heuristic有更高经验有用返回，但同时有unsafe且无联合置信契约。所测有界流程存在非baseline安全正收益返回；所测finite-moment检测仍有明确负结果。不能据此声称普遍估计器优势。

候选/坐标描述量与完整独立trial的覆盖、错误、返回率分开报告；坐标数量不能倍增binomial分母。E5的utility-NI保证不自动变成strict-positive-gain保证，strict gain是posthoc oracle描述端点。

## E6最终状态

`DATA_BLOCKED_NOT_FROZEN`。官方正常请求403；公开CSV镜像未取得有效文件，也未证明其与原始官方档案的完整数据等价。没有prepare、freeze、消费种子或产生E6结果，不使用替代数据或占位图。

## 如何使用包

解压后进入 `COMET_REVIEW_20261115/`，先读本文件和最终研究结论，再看PDF/矩阵。包包含完整LaTeX及所有实际图依赖、适用条件/API/证明、全部实验汇总和足够的逐query/group聚合CSV、E6契约与失败记录。原始checkpoint和巨大重复详细JSON未打入轻量审阅包，仍保留于原工作区；排除项目及理由见 `reports/delivery_sync_20261115/review_bundle_plan.json`。不能把这个审阅包误认为完整raw数据备份。

既有manifest中的校验字段是历史证据，本轮没有对它们或旧数据重算哈希。同步使用普通Git和小文件正文直接比较；没有force-push或修改独立Overleaf。主证明开头的“THEORY_NOTE当时未取得”是原写作时间状态，后续完整读取与49点网格和解见 `reports/post_cstat/theory_note_reconciliation.md`，冻结证明源保持原字节。
