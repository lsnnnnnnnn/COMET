# 最终有界数字核对

仅核对 `paper/post_cstat/main.tex` 摘要、`sections/evidence.tex` 的 E5 段落、`tables/E5_decisions.tex` 和 `reports/research_verdict.md`，对照已完成的 E5 analysis、独立 diagnostics 及本轮已核实补充结果。未发现实质数字、分母或保证范围错误。

- E5 的 500-trial 分母、各 cell 的 SU/global/nonbaseline 计数、7 与 265 个 baseline 拆分，以及 conditional-on-return 的 mean utility gain 均对应最终结果。
- 32 项 coverage 明确包含 fixed-slice own family；primary discovered-family return guarantee 的适用范围未被扩大。
- baseline NI 与严格正收益已分开；未将 status quo 或全弃权当作 policy repair。
- global 明确为纯截断 ablation；其与 COMET 的差异未被单独归因为 graph localization，matched generic 的相同 dispatch 与等价性已保留。
- 28,600 主单位、1,700 补充单位、E6 的 1,000 个未完成单位，以及 anchor 次级 199/200 的未覆盖记录均一致。

本次只新增此核对记录，没有修改上述文件、追加统计、测试、抽样或扩展为全论文重审。
