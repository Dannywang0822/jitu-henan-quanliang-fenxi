# 极兔河南全量分析（决策平台）

仓库地址：https://github.com/Dannywang0822/jitu-henan-quanliang-fenxi

本仓库现已按要求改为公开库，用于河南经营决策、成本管控和收入分析的决策中枢。经理能看、主管能用；同一模型内核上挂各部门视角，不按部门另建系统。

当前是测试层第一轮：已接入编制对照、2026-11-08 损益日报、2026-11-12 核心指标三张汇总，可跑两层测算（整体结论 / 各部门重点关注目标）。测算均标明「测试，非正式」。正式输出层仍为空，须校验通过并另一次点头后才晋升。H5 测试层页面在 `h5/`，方案见 `H5_PAGE_SPEC.md`。在线预览：[https://dannywang0822.github.io/jitu-henan-quanliang-fenxi/](https://dannywang0822.github.io/jitu-henan-quanliang-fenxi/)。本地预览：在 `h5/` 目录执行 `python3 -m http.server 8765`，再用浏览器打开 [http://127.0.0.1:8765/](http://127.0.0.1:8765/)。飞书登录尚未接入。

## 本地检查

在仓库根目录执行：

```bash
./checks/run.sh
```

通过后会重放测试层非正式输出，路径：

- `test_layer/outputs/整体结论.md`
- `test_layer/outputs/各部门重点关注目标.md`

## H5 测试层页面

移动优先，三个入口：整体结论、各部门重点关注目标、上传录入。全程标明「测试，非正式」。上传只收汇总，默认进入测试层待处理，不写入正式层。GitHub Pages 仅发布 `h5/`，全程仍标明「测试，非正式」。

## 约定

- 只收汇总、假设、政策参数、公开信号和已授权汇总，不收公司明细，不对接内部系统。
- 数字必须标明来源：假设 / 公开来源 / 合规授权汇总 / Danny提供的汇总。
- 不同日期的报表不得混为同一天；测试层写不进正式层。

更完整的接口与门禁见 `TASK_CONTRACT.md`、`DECISION_HUB.md`、`FIELD_DICTIONARY.md`、`L5_PREBUILD.md`。
