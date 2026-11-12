# COMET Gate A+B 后续决策说明

## 核心结论

根据用户汇报，Gate A+B 已完成，但 30/30 同时覆盖率完全来自覆盖整段可行范围的区间。该实验只证明基本流程能运行，不能证明证书有信息量，也不能证明最终 90%/95% familywise coverage 达标。**下一步应先完成 Gate C0（证书有效性与非平凡性），再决定是否启动大规模 Gate C。**

注：最新 Gate A/B 报告在用户的 Mac 本地路径，未上传到当前对话；尝试通过已连接 GitHub 账户读取两个指定仓库/commit，返回 404。因此没有独立检查新代码的权限，判断以用户报告与此前论文/任务规范为基础。

## 第一项优先改进：MOM 分组的精确二项尾界

当前保守公式
\[
K=\lceil8\log(2|\Theta|/\delta)\rceil
\]
在 \(|\Theta|=16,\delta=0.05\) 时为 52。

若 Gate A 定理确实能保证在一个合法共同条件下独立的 supergroup bad-event，且各组概率不超过 \(\eta=1/8\)，则可以直接使用
\[
|\Theta|\Pr[\mathrm{Bin}(K,\eta)\ge\lceil K/2\rceil]\le\delta.
\]
此时奇数 \(K=9\) 已满足 95% familywise 要求，失效概率上界约 0.03972。必须补充分组独立、共同 target、各组 p-moment 常数和余数分组处理的证明，不能直接把 K 改成 9。

B=128 时，旧方案每组至少 2 个宏块，新方案每组至少 14 个宏块。在相同 \(\eta=1/8\) 与同一个 p-moment 常数下，p=2 时最保守半径可按 \(\sqrt{2/14}\) 的比例下降；p 接近 1 时改善幅度有限。此改进不保证现实数据上的新模型有效。

## 第二项：比较严谨、可计算的有界回报证书

对于 \(Y(s),\hat\mu(s)\in[0,1]\)，预先固定的 \(q,h\)，已知精确曝光概率 \(e(s)>0\)，和真正满足条件依赖图/独立宏块条件的外生 design，有
\[
v_u=h_u^2\sum_s q_u(s)^2/e_u(s), \quad
V_\theta=N^{-2}\sum_b\chi_b\sum_{u\in b}v_u.
\]
基于条件方差图界及 Chebyshev + union bound，可以为直接的 sample-mean DR 估计量给出半径
\[
r_\theta=\sqrt{|\Theta|V_\theta/\delta}.
\]
这与原重尾 MOM 是不同的、假设更窄的估计方法，适合作为实际非平凡性和 sharpness 的严谨基线。它在没有统一 overlap 下界时依然可计算，但当 realized e 非常小时可能很宽。不能将其推广到未证明的自适应未来 design 或真正无界 Y。

如果采用 \(w_c(s)=\min(q(s)/e(s),c)\) 削减波动，必须另加对原目标的确定性最坏情形偏差预算：
\[
b_c=N^{-1}\sum_u |h_u|\sum_s(q_u(s)-c e_u(s))_+.
\]
不得把无偏性与 clipping 自动等同起来。

## 推荐里程碑

1. **C0.1 取证定位**：逐项导出 raw half-width、截断后 width/feasible diameter、K、B、L、n_eff、\(\nu_p\)、\(\chi\)、family size 和各 radius 组成。
2. **C0.2 解析可行性表**：反解理论半径所需 N，判别不可能在现实样本规模下达到的 p/overlap 区域。不要先跑大实验。
3. **C0.3 精确 binomial MOM**：严谨证明、实现、单元测试并保留旧 K 模式作对照。
4. **C0.4 有界 Y 的有效基线**：独立理论与 API；只有证明后才能打 certified 标签。酌情加上带偏差预算的 clipped 版本。
5. **C0.5 小试验**：从 strong overlap + bounded Y + p=2 开始，分别看 90/95% family coverage、width ratio、nontrivial fraction、false-safe 和 abstention；逐步加 \(\chi\) 与弱 overlap。单元测试之外不超过 400 新 replication-cells；不跑大型数据集。

**C0 通过要求**：至少一个预注册的简单模型能得到严格小于完整可行范围的合法区间；所有理论状态正确标注，回归测试保持通过；并记录失败和局限。这个标准只是允许进入 Gate C 的门槛，并不等于已经有足够的论文实验证据。

## 尚未证明部分如何处理

- 任意自适应部署路径：放入独立的后续 martingale/predictable truncation 研究任务；在完成前论文不能声称覆盖任意 adaptive history。
- 相互训练的 cross-fit：主要 certified 实验继续采用独立 pilot 或严格允许的训练设计；互训版本只做探索性对比。
- 估计 tail scale、nuisance 与未知 drift：只有额外高概率上界才纳入认证，否则用 sensitivity 标签。
- 长期闭环部署安全：当作额外验证目标，不是现有离线证书的定理结论。
- 重尾 p 接近 1 的证书仍可能很宽：如实报告拒绝认证的区域，避免只给覆盖率不报告可用性。

**在完成上述工作前，不建议开始 1,000 次重复的主覆盖率实验。**
