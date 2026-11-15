# 已完成补充实验：ANCHORS 与负对照

仅从服务器回传后两份完成分析提取；summary SHA256均匹配manifest。回传receipt记录1,718个文件压缩字节SHA全匹配，科学单位为1,600 anchor logs +100 negative-control logs，不能称为1,718条实验日志。本次未读raw、抽样或修改论文/冻结源。

## 完成状态与分母

- 68个eligible主水平anchor cell×method比较全部complete-family coverage=200/200、Holm flags=0、观察false claim=0。analysis的execution/record failed_units与unknown frame均为0；runner invocation的failed_units为1，含下述secondary coverage miss，不能称“1,600零失败”。
- IID anchor为N=32768、m=1、target=.45、threshold=.4、logging e=(.75,.25)、target q=(.5,.5)；heterogeneous cycle scaling为m=16。单坐标或完整family的coverage/error单位均是独立完整日志，n=200，不能乘16。
- 每个cell的methods和两个levels共享日志。下表为主delta=.05；JSON保留两level完整208个anchor rows，含NA。宽度是最终**intersected**区间的mean-per-trial coordinate mean，不是raw width。
- 一条checkpoint保留`COMPLETE_WITH_CONFIDENCE_FAILURE`：次级delta=.10的IID bounded scalar betting coverage=199/200；主delta=.05为200/200。runner invocation将该日志计入failed_units=1；analysis.execution failed_units=0。它是随机置信未覆盖，不是执行失败；没有丢弃。
- 负控为4×25独立完整日志、m=1，三engines与两个levels共享日志。无numerical failures，不加入任何主比较/Holm family；HEURISTIC不是certificate。

## IID：全部强基线检测与相交宽度

| 方法 | bounded D | bounded width | heavy D | heavy width |
|---|---:|---:|---:|---:|
| Scalar OPE betting（author implementation） | 200/200 | 0.0194089907 | NA | NA |
| Bhatt2022 IID Catoni | 200/200 | 0.0273953365 | 0/200 | 0.152459466 |
| Waudby-Smith2024 independent DR-EB | 200/200 | 0.0105485705 | NA | NA |
| COMET | 200/200 | 0.0174764331 | 0/200 | 0.174159345 |
| matched generic | 200/200 | 0.0174764331 | 0/200 | 0.174159345 |
| graph Bernstein | 200/200 | 0.0174764331 | NA | NA |
| global graph Bernstein | 200/200 | 0.0174764331 | NA | NA |
| graph Hoeffding | 200/200 | 0.0300100875 | NA | NA |
| global graph Hoeffding | 200/200 | 0.0300100875 | NA | NA |
| local truncation | 200/200 | 0.0273340317 | 0/200 | 0.174159345 |
| local moments/global graph | 200/200 | 0.0273340317 | 0/200 | 0.174159345 |
| global envelope+graph | 200/200 | 0.0273340317 | 0/200 | 0.174159345 |
| colorwise truncation | 200/200 | 0.0273340317 | 0/200 | 0.174159345 |

IID bounded DR-EB比COMET更窄；IID heavy Catoni也更窄，但两者都0/200检测。matched generic与COMET相等。IID-only三基线在scaling为NA，bounded-only方法在heavy为NA，不能当作0检测。

## Scaling：全部N×outcome，主水平

各适用方法coverage均200/200、false claim均0。D是每个适用方法共同的family-any true-violation detection，不是primary-query power。GB/GH分别合并local/global相同版本；LT与local-moments/global-graph相同。JSON逐方法完整保留。

| N | outcome | COMET=generic | GB | GH | LT=local moments/global graph | global envelope | colorwise | 每个适用方法D |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 8192 | bounded | 0.0342367751 | 0.0342887883 | 0.043402841 | 0.0510577961 | 0.0830917636 | 0.0537266291 | 200/200 |
| 8192 | heavy | 0.190706361 | NA | NA | 0.190706361 | 0.247162298 | 0.197105843 | 0/200 |
| 32768 | bounded | 0.0166628208 | 0.0166628208 | 0.0217008206 | 0.0255282097 | 0.0449024759 | 0.0268625904 | 200/200 |
| 32768 | heavy | 0.121527719 | NA | NA | 0.121527719 | 0.166803403 | 0.125652181 | 0/200 |
| 131072 | bounded | 0.00821117899 | 0.00821117899 | 0.0108504855 | 0.0127641911 | 0.0248676746 | 0.0134313862 | 200/200 |
| 131072 | heavy | 0.0766425082 | NA | NA | 0.0766425082 | 0.116180292 | 0.0792905449 | 0/200 |

这些是fixed-DGP描述性scaling，不是minimax rate或必要样本复杂度验证。所有heavy适用方法虽随N区间缩窄，三个N下均0/200检测。

## 负对照：所有valid / invalid / honest，主水平

C=interval coverage，FS/FV=false-safe/false-violation，D=true violation detection，w=mean width，非NA事件分母均为25。invalid严格标`HEURISTIC_INTENTIONALLY_INVALID_ASSUMPTIONS`，只称diagnostic claims。shared-shock的valid/range是确定性known-range参考。

| control | engine/类型 | C | FS | FV | D | w | nontrivial | issued/refused |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| evaluation_nuisance_leak | valid/certificate | 25/25 | 0/25 | 0/25 | 25/25 | 0.0600201748 | 25/25 | 25/0 |
| evaluation_nuisance_leak | invalid/HEURISTIC | 0/25 | 25/25 | 0/25 | 0/25 | 0.0600201747 | 25/25 | 25/0 |
| evaluation_nuisance_leak | honest/no certificate | NA | NA | NA | NA | NA | 0/25 | 0/25 |
| hidden_shared_shock | valid/range | 25/25 | 0/25 | 0/25 | 0/25 | 1 | 0/25 | 25/0 |
| hidden_shared_shock | invalid/HEURISTIC | 0/25 | 0/25 | 13/25 | 0/25 | 0.0150050439 | 25/25 | 25/0 |
| hidden_shared_shock | honest/no certificate | NA | NA | NA | NA | NA | 0/25 | 0/25 |
| missing_clipping_bias | valid/certificate | 25/25 | 0/25 | 0/25 | 0/25 | 1 | 0/25 | 25/0 |
| missing_clipping_bias | invalid/HEURISTIC | 0/25 | 25/25 | 0/25 | 0/25 | 0.0213782976 | 25/25 | 25/0 |
| missing_clipping_bias | honest/no certificate | NA | NA | NA | NA | NA | 0/25 | 0/25 |
| wrong_propensity | valid/certificate | 25/25 | 0/25 | 0/25 | 25/25 | 0.0600201748 | 25/25 | 25/0 |
| wrong_propensity | invalid/HEURISTIC | 0/25 | 25/25 | 0/25 | 0/25 | 0.0240080701 | 25/25 | 25/0 |
| wrong_propensity | honest/no certificate | NA | NA | NA | NA | NA | 0/25 | 0/25 |

次级delta=.10各control×engine的coverage、FS、FV、D、issued/refused与nontrivial计数均与主水平相同，只有宽度变化；JSON保留全部24条记录。honest每control拒绝25/25，但coverage/error denominator=0且rate/CI为NA，不能写成0/25错误或零风险。

shared-shock invalid的coverage为0/25，而FV为13/25：负shock下方向正确的safe claim也不能使未覆盖区间变有效。wrong-e/leak/missing-bias各FS=25/25。proper clipping-bias证书和shared-shock range参考都width=1、nontrivial=0、D=0，不能把空泛覆盖描述为检测成功。

解析机制：wrong-e期望错误DR=.50（target=.68）；leak期望=.32（target=.68）；遗漏bias的clipped expectation=.4901（target=.80），精确bias=.3099而合法上界19.52984668360965很松。shock/wrong-e/leak的schema_detectability=false；honest refusal依赖如实披露的违约前提，不是schema从日志自动发现隐藏问题。

## Pointwise Wilson95（保留服务器分析存储值）

| 计数 | 区间 |
|---:|---|
| 200/200 | [0.981154673623, 1] |
| 0/200 | [0, 0.0188453263773] |
| 199/200 | [0.972226295602, 0.999116831284] |
| 25/25 | [0.866807749061, 1] |
| 0/25 | [0, 0.133192250939] |
| 13/25 | [0.334985169504, 0.699687140459] |

honest-refusal的25/25频率可单独描述，但不产生coverage/error区间。Wilson以固定cell/engine/level的whole-log为单位，为pointwise Monte Carlo区间，不跨方法、坐标、control或levels pooling。

## 可直接入论文的英文段落（建议文本）

Across 1,600 supplementary anchor logs, all 68 eligible primary cell-method comparisons covered their complete target family in 200/200 independent trials, with no observed false claim or Holm undercoverage flag. The homogeneous IID anchor has one target coordinate; the heterogeneous cycle scaling anchors have 16. In the bounded IID setting, the independent DR empirical-Bernstein comparator produced a mean intersected width of 0.01055, compared with 0.01748 for COMET, its matched generic version and graph Bernstein; all detected the violation in 200/200 trials. In the heavy-tailed IID setting, the Catoni anchor was narrower than COMET (0.15246 versus 0.17416), but both detected no violation. One scalar-betting interval missed the target at the secondary 90% level (199/200 coverage); its primary 95% coverage was 200/200. The runner marked that log COMPLETE_WITH_CONFIDENCE_FAILURE; the completed analysis reports no execution failure.

With N=8,192, 32,768 and 131,072, COMET’s mean intersected coordinate widths were 0.03424, 0.01666 and 0.00821 in the bounded cycle model, and 0.19071, 0.12153 and 0.07664 in the heavy-tailed model. Every applicable method detected a violation in 200/200 bounded trials and 0/200 heavy-tailed trials at each sample size. These are descriptive results for fixed data-generating processes, rather than a minimax-rate validation; methods and confidence levels share each complete log.

Four prespecified invalid-assumption controls used 25 complete logs each and a fixed threshold of 0.6. The deliberately invalid, heuristic intervals made false-safe claims in 25/25 trials under wrong propensities, evaluation-nuisance leakage and omission of clipping bias, and false-violation claims in 13/25 trials under a hidden shared shock; all four heuristic arms had 0/25 interval coverage. The correctly declared range reference for the shared shock and the bias-debited clipping certificate each covered 25/25 targets but had width one and no violation detection. Truthfully disclosed unsupported requests were refused in 25/25 trials per control: their coverage and error rates are not applicable. These diagnostics neither certify the invalid arms nor imply that input schemas can discover hidden dependence or nuisance leakage.

## 来源指纹

- anchors: `results/post_cstat/ANCHORS_server_v2_analysis_v1/summary.json`；summary SHA256=`9f76354e6575d4013086db8516184eb02133237c779521c9997ca3a4f6b4f92a`；analysis fingerprint=`e39b72cd9e4709770d6a26f2a717a61d7e33acb4d9641e393b1650ea21451080`。
- negative_controls: `results/post_cstat/negative_controls_server_v2_analysis_v1/summary.json`；summary SHA256=`0e38231f526dd654527db6a5ab13772bf2bab5dbb0fd45c3eab7ad3a5a834e39`；analysis fingerprint=`55c655f0f41c1e052fb7d3f6a73792195ac78d33315d8aba6168a9df760558bc`。

配套`supplementary_completed_findings.json`保留所有方法/levels/NA/分母/Wilson、120条paired-width comparisons及解析参数。旧17项和E1–E5主family未合并或修改，本补充不提供pipeline return AND safe AND useful结论。

Invocation区分的来源：`reports/post_cstat/server_completed_mirror/server_ANCHORS_run_1794716768652357363_stdout.txt`，SHA256=`dea9594686fc9193ab18780c9a9f1de7ae5df2e7ce0230ceb34a19ce95546b41`。
