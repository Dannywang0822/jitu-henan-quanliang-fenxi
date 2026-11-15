# 测试层产出副本

本目录中的文件是 `test_layer/outputs/` 的副本，仅供 H5 静态预览读取：

- `test_report.json`（结构源，优先用于发现、方案、部门状态、缺数、as_of）
- `整体结论.md`（整体「详细测算」展开文本）
- `各部门重点关注目标.md`（各部门「详细测算」展开文本）

它们不是正式层数据，**禁止**复制到 `formal_layer/`。

若内核或测试层重新跑过（例如在仓库根目录执行 `./checks/run.sh` 会按夹具重放并覆盖 `test_layer/outputs/`），必须把产出重新同步到本目录，**不要在任一侧手改数字**。

在仓库根目录同步：

```bash
cp test_layer/outputs/test_report.json \
   test_layer/outputs/整体结论.md \
   test_layer/outputs/各部门重点关注目标.md \
   h5/data/
```
