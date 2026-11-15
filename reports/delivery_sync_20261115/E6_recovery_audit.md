# E6 恢复核查（2026-11-15，仅交付收尾）

**结论：E6 仍为 `DATA_BLOCKED_NOT_FROZEN`。已找到一个公开原始 CSV 镜像候选，但没有取得有效文件，也没有证明它与原官方 ZIP 的字节或完整行列内容相同。** 本轮未准备数据、冻结协议、消费 E6 种子、运行实验或计算文件哈希；历史 E0 和已完成的 30,300 个新单位均未抽样。

已完整阅读现有 `experiments/semisynthetic_selective_labels.py`、`experiments/e6_runner.py`、E6 template／数据选择记录，并核对实际下载失败日志。结构化证据见同目录 `E6_recovery_audit.json`。

## 精确数据与处理契约

选定数据是 **2018 ACS 1-Year、California、person PUMS**，不是 2014–2018 五年数据、住房文件或别的州／年度。官方归档为 `csv_pca.zip`，loader 要求其中恰有一个 `psam_p06.csv`。官方目录显示该 ZIP 为约 64M，修改时间 2019-10-31 15:11；这只是目录元数据，不是文件内容认证。[官方访问页](https://www.census.gov/programs-surveys/acs/microdata/access/2018.html)、[官方目录](https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/)

本库的既定处理如下：

| 环节 | 既定规则 |
|---|---|
| 身份和版本 | `(SERIALNO, SPORDER)` 唯一；每行 `ST=6`；若有 `YEAR` 列须为 2018，否则年份由可信来源凭据绑定，不能仅凭文件名推断 |
| 筛选 | `AGEP>16 AND PINCP>100 AND WKHP>0 AND PWGTP>=1` |
| 标签 | 原始 `PINCP>50000`；现有 loader 不另乘 `ADJINC` |
| 十个协变量 | `AGEP,COW,SCHL,MAR,OCCP,POBP,RELP,WKHP,SEX,RAC1P`；通过筛选后将空数值协变量填为 `-1` |
| 设计特征 | `AGEP,SCHL,WKHP,SEX`，按全部合格固定 X 的最小／最大值缩放至 `[-1,1]`，不用标签 |
| 排序与权重 | 按人员键排序；`PWGTP` 仅用于资格筛选；目标是未加权有限总体 moment |
| 划分 | 整户保留，确定性户顺序并预留单人户补足；training 4,096、discovery 8,192、certification 16,384；禁止复制人员，不足或无法整户凑齐即 `AVAILABILITY_BLOCKED` |
| 导出 | covariates、人员键、split registry 与说明；不导出 `PINCP` 或标签。标签只在 logger/evaluator vault 中使用 |

官方说明区分 person／housing 文件，并以 `SERIALNO+SPORDER` 标识人员；标准人口估计需要调查权重，因此本库的未加权固定总体目标不能被写成 California 人口估计或收入干预因果效应。[2018 官方 ReadMe](https://www2.census.gov/programs-surveys/acs/tech_docs/pums/ACS2018_PUMS_README.pdf)、[2018 数据字典](https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/PUMS_Data_Dictionary_2018.txt)

## 实际可用性及合法渠道

- **正常官方渠道仍被阻止。** 历史本机请求为 DNS 失败／HTTP403；同一服务器 GET 为 HTTP403、curl22、4,861 字节错误页，并非 ZIP。当前服务器正常 HEAD 又返回 403；官方 2018 record-count CSV 也返回 403，故 California 原始行数尚未核得。未换代理、伪装 UA、绕过挑战或使用凭据。
- **已有缓存未找到。** 仅检查了本机 Downloads、COMET data 和已知 HF／folktables 缓存路径，以及现有服务器两个 COMET data 与同类缓存目录；没有有效的精确 ZIP 或 person CSV。此结论不冒充对用户所有目录的穷尽搜索。
- **公开 CSV 镜像候选。** `davidboetius/ACSIncome-2018-1-Year` 的 `psam_p06.csv` 在固定提交 `2c42fc79349462e98c7c8290a5f5e679a0ccd201` 标示为 267,297,811 字节。上传者称其为原 folktables Census 数据，但它是 CSV，并非原 ZIP；页面发布的镜像自有校验值不能证明官方 ZIP 同一。本轮服务器正常前缀请求超时、0 字节；本机标准 Range 请求连接超时，curl28、约 10.007 秒、0 字节。未取得可核字段或行数的内容。[镜像说明](https://huggingface.co/datasets/davidboetius/ACSIncome-2018-1-Year/raw/main/README.md)、[固定上传记录](https://huggingface.co/datasets/davidboetius/ACSIncome-2018-1-Year/commit/2c42fc79349462e98c7c8290a5f5e679a0ccd201)
- **Census 所链 AWS 分发未作替代。** 其 ACS PUMS 项目是 Data.world 的 RDF／Turtle 转换数据，没有核得精确 2018 CA person ZIP 或完整行列等价凭据，不能直接替换现有输入。[分发说明](https://registry.opendata.aws/census-dataworld-pums/)

公开可访问不等于已经证明版本同一；也不根据一条 403 推断原数据从世界上消失。Census 仍公开列出其下载与开放数据渠道。[官方开放数据说明](https://www.census.gov/topics/research/research-transparency-public-access/open-data.html)

当前存在两个独立阻塞：**镜像正常传输不可达**，以及**原官方 ZIP 同一／原始表等价未证**。即使解决前者，也不能靠改文件名或 `canonical source_url` 越过后者。

请求方法、请求 URL、已观测的跳转／effective URL、退出类型与超时上限见 JSON。既有服务器 GET 的 curl metadata 证实零跳转且 effective URL 与请求相同；本轮 metadata-only HEAD 未保存完整响应头／跳转链，JSON 明确记为未捕获，未虚构补全或为此重复请求。本机镜像 probe 在建立连接前超时，响应头文件为空，没有观测到响应 effective URL。

## 接受同副本前具体还缺什么

1. 优先取得正常官方 ZIP，或有可信原始下载凭据的现成缓存。若仅有 CSV 镜像，需固定镜像版本、来源链和未筛选／未变换的完整 person 表身份。
2. 检查 CA／2018／1-Year 版本、全部必要列、人员键唯一性、官方原始记录数，以及与可接受官方成员的逐行／必要列一致性或可审计原始下载凭据。文件名、大小或行数相等单独均不足。
3. 若接受同一原始 CSV 的镜像／重新封装，必须明确记录 **source-trust／packaging amendment**。自制 ZIP 不是原官方 ZIP；镜像内部完整性也不是官方来源认证。不能静默把预处理 MiniACSIncome、RDF、另一年度或五年数据塞入旧契约。
4. 维持上述资格、缺失值、排序、整户划分和 label-vault 规则。取得有效副本后，才交主任务做原契约必须的一次文件核验；本轮没有文件可供该核验，未调用 loader／prepare。

`freeze_e6` 在安装协议或消费种子前要求真实归档和非 fixture 的 prepared receipt、可用人数及精确整户划分；`run_e6` 拒绝替换 vault／抽样器并核验真实生产环境。当前无 E6 protocol、有效 archive 或 prepared population，1,000 个 E6 ID 仍只是未冻结的预留清单。本轮因未取得合格数据而未触发后续E6恢复流程；用户授权的剩余1,000个ID仍须在契约满足后才可执行。

本轮新失败证据仅三个小文件：`E6_mirror_probe/headers.txt`（空）、`stdout.txt`、`stderr.txt`；服务器 metadata 请求结果在 JSON 中记录。无原始数据需打入审阅包。**本轮新计算文件 hash 数为 0；没有对旧结果或全仓库做校验扫描。**
