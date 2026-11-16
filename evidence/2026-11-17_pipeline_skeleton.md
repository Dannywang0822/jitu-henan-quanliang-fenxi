# 经营管理流水线骨架验证证据

- 记录时点：2026-11-17 01:08:54（Asia/Shanghai）
- 被测修订：`c602d777acb5a6f51250d955d376c20b241fe764`
- 被测时工作区：相对该修订干净。本证据在检查通过后写入，随后单独提交，不改被测代码。
- 命令：`checks/run.sh`
- 环境：Asia/Shanghai 2026-11-17 01:08:54；cwd=/workspace；Python 3.12.3；pydantic 2.14.3；pytest 9.2.0；解释器 python3；Linux x86_64 glibc 2.39
- 总结果：`checks/run.sh` 退出码 0。pytest 76 passed（含原有 62 项与本轮 14 项）。流水线自检打印「骨架不变量通过」，测试层宽表 5 行，正式层 0 行。

云资源尚未开通。本轮没有购买套餐，没有登录或部署 CloudBase、对象存储、PostgreSQL 或轻量服务器。合成夹具只用假设整数，不含经营明细。

## 1. 固定入口覆盖旧检查和新流水线不变量

- `requirement`：`checks/run.sh` 先重放测试层非正式输出，再跑全部 pytest，再跑经营管理流水线骨架自检；旧检查仍通过，正式层仍空
- `tested_commit`：c602d777acb5a6f51250d955d376c20b241fe764
- `tested_worktree_diff`：被测时工作区相对 c602d777acb5a6f51250d955d376c20b241fe764 干净。本证据随后单独提交。
- `command_or_action`：checks/run.sh
- `relevant_environment`：Asia/Shanghai 2026-11-17 01:08:54；cwd=/workspace；Python 3.12.3；pydantic 2.14.3；pytest 9.2.0；python3；Linux x86_64 glibc 2.39
- `expected_result`：退出码 0；pytest 76 passed；自检看到测试层 5 行、正式层 0 行；仓库 formal_layer 与 dictionary/formal 仍只有占位文件
- `observed_result`：退出码 0。pytest 76 passed。自检输出「骨架不变量通过」和「测试层宽表 5 行，正式层 0 行」。重跑后 git status 干净。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `checks/run.sh`
  - `checks/test_pipeline_skeleton.py`
  - `pipeline/selfcheck.py`
  - `PIPELINE_DESIGN.md`
  - `formal_layer/README.md`
  - `dictionary/formal/README.md`
- `status`：PASS
- `blocker_if_any`：（无）

## 2. 明细拒收且不落存；字典未完全一致不得入宽表

- `requirement`：运单、客户、轨迹、薪酬明细整份拒收，不进对象存储，不进宽表；表头、单位或口径与字典不完全一致时可以留在存储，但宽表行数为 0；只对上一部分列也不得入宽表
- `tested_commit`：c602d777acb5a6f51250d955d376c20b241fe764
- `tested_worktree_diff`：干净
- `command_or_action`：pytest checks/test_pipeline_skeleton.py（由 checks/run.sh 调用）以及 pipeline.selfcheck
- `relevant_environment`：同上
- `expected_result`：`syn-detail-001` 被拒且存储键中没有它；哨兵取值不出现在异常文本、对象存储或宽表。`syn-front-mismatch`、`syn-front-partial`、`syn-analysis-mismatch` 已存储但未入宽表
- `observed_result`：通过。明细列名被拒。部分匹配被标成未完全一致。不一致文件没有出现在宽表的来源文件编号里。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `storage/fixtures/detail_rejected.json`
  - `storage/fixtures/frontline_mismatch.json`
  - `storage/fixtures/frontline_partial.json`
  - `storage/fixtures/analysis_mismatch.json`
  - `ingest/dictionary.py`
  - `ingest/upload.py`
  - `storage/objects.py`
- `status`：PASS
- `blocker_if_any`：（无）

## 3. 杂乱底表识别后入测试层宽表，每行带来源文件编号和部门

- `requirement`：基层原始底表的别名在单位和口径一致时映射到字典字段，并与经营分析组汇总表一起写入测试层宽表；每行有来源文件编号和部门；结果标明「测试，非正式」
- `tested_commit`：c602d777acb5a6f51250d955d376c20b241fe764
- `tested_worktree_diff`：干净
- `command_or_action`：python -m pipeline.selfcheck（由 checks/run.sh 调用）
- `relevant_environment`：同上
- `expected_result`：`揽收件数(票)` 映射到 `揽收量_当日`。宽表来源文件为 syn-front-daily、syn-front-week、syn-front-month、syn-analysis-month。部门只有营运和财务。全部是测试层，并带「测试，非正式」
- `observed_result`：通过。测试层宽表 5 行。日表两行来自同一文件编号、不同日期。月成本来自财务的经营分析组文件。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `storage/fixtures/frontline_daily.json`
  - `storage/fixtures/synthetic_dictionary.json`
  - `parse/wide_table.py`
  - `parse/function.py`
  - `warehouse/rows.py`
  - `warehouse/schema_sqlite.sql`
  - `warehouse/schema_postgres.sql`
- `status`：PASS
- `blocker_if_any`：（无）

## 4. 日、周、月不串期；下个月不是下个周；测试层标明非正式

- `requirement`：当日、当周、当月分别呈现，不得共用行；下个月测算的目标是参照月的下一个日历月，内容含投入、打法、政策调动、成本优化；不得写成下个周。正式层未晋升前这些结果只在测试层
- `tested_commit`：c602d777acb5a6f51250d955d376c20b241fe764
- `tested_worktree_diff`：干净
- `command_or_action`：pipeline.selfcheck 与 pytest checks/test_pipeline_skeleton.py
- `relevant_environment`：同上
- `expected_result`：2026-11-02 只见合成值 100，2026-11-03 只见 80，2026-W45 只见 180，2026-11 当月只见揽收 400 与成本 50。下个月目标是 2026-12，输入字段只有揽收量_当月和成本_当月。把两天放进同一个当日结果会失败。`forecast_next_week` 失败
- `observed_result`：通过。联动板三档的非正式标记为「测试，非正式」。合成夹具的 as_of 不含 2026-11-08 和 2026-11-12。已有检查仍拒绝把这两天合成同一天。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `periods/views.py`
  - `periods/next_month.py`
  - `periods/formal_surfaces.py`
  - `storage/fixtures/frontline_week.json`
  - `storage/fixtures/frontline_month.json`
  - `storage/fixtures/analysis_month.json`
- `status`：PASS
- `blocker_if_any`：（无）

## 5. 不得自动晋升；正式层为空时三个正式表面不可用

- `requirement`：审批决定本身不写正式层。没有 Danny 点头不能签发晋升许可。直接写正式宽表和自动晋升都失败。正式层行数为 0 时，周运营台、决策逻辑、历史对比为不可用。仓库 `formal_layer/` 不被写入
- `tested_commit`：c602d777acb5a6f51250d955d376c20b241fe764
- `tested_worktree_diff`：干净
- `command_or_action`：pytest checks/test_pipeline_skeleton.py::test_no_auto_promotion_and_formal_surfaces_refuse
- `relevant_environment`：同上
- `expected_result`：内存库里，Danny 点头前的决定不增加正式行；未签发的许可不能晋升。内存库上的显式晋升后可以回滚到 0 行。仓库正式目录仍空
- `observed_result`：通过。自检结束时正式层 0 行。三个表面状态都是不可用。回滚演练只发生在 sqlite 内存库，没有写入 `formal_layer/`。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `access_control/approvals.py`
  - `access_control/accounts.py`
  - `warehouse/local_dual.py`
  - `pipeline/permit.py`
  - `formal_layer/`
- `status`：PASS
- `blocker_if_any`：（无）

## 6. 云边界与提需求入口保持关闭

- `requirement`：原始表或宽表写入文档库、开通经营管理环境、购买套餐、部署上线都失败。提需求不进入交数流水线。新代码不导入云 SDK。账号不开放注册
- `tested_commit`：c602d777acb5a6f51250d955d376c20b241fe764
- `tested_worktree_diff`：干净
- `command_or_action`：pytest checks/test_pipeline_skeleton.py 中的边界与注册检查
- `relevant_environment`：同上
- `expected_result`：上述入口抛出对应错误。自行注册失败。PostgreSQL schema 文件只作为设计，本地双的 backend 为 sqlite-memory
- `observed_result`：通过。检查没有连接外网云服务。`warehouse/schema_postgres.sql` 含 mgmt_test 与 mgmt_formal，检查只执行 sqlite 内存 schema。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `pipeline/boundaries.py`
  - `warehouse/schema_postgres.sql`
  - `PIPELINE_DESIGN.md`
- `status`：PASS
- `blocker_if_any`：（无）

## 本轮未做

- 未开通「经营管理」CloudBase 环境，未购买 COS、PostgreSQL 或轻量服务器，未部署，未改现网，未接飞书，未做真实登录。
- 未把测试层结果写入仓库正式层或正式字典。H5 只增补了规格，没有改现有页面。
