"""供 checks/run.sh 调用的流水线不变量自检。不写仓库文件。"""

from __future__ import annotations

from kernel.isolation import list_non_placeholder
from kernel.output import INFORMAL_MARK
from pipeline.walkthrough import repo_root, run_synthetic_walkthrough


def main() -> int:
    root = repo_root()
    report = run_synthetic_walkthrough(root)
    if report.informal_mark != INFORMAL_MARK:
        raise SystemExit("测试层闭环缺少「测试，非正式」")
    if not report.detail_rejected or report.detail_stored:
        raise SystemExit("明细表必须拒收且不落存")
    if report.formal_count != 0:
        raise SystemExit("骨架不得把测试层写入正式层")
    if any(view.status != "不可用" or view.available for view in report.surfaces):
        raise SystemExit("正式层为空时周运营台、决策逻辑、历史对比必须不可用")
    if report.next_month.horizon != "下个月" or report.next_month.target_month != "2026-12":
        raise SystemExit("下个月测算必须落到下一个日历月")
    if report.next_month.layer != "test" or report.linkage.informal_mark != INFORMAL_MARK:
        raise SystemExit("未晋升前的测算必须留在测试层并标明非正式")
    if set(report.next_month.input_field_ids) != {"揽收量_当月", "成本_当月"}:
        raise SystemExit("下个月测算只能使用当月粒度")
    if len(report.storage_keys) != 7:
        raise SystemExit("对象存储里的文件数量与两路夹具不一致")
    blocked = set(report.blocked_file_ids)
    leaked = {row.source_file_id for row in report.wide_rows} & blocked
    if leaked:
        raise SystemExit(f"字典未完全一致的文件进入了宽表: {sorted(leaked)}")
    if report.daily_header != "揽收件数(票)" or report.daily_field_id != "揽收量_当日":
        raise SystemExit("杂乱表头没有识别到字典字段")
    day_values = {row.value for row in report.linkage.day.rows}
    other_values = {row.value for row in report.other_day.rows}
    week_values = {row.value for row in report.linkage.week.rows}
    if day_values != {"100"} or other_values != {"80"} or week_values != {"180"}:
        raise SystemExit("日、周结果串期")
    month_values = {row.field_id: row.value for row in report.linkage.month.rows}
    if month_values != {"揽收量_当月": "400", "成本_当月": "50"}:
        raise SystemExit("当月结果不正确或串入了其他粒度")
    as_ofs = {row.as_of for row in report.wide_rows}
    if "2026-11-08" in as_ofs or "2026-11-12" in as_ofs:
        raise SystemExit("合成流水线不得使用 11-08 与 11-12")
    if list_non_placeholder(root / "formal_layer") or list_non_placeholder(root / "dictionary" / "formal"):
        raise SystemExit("仓库正式层或正式字典被写入")
    print("[pipeline] 骨架不变量通过")
    print(f"[pipeline] 测试层宽表 {len(report.wide_rows)} 行，正式层 {report.formal_count} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
