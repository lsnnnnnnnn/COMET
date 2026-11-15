# E5 已完成结果：完整 pipeline、主约束返回与独立复核

仅在主analysis与独立diagnostics均COMPLETE、4000/4000后提取；未查看partial科学表现。两份summary SHA256均匹配manifest，protocol和checkpoint inventory完全相同。未读raw、抽样、改论文或冻结源。

## 完成与保证适用性

- 8 cells ×500个独立完整three-split trials，execution failure/unassessable均0，4000个checkpoint均COMPLETE。两levels与8arms共享日志；47个风险/效用坐标和64,000个复核frames都不增加统计n。
- 每个trial为training4096、discovery8192、certification32768行。全实际deduplicated family m均为47：每cell、每arm、每level都是`47:500`，不是固定16；相同m不意味着审计family相同。
- 32个eligible主certificate cell×method比较全own-family coverage=500/500，Wilson95=[.9923756595384478,1]，Holm flags=0（所有p=1）。其中只有24个比较保证primary independently discovered-family可行返回；8个fixed-slice比较只覆盖各自fixed family。
- independent diagnostics为RECONSTRUCTED_RECORDS_MATCH：12000个families、64000个frames被重建，mismatch=0。它复核saved policies/conditional truths/selection/booleans，不重拟合、重放随机源或证明schema可检测隐藏违约。

| arm | certificate coverage | primary discovered-family return guarantee |
|---|---|---|
| Point (heuristic) | NA | no |
| In-sample (heuristic) | NA | no |
| Global (primary certified) | primary discovered family | yes, under declared assumptions |
| COMET (primary certified) | primary discovered family | yes, under declared assumptions |
| Matched generic (primary certified) | primary discovered family | yes, under declared assumptions |
| Fixed slices (own family) | own fixed family | no |
| Abstain reference | NA | no |
| Status quo (uncertified) | NA | no |

`R`=return；`U`=return AND unsafe（违反任一主发现risk约束）；`I`=return AND infeasible（risk或utility NI或service/capacity失败）；`SU`=return AND safe AND useful（全部条件通过）。所有arm返回都按primary发现约束评价，包括fixed-slice/in-sample。实际所有I=U，所有已返回策略的utility NI与service/capacity条件均通过；这只是本次观察，不是一般等价。

所有下表是主delta=.05，分母500；方括号为固定cell/arm端点的pointwise Wilson95（为可读性显示6位，JSON保留源精度）。NA不填0。零U且零R的弃权策略没有有用返回；零弃权但U很高也不能称成功。

## 全部8 cells ×8 arms：joint端点、coverage与独立baseline/gain诊断

`B/NB`=baseline/nonbaseline return；`NB-SU`=nonbaseline AND safe AND useful；`G+`=return AND strictpositive utilitygain，**单独不要求safe**。NB-SU与G+的Wilson也完整保存在JSON。coverage为own family；heuristic与reference没有证书coverage。

### cycle-moderate-mixed

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| Global (primary certified) | 351/500 [0.660493, 0.740427] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 351/500 [0.660493, 0.740427] | 500/500 | 0 / 351 | 351 / 351 |
| COMET (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Matched generic (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 500/500 [0.992376, 1.000000] | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 500/500 | 0 / 500 | 0 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### cycle-moderate-null

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| Global (primary certified) | 454/500 [0.879461, 0.930317] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 454/500 [0.879461, 0.930317] | 500/500 | 0 / 454 | 454 / 454 |
| COMET (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Matched generic (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### cycle-weak-mixed

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 19/500 [0.024460, 0.058585] | 19/500 [0.024460, 0.058585] | 481/500 [0.941415, 0.975540] | NA | 0 / 500 | 481 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 19/500 [0.024460, 0.058585] | 19/500 [0.024460, 0.058585] | 481/500 [0.941415, 0.975540] | NA | 0 / 500 | 481 / 500 |
| Global (primary certified) | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 | 0 / 0 | 0 / 0 |
| COMET (primary certified) | 340/500 [0.637873, 0.719382] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 340/500 [0.637873, 0.719382] | 500/500 | 0 / 340 | 340 / 340 |
| Matched generic (primary certified) | 340/500 [0.637873, 0.719382] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 340/500 [0.637873, 0.719382] | 500/500 | 0 / 340 | 340 / 340 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 82/500 [0.134129, 0.198995] | 82/500 [0.134129, 0.198995] | 418/500 [0.801005, 0.865871] | 500/500 | 0 / 500 | 418 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### cycle-weak-null

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| Global (primary certified) | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 | 0 / 0 | 0 / 0 |
| COMET (primary certified) | 238/500 [0.432574, 0.519792] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 238/500 [0.432574, 0.519792] | 500/500 | 7 / 231 | 231 / 231 |
| Matched generic (primary certified) | 238/500 [0.432574, 0.519792] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 238/500 [0.432574, 0.519792] | 500/500 | 7 / 231 | 231 / 231 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### independent-moderate-mixed

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 1/500 [0.000353, 0.011241] | 1/500 [0.000353, 0.011241] | 499/500 [0.988759, 0.999647] | NA | 0 / 500 | 499 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 1/500 [0.000353, 0.011241] | 1/500 [0.000353, 0.011241] | 499/500 [0.988759, 0.999647] | NA | 0 / 500 | 499 / 500 |
| Global (primary certified) | 340/500 [0.637873, 0.719382] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 340/500 [0.637873, 0.719382] | 500/500 | 0 / 340 | 340 / 340 |
| COMET (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Matched generic (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 500/500 [0.992376, 1.000000] | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 500/500 | 0 / 500 | 0 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### independent-moderate-null

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| Global (primary certified) | 411/500 [0.786055, 0.853035] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 411/500 [0.786055, 0.853035] | 500/500 | 0 / 411 | 411 / 411 |
| COMET (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Matched generic (primary certified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### independent-weak-mixed

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 19/500 [0.024460, 0.058585] | 19/500 [0.024460, 0.058585] | 481/500 [0.941415, 0.975540] | NA | 0 / 500 | 481 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 19/500 [0.024460, 0.058585] | 19/500 [0.024460, 0.058585] | 481/500 [0.941415, 0.975540] | NA | 0 / 500 | 481 / 500 |
| Global (primary certified) | 44/500 [0.066206, 0.116076] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 44/500 [0.066206, 0.116076] | 500/500 | 0 / 44 | 44 / 44 |
| COMET (primary certified) | 411/500 [0.786055, 0.853035] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 411/500 [0.786055, 0.853035] | 500/500 | 0 / 411 | 411 / 411 |
| Matched generic (primary certified) | 411/500 [0.786055, 0.853035] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 411/500 [0.786055, 0.853035] | 500/500 | 0 / 411 | 411 / 411 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 459/500 [0.890645, 0.938981] | 459/500 [0.890645, 0.938981] | 41/500 [0.061019, 0.109355] | 500/500 | 0 / 500 | 41 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

### independent-weak-null

| arm | R [CI] | U [CI] | I [CI] | SU [CI] | own coverage | B / NB | NB-SU / G+ |
|---|---|---|---|---|---|---|---|
| Point (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| In-sample (heuristic) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 0 / 500 | 500 / 500 |
| Global (primary certified) | 17/500 [0.021335, 0.053771] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 17/500 [0.021335, 0.053771] | 500/500 | 0 / 17 | 17 / 17 |
| COMET (primary certified) | 497/500 [0.982510, 0.997957] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 497/500 [0.982510, 0.997957] | 500/500 | 265 / 232 | 232 / 232 |
| Matched generic (primary certified) | 497/500 [0.982510, 0.997957] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 497/500 [0.982510, 0.997957] | 500/500 | 265 / 232 | 232 / 232 |
| Fixed slices (own family) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | 500/500 | 0 / 500 | 500 / 500 |
| Abstain reference | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | NA | 0 / 0 | 0 / 0 |
| Status quo (uncertified) | 500/500 [0.992376, 1.000000] | 0/500 [0.000000, 0.007624] | 0/500 [0.000000, 0.007624] | 500/500 [0.992376, 1.000000] | NA | 500 / 0 | 0 / 0 |

## 返回策略的效用、服务与真实风险超限：全部arm

`n_R`是实际返回数；Umean、gainmean、risk-excess均只在这n_R个返回上取均值，无返回记NA。`service_all`在500trials上平均、弃权贡献0；`service_R`由同一保存统计量与返回数转换，表示已返回策略的平均expected service。capacity与service在本设计相同，完整原值在JSON。不能把很小的service_all误读成返回策略违反.2服务下限。

### cycle-moderate-mixed

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.247512872 | 0.0544884743 | 0.449999998 | 0.449999998 | 0 |
| In-sample (heuristic) | 500 | 0.247512872 | 0.0544884743 | 0.449999998 | 0.449999998 | 0 |
| Global (primary certified) | 351 | 0.239995764 | 0.0469713659 | 0.315900001 | 0.450000002 | 0 |
| COMET (primary certified) | 500 | 0.247495697 | 0.0544712989 | 0.449999998 | 0.449999998 | 0 |
| Matched generic (primary certified) | 500 | 0.247495697 | 0.0544712989 | 0.449999998 | 0.449999998 | 0 |
| Fixed slices (own family) | 500 | 0.260091466 | 0.0670670674 | 0.449999999 | 0.449999999 | 0.157008108 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.193024398 | 0 | 0.35 | 0.35 | 0 |

### cycle-moderate-null

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.243195958 | 0.0594723221 | 0.449999999 | 0.449999999 | 0 |
| In-sample (heuristic) | 500 | 0.243195958 | 0.0594723221 | 0.449999999 | 0.449999999 | 0 |
| Global (primary certified) | 454 | 0.237101751 | 0.0533781145 | 0.4086 | 0.449999999 | 0 |
| COMET (primary certified) | 500 | 0.243195958 | 0.0594723221 | 0.449999999 | 0.449999999 | 0 |
| Matched generic (primary certified) | 500 | 0.243195958 | 0.0594723221 | 0.449999999 | 0.449999999 | 0 |
| Fixed slices (own family) | 500 | 0.243195958 | 0.0594723221 | 0.449999999 | 0.449999999 | 0 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.183723636 | 0 | 0.35 | 0.35 | 0 |

### cycle-weak-mixed

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.248408127 | 0.0553837285 | 0.449999998 | 0.449999998 | 0.000415714982 |
| In-sample (heuristic) | 500 | 0.248408127 | 0.0553837285 | 0.449999998 | 0.449999998 | 0.000415714982 |
| Global (primary certified) | 0 | NA | NA | 0 | NA | NA |
| COMET (primary certified) | 340 | 0.241447658 | 0.0484232595 | 0.306 | 0.450000001 | 0 |
| Matched generic (primary certified) | 340 | 0.241447658 | 0.0484232595 | 0.306 | 0.450000001 | 0 |
| Fixed slices (own family) | 500 | 0.246646035 | 0.0536216372 | 0.449999999 | 0.449999999 | 0.00557586267 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.193024398 | 0 | 0.35 | 0.35 | 0 |

### cycle-weak-null

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.242793317 | 0.059069681 | 0.449999999 | 0.449999999 | 0 |
| In-sample (heuristic) | 500 | 0.242793317 | 0.059069681 | 0.449999999 | 0.449999999 | 0 |
| Global (primary certified) | 0 | NA | NA | 0 | NA | NA |
| COMET (primary certified) | 238 | 0.237120962 | 0.0533973256 | 0.2128 | 0.447058823 | 0 |
| Matched generic (primary certified) | 238 | 0.237120962 | 0.0533973256 | 0.2128 | 0.447058823 | 0 |
| Fixed slices (own family) | 500 | 0.242554467 | 0.0588308306 | 0.449999999 | 0.449999999 | 0 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.183723636 | 0 | 0.35 | 0.35 | 0 |

### independent-moderate-mixed

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.247683437 | 0.0546590389 | 0.449999998 | 0.449999998 | 7.17610355e-06 |
| In-sample (heuristic) | 500 | 0.247683437 | 0.0546590389 | 0.449999998 | 0.449999998 | 7.17610355e-06 |
| Global (primary certified) | 340 | 0.240582176 | 0.0475577783 | 0.306000001 | 0.450000002 | 0 |
| COMET (primary certified) | 500 | 0.247516904 | 0.0544925062 | 0.449999998 | 0.449999998 | 0 |
| Matched generic (primary certified) | 500 | 0.247516904 | 0.0544925062 | 0.449999998 | 0.449999998 | 0 |
| Fixed slices (own family) | 500 | 0.26005424 | 0.0670298422 | 0.449999999 | 0.449999999 | 0.156087154 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.193024398 | 0 | 0.35 | 0.35 | 0 |

### independent-moderate-null

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.243181249 | 0.0594576128 | 0.449999999 | 0.449999999 | 0 |
| In-sample (heuristic) | 500 | 0.243181249 | 0.0594576128 | 0.449999999 | 0.449999999 | 0 |
| Global (primary certified) | 411 | 0.23767037 | 0.0539467335 | 0.3699 | 0.45 | 0 |
| COMET (primary certified) | 500 | 0.243181089 | 0.059457453 | 0.449999999 | 0.449999999 | 0 |
| Matched generic (primary certified) | 500 | 0.243181089 | 0.059457453 | 0.449999999 | 0.449999999 | 0 |
| Fixed slices (own family) | 500 | 0.243181089 | 0.059457453 | 0.449999999 | 0.449999999 | 0 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.183723636 | 0 | 0.35 | 0.35 | 0 |

### independent-weak-mixed

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.248509971 | 0.0554855726 | 0.449999998 | 0.449999998 | 0.000392888461 |
| In-sample (heuristic) | 500 | 0.248509971 | 0.0554855726 | 0.449999998 | 0.449999998 | 0.000392888461 |
| Global (primary certified) | 44 | 0.239853492 | 0.0468290935 | 0.0396 | 0.45 | 0 |
| COMET (primary certified) | 411 | 0.242829896 | 0.0498054977 | 0.3699 | 0.45 | 0 |
| Matched generic (primary certified) | 411 | 0.242829896 | 0.0498054977 | 0.3699 | 0.45 | 0 |
| Fixed slices (own family) | 500 | 0.256146392 | 0.0631219935 | 0.449999999 | 0.449999999 | 0.0851170008 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.193024398 | 0 | 0.35 | 0.35 | 0 |

### independent-weak-null

| arm | n_R | mean true utility | mean gain | service_all | service_R | mean max true risk excess |
|---|---:|---:|---:|---:|---:|---:|
| Point (heuristic) | 500 | 0.242224828 | 0.058501192 | 0.449999999 | 0.449999999 | 0 |
| In-sample (heuristic) | 500 | 0.242224828 | 0.058501192 | 0.449999999 | 0.449999999 | 0 |
| Global (primary certified) | 17 | 0.238209268 | 0.054485632 | 0.0153000001 | 0.450000003 | 0 |
| COMET (primary certified) | 497 | 0.209716214 | 0.0259925783 | 0.3943 | 0.39668008 | 0 |
| Matched generic (primary certified) | 497 | 0.209716214 | 0.0259925783 | 0.3943 | 0.39668008 | 0 |
| Fixed slices (own family) | 500 | 0.241981857 | 0.0582582204 | 0.449999999 | 0.449999999 | 0 |
| Abstain reference | 0 | NA | NA | 0 | NA | NA |
| Status quo (uncertified) | 500 | 0.183723636 | 0 | 0.35 | 0.35 | 0 |

## 真实违规检测、点比较错误与oracle comparator

D=family-any真违规认证，DC=发现并认证非all子群真违规，F=any false claim（Point/In-sample是heuristic point比较错误而非certificate error）。fixed-slice的DC预声明为NA。U与I在上表始终按primary约束；D/F则属于该arm自己的audited family。

| cell | COMET D / DC / F | Global D / DC / F | Fixed D / DC / F | Point D / DC / F | In-sample D / DC / F |
|---|---|---|---|---|---|
| cycle-moderate-mixed | 500 / 500 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 22 | 0 / 0 / 21 |
| cycle-moderate-null | 0 / 0 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| cycle-weak-mixed | 0 / 0 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 159 | 0 / 0 / 164 |
| cycle-weak-null | 0 / 0 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| independent-moderate-mixed | 500 / 500 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 33 | 0 / 0 / 33 |
| independent-moderate-null | 0 / 0 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| independent-weak-mixed | 0 / 0 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 145 | 0 / 0 / 180 |
| independent-weak-null | 0 / 0 / 0 | 0 / 0 / 0 | 0 / NA / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

matched generic逐端点与COMET相等；status quo不作certified风险声明，Abstain不作声明。原端点的全部Wilson与适用性已保留JSON。

| cell | mean oracle-best feasible utility (n=500) | COMET robust-slack mean / available count |
|---|---:|---|
| cycle-moderate-mixed | 0.247512872 | 0.247495697 / 500 |
| cycle-moderate-null | 0.243195958 | 0.241893215 / 500 |
| cycle-weak-mixed | 0.248332601 | 0.241693673 / 1 |
| cycle-weak-null | 0.242802552 | 0.238832627 / 13 |
| independent-moderate-mixed | 0.247682066 | 0.247516904 / 500 |
| independent-moderate-null | 0.243181291 | 0.242951757 / 500 |
| independent-weak-mixed | 0.248443314 | 0.241154693 / 141 |
| independent-weak-null | 0.242244919 | 0.232828529 / 54 |

oracle与robust comparator均evaluation-only，未用于选择。robust mean只跨存在robust-feasible candidate的trial，available count很小时不应与500-trial平均效用直接比较；完整各arm值/计数已在JSON保留。

## 配对global对照与独立diagnostics解读

| cell | COMET-minus-global SU mean difference | paired bootstrap pointwise95 |
|---|---:|---|
| cycle-moderate-mixed | 0.298 | [0.258, 0.338] |
| cycle-moderate-null | 0.092 | [0.068, 0.118] |
| cycle-weak-mixed | 0.68 | [0.63995, 0.722] |
| cycle-weak-null | 0.476 | [0.432, 0.518] |
| independent-moderate-mixed | 0.32 | [0.28, 0.362] |
| independent-moderate-null | 0.178 | [0.146, 0.212] |
| independent-weak-mixed | 0.734 | [0.694, 0.774] |
| independent-weak-null | 0.96 | [0.942, 0.976] |

**归因限制：** `independent_global`实际engine是`truncated_global_envelope`，即纯截断的global envelope/global graph；COMET/generic还允许eligible bounded dispatch。因此COMET-minus-global同时包含localization/envelope与bounded分支差异，不能单独归因为graph localization，也不能把这个global arm称为最强bounded baseline。充分匹配的强generic使用同一dispatch并完全相等；E2的三层pure truncation才单独隔离graph成本。

每行500个完整paired trial、2000次预声明bootstrap。COMET-minus-matched的16个cell×level配对均差0、CI[0,0]。所有CI为pointwise；不能称跨8cells或所有arms的同时优势结论。

- COMET四个moderate cells均SU=500/500且全nonbaseline/strictgain；weak cells中SU与非baseline改进必须分开：cycle-null的238包含7baseline，independent-null的497包含265baseline。后者真正NB-SU/G+只有232/500。
- Status quo每cell SU=500/500，但B=500、G+=0；NI型有用返回不等于policy repair。fixed-slice全返回且G+=500，但mixed环境出现大量unsafe，strictgain也不等于safe improvement。
- Point/In-sample有些环境比proper证书返回更多，却在independent-moderate-mixed有1/500、两个weak-mixed各19/500unsafe；不得据高返回率宣称有保证的有用性。
- Global在cycle-weak-mixed/null都完全弃权：U=0同时SU=0，零错误不能掩盖零服务。Abstain reference在全部cells同理。

## 同等数据预算（独立diagnostic）

- 共180,224,000行：training16,384,000、discovery32,768,000、certification131,072,000。按4000个trial计一次，不乘arms、levels或47个坐标。
- 暴露action1标签单位：training4,328,656、discovery8,650,671、certification34,614,972（每个暴露单位包含risk/utility两channel）。全4000trial统计已知，unknown=0；保存raw-debug的8trial/split计数另被复核，不能说全体观测被逐行独立验证。
- In-sample重复使用certification labels作搜索与point decision，没有获赠第二批独立certification数据。完整budget限制和独立验证限度保留于JSON。

## 可直接入论文的英文段落（建议文本）

All 4,000 independent three-split pipeline trials completed without execution or assessment failure. Each fixed cell contains 500 complete trials; all 32 eligible primary certificate comparisons covered their own complete 47-coordinate risk-plus-utility family in 500/500 trials, with no Holm undercoverage flag. Only the global, COMET and matched generic engines certify feasibility for the primary independently discovered constraints; fixed-slice coverage concerns a different family. An independent read-only reconstruction matched all saved decisions and joint endpoints, without refitting or replaying observations.

At the primary 95% level, COMET and its matched generic version returned a safe, feasible policy in 500/500 trials in every moderate-overlap cell. Under weak overlap, the corresponding counts were 340/500 and 238/500 for cycle mixed and null settings, and 411/500 and 497/500 for independent mixed and null settings. No COMET return violated a primary risk constraint or the utility/service conditions. The global comparator returned safe and useful policies in 0, 0, 44 and 17 of those weak-overlap trials, respectively. This comparison changes both localization and the eligible bounded branch: the global arm uses pure global-envelope truncation, whereas COMET can dispatch to bounded certificates. It therefore does not isolate a graph-localization effect. The fully matched generic comparator uses the same dispatch and has identical results; the E2 pure-truncation layers separately isolate graph cost. All reported performance intervals are pointwise, and zero observed unsafe returns do not establish zero risk or conditional safety given return.

Useful return alone does not measure policy repair. In the independent weak-overlap null cell, 265 of COMET’s 497 safe and useful returns were the unchanged baseline; only 232/500 trials returned a nonbaseline safe and useful policy with strictly positive utility gain. The status-quo reference was safe and noninferior in 500/500 trials in every cell, but never improved utility. Conversely, fixed-slice certificates covered their own family in 500/500 trials while their returned policies violated the primary discovered constraints in 500/500 trials in both moderate-overlap mixed cells, 82/500 cycle weak-overlap mixed trials and 459/500 independent weak-overlap mixed trials. Point constraints and in-sample auditing also made unsafe returns in 1/500 independent moderate-overlap mixed trials and 19/500 trials in each weak-overlap mixed cell. Abstention had no unsafe return but also no useful return.

## 来源

- main summary SHA256=`4afa6eccc2816d512eb844a504222b0319bbf35a6efc27bc6a4750ba5b46b77e`；analysis fingerprint=`3b86226fac1aaf0b871872c4b19c8656f9e87acaac65ab565b0ffc0367cf2a4d`。
- independent diagnostics SHA256=`88fffca2325350fbcb2cfbfd0bb1e97b1e81b76dfebb752d80c3f060e6419074`；diagnostic fingerprint=`c104ed56b288c2d345ac24773d942e5daf8753a22c1701631d4f92d05fdcf0a1`。
- 共同protocol fingerprint=`f077fb800ffba466bafc42ad51ee4f98e4da41c399bc164937ed3b4ab658814b`；checkpoint inventory=`8fbc7481e4079ce3a058720599ae8e1f8a87dd8c46504ec13893cd9bba89e5d8`。

配套E5_completed_findings.json保留全部64主级及64次级joined rows、源精度Wilson、适用性、baseline/nonbaseline/strictgain所有诊断、实际m分布、utility/service/风险与comparator各自value_count，以及全部paired bootstrap。不得将500trial扩成500×47坐标或把零弃权/全弃权本身当作成功。
