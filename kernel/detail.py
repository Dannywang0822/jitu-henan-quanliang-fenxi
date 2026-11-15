"""明细列整列拒绝，不入候选字典，不落存。"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


class DetailColumnRejected(ValueError):
    """明细列被拒绝。"""


# 识别到这些形态时整列拒绝。
DETAIL_NAME_HINTS = (
    "薪酬明细",
    "工资明细",
    "个人工资",
    "银行账户",
    "银行卡",
    "证件号",
    "身份证",
    "工号清单",
    "员工名单",
    "运单明细",
    "运单号",
    "客户明细",
    "客户名单",
    "客户电话",
    "车辆轨迹",
    "轨迹明细",
    "逐车",
    "趟次明细",
    "加盟合同",
    "合同原文",
    "单商户结算",
    "结算明细",
)

# 明确允许出现在汇总表里的易混淆列名（不是明细落存）。
ALLOWED_SUMMARY_EXCEPTIONS = {
    "轨迹断更",  # 核心指标里是票数汇总，不是轨迹明细
}


def is_detail_column(column_name: str) -> bool:
    text = column_name.strip()
    if text in ALLOWED_SUMMARY_EXCEPTIONS:
        return False
    return any(hint in text for hint in DETAIL_NAME_HINTS)


def reject_detail_column(column_name: str, values: Sequence[Any] | None = None) -> None:
    if is_detail_column(column_name):
        if values:
            # 明确不落存：调用方即使传入值也不应被接收。
            raise DetailColumnRejected(
                f"明细列整列拒绝，不入候选字典，不落存: {column_name}"
            )
        raise DetailColumnRejected(
            f"明细列整列拒绝，不入候选字典，不落存: {column_name}"
        )


def filter_or_reject_columns(columns: Iterable[str] | Mapping[str, Any]) -> list[str]:
    """返回可通过的列名；遇到明细列立即失败，不返回也不保存明细值。"""
    names = list(columns.keys()) if isinstance(columns, Mapping) else list(columns)
    accepted: list[str] = []
    for name in names:
        if is_detail_column(name):
            reject_detail_column(name, None)
        accepted.append(name)
    return accepted
