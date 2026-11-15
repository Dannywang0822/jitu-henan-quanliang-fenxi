# 第一轮验证证据

- 记录时点：2026-11-15 23:38:41（Asia/Shanghai）
- 被测修订：`27d07245f092e92c3cfa399d0ddff27758b4dc65`
- 被测时工作区：干净；本证据随后单独提交。
- 命令：`checks/run.sh`
- 环境：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- 总结果：checks/run.sh 退出码 0，pytest 62 passed。

字段按技能要求逐项记录如下。

## 1. 固定入口 checks/run.sh 必须在仓库根目录可执行，全部检查通过才算本轮完成

- `requirement`：固定入口 checks/run.sh 必须在仓库根目录可执行，全部检查通过才算本轮完成
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：checks/run.sh
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：退出码 0，先重放测试层非正式输出，再跑 pytest checks，全部通过（62 项）
- `observed_result`：退出码 0。pytest 62 passed。测试层发现：件量不慢、利润偏慢、缺口主在揽件侧、运力口径不得合并、质量当日变差、云仓件量落后。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `checks/run.sh`
  - `test_layer/outputs/整体结论.md`
  - `test_layer/outputs/各部门重点关注目标.md`
  - `test_layer/outputs/test_report.json`
  - `formal_layer/README.md`
  - `dictionary/formal/README.md`
- `status`：PASS
- `blocker_if_any`：（无）

## 2. 缺来源类型或来源不在四类之内必须失败；合法夹具来源均为 Danny提供的汇总

- `requirement`：缺来源类型或来源不在四类之内必须失败；合法夹具来源均为 Danny提供的汇总
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_source_types.py（由 checks/run.sh 调用）
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：无来源或非法来源无法构造/录入；三张夹具均带 Danny提供的汇总
- `observed_result`：5 项通过。缺来源与「公司系统导出」被拒，四类合法来源可构造。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `checks/test_source_types.py`
  - `kernel/source.py`
  - `fixtures/`
- `status`：PASS
- `blocker_if_any`：（无）

## 3. 将 2026-11-08 损益与 2026-11-12 核心指标当作同一天必须失败；可对照但须标明不同 as_of

- `requirement`：将 2026-11-08 损益与 2026-11-12 核心指标当作同一天必须失败；可对照但须标明不同 as_of
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_as_of_mixing.py 及 checks/test_kernel_analysis.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：as_same_day 与未标明的跨日对照失败；测试层输出标明不同 as_of、不是同一天
- `observed_result`：混为同一天被拒。测试层 used_as_of 同时含 2026-11-08 与 2026-11-12，并写明不是同一天。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/dates.py`
  - `test_layer/outputs/整体结论.md`
- `status`：PASS
- `blocker_if_any`：（无）

## 4. 禁止合并两种单票人力，禁止跨表自动合并单公斤运力

- `requirement`：禁止合并两种单票人力，禁止跨表自动合并单公斤运力
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_metric_separation.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：forbid_merge / auto_merge 对上述字段对抛 FieldMergeForbidden；夹具保持分字段
- `observed_result`：4 项通过。夹具中分别为 单票人力_考核* 与 单票操作人力成本*，以及 单公斤运力_核心指标* 与 单公斤运力_损益日报*。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/metrics.py`
  - `fixtures/core_metrics_2026-11-12.json`
  - `fixtures/pnl_2026-11-08.json`
- `status`：PASS
- `blocker_if_any`：（无）

## 5. 用错环比或「11月累计」口径必须失败（件量累计日均 vs 月累计件数；环比须分类型）

- `requirement`：用错环比或「11月累计」口径必须失败（件量累计日均 vs 月累计件数；环比须分类型）
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_calibers.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：无类型环比、混用环比口径、把累计日相当月合计或把月累计件数直接当日均，均失败
- `observed_result`：5 项通过。核心指标 揽收量_11月累计 口径为累计日均 592.2；损益 累计收件 为月累计件数 4528，÷8 天才得日均 566。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/ratios.py`
  - `checks/test_calibers.py`
- `status`：PASS
- `blocker_if_any`：（无）

## 6. 预算达成率=实际/预算；拒绝计算或接受 2−实际/预算（含印刷 173.61%、173.28%）

- `requirement`：预算达成率=实际/预算；拒绝计算或接受 2−实际/预算（含印刷 173.61%、173.28%）
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_achievement_rate.py 及测试层内核测算
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：12853/48711≈26.39%，171/641≈26.68%；印刷 173% 被拒绝，不得当正确结论
- `observed_result`：通过。模型重算 26.39% 与 26.68%，并在整体详细测算中写明拒绝印刷 173.61%/173.28%。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/ratios.py`
  - `test_layer/outputs/整体结论.md`
  - `fixtures/pnl_2026-11-08.json`
- `status`：PASS
- `blocker_if_any`：（无）

## 7. 测试结果不能写入正式层；未点头的 promote 必须失败；正式层与正式字典未晋升前为空（除 README/.gitkeep）

- `requirement`：测试结果不能写入正式层；未点头的 promote 必须失败；正式层与正式字典未晋升前为空（除 README/.gitkeep）
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_formal_isolation.py checks/test_kernel_analysis.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：write_text_from_test_layer 写 formal_layer 或 dictionary/formal 失败；approved=False 的 promote 失败且不落盘；仓库正式目录仅占位文件
- `observed_result`：6+ 相关项通过。运行测试层后 formal_layer 与 dictionary/formal 仍仅有 .gitkeep 与 README.md。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/promotion.py`
  - `kernel/isolation.py`
  - `formal_layer/`
  - `dictionary/formal/`
- `status`：PASS
- `blocker_if_any`：（无）

## 8. 明细列整列拒绝，不入候选字典，不落存；不以负责人姓名做主键

- `requirement`：明细列整列拒绝，不入候选字典，不落存；不以负责人姓名做主键
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_detail_reject.py checks/test_field_keys.py checks/test_kernel_analysis.py::test_candidates_do_not_contain_detail_or_person_keys
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：薪酬/运单或客户/车辆轨迹或趟次/加盟合同等明细列被拒；负责人、姓名、示例姓名不能当字段主键；夹具可记有负责人姓名列但不用作主键
- `observed_result`：通过。核心指标夹具注明有负责人姓名列但模型不以人名为主键，未写入具体姓名。候选 JSON 不含姓名/明细字段。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/detail.py`
  - `kernel/fields.py`
  - `dictionary/candidates/`
- `status`：PASS
- `blocker_if_any`：（无）

## 9. 输出必须同时有方案和详细测算，分整体结论与各部门重点关注目标；对不上则不能作为完整呈报；九个部门都要出现，无动作或缺数仍标明

- `requirement`：输出必须同时有方案和详细测算，分整体结论与各部门重点关注目标；对不上则不能作为完整呈报；九个部门都要出现，无动作或缺数仍标明
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_output_completeness.py checks/test_kernel_analysis.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：缺方案、缺测算、缺部门、发现项无部门支撑、不同 as_of 未标明，均不能构成 TwoLayerReport；内核产出九部门且含缺数/无动作
- `observed_result`：通过。部门顺序为客服、人资行政、总经办、市场、质控、网络管理、财务、营运、云仓。客服/网络管理为缺数，总经办为无动作。输出文件均有方案与详细测算，并标明测试，非正式。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/output.py`
  - `test_layer/outputs/整体结论.md`
  - `test_layer/outputs/各部门重点关注目标.md`
- `status`：PASS
- `blocker_if_any`：（无）

## 10. 有损益恒等式输入时，利润分项加总不平衡必须失败；合法夹具 收入−成本=毛利、毛利−费用=净利

- `requirement`：有损益恒等式输入时，利润分项加总不平衡必须失败；合法夹具 收入−成本=毛利、毛利−费用=净利
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_pnl_identity.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：13435−12853=582，582−171=411 通过；改净利或毛利则失败
- `observed_result`：2 项通过。夹具 identity 平衡，人为不平衡输入被拒。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/pnl.py`
  - `fixtures/pnl_2026-11-08.json`
- `status`：PASS
- `blocker_if_any`：（无）

## 11. 测试层测算必须从夹具计算得出，并在夹具支撑时得出已知经营判断方向（件量不慢、利润偏慢、缺口主在揽件侧、运力不得合并、质量变差、云仓落后）；缺数须标明

- `requirement`：测试层测算必须从夹具计算得出，并在夹具支撑时得出已知经营判断方向（件量不慢、利润偏慢、缺口主在揽件侧、运力不得合并、质量变差、云仓落后）；缺数须标明
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：python -m test_layer.run 以及 pytest checks/test_kernel_analysis.py
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：发现项与方向由夹具算出，不把结论写死；缺同一天对照表、覆盖/加盟政策结果、运力结构/储备
- `observed_result`：计算出件量不慢、利润偏慢、缺口主在揽件侧、运力口径不得合并、质量当日变差、云仓件量落后。累计净利达成按 411/2169 得 18.95%（印刷 18.94%），时间进度 8/30=26.67%（约 27%）。整体缺数三项均已标明。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/analysis.py`
  - `test_layer/run.py`
  - `test_layer/outputs/整体结论.md`
  - `test_layer/outputs/各部门重点关注目标.md`
  - `test_layer/outputs/test_report.json`
- `status`：PASS
- `blocker_if_any`：（无）

## 12. 不存在极兔内部系统连接器；运力不是独立部门，只挂在营运之下；本轮无飞书、无 H5 页面、无新建 bot

- `requirement`：不存在极兔内部系统连接器；运力不是独立部门，只挂在营运之下；本轮无飞书、无 H5 页面、无新建 bot
- `tested_commit`：27d07245f092e92c3cfa399d0ddff27758b4dc65
- `tested_worktree_diff`：被测时 git 工作区相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 干净；本证据文件在检查通过后写入，随后单独提交，不改被测代码。
- `command_or_action`：pytest checks/test_no_internal_connector.py checks/test_departments.py；并审阅仓库目录
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:38:41；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；解释器 .venv/bin/python；Linux x86_64 glibc 2.41
- `expected_result`：connect_jitu_internal 必失败；解析「运力部」失败；仓库无内部连接器模块，无飞书/页面/新 bot 代码
- `observed_result`：通过。部门枚举九个，运力归属营运。未接入飞书、未做 H5、未新建 bot。
- `exit_code_if_applicable`：0
- `artifact_paths`：
  - `kernel/connectors.py`
  - `departments/营运/capacity.py`
- `status`：PASS
- `blocker_if_any`：（无）

## 补记（可复现性）

在 `27d07245f092e92c3cfa399d0ddff27758b4dc65` 上首次记录证据后，发现识别结果含墙钟 `generated_at`，重跑会弄脏工作区。已在 `54e78aa41c748c970e5e47d58bdc084a91802675` 去掉该时间戳。于该提交上重跑 `checks/run.sh`，退出码 0，工作区干净。

- `requirement`：检查入口可复现：重跑不得因时间戳改写候选字典；全部检查仍通过，正式层仍空
- `tested_commit`：54e78aa41c748c970e5e47d58bdc084a91802675
- `tested_worktree_diff`：被测代码为 54e78aa41c748c970e5e47d58bdc084a91802675（相对 27d07245f092e92c3cfa399d0ddff27758b4dc65 仅去掉候选字典 generated_at，使 checks/run.sh 可复现）。检查重跑后工作区干净。本补记在检查通过后写入并单独提交。
- `command_or_action`：checks/run.sh（在 54e78aa 上重跑，随后 git status）
- `relevant_environment`：Asia/Shanghai 2026-11-15 23:40 左右；cwd=/workspace/jitu-henan-quanliang-fenxi；Python 3.13.5；pydantic 2.14.3；pytest 9.2.0；.venv/bin/python
- `expected_result`：退出码 0，工作区保持干净，正式层与正式字典仍仅占位文件
- `observed_result`：退出码 0，pytest 62 passed，git status 干净。
- `exit_code_if_applicable`：0
- `artifact_paths`：`data_interface/recognize.py`、`dictionary/candidates/`、本文件
- `status`：PASS
- `blocker_if_any`：（无）
