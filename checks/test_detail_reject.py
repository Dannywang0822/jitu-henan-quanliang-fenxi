"""明细列整列拒绝，不入候选字典，不落存。"""

import pytest

from kernel.detail import DetailColumnRejected, filter_or_reject_columns, reject_detail_column
from data_interface.ingest import ingest_records


@pytest.mark.parametrize(
    "column",
    [
        "薪酬明细",
        "个人工资",
        "运单明细",
        "客户名单",
        "车辆轨迹",
        "趟次明细",
        "加盟合同",
    ],
)
def test_detail_columns_rejected(column: str):
    with pytest.raises(DetailColumnRejected):
        reject_detail_column(column, values=["不应落存的值"])
    with pytest.raises(DetailColumnRejected):
        filter_or_reject_columns([column, "揽收量_当日"])


def test_detail_column_ingest_rejected():
    with pytest.raises(DetailColumnRejected):
        ingest_records([
            {
                "field_id": "薪酬明细",
                "value": "1",
                "unit": "元",
                "caliber": "明细",
                "as_of": "2026-11-12",
                "source_type": "Danny提供的汇总",
            }
        ])


def test_legal_fixtures_have_no_detail_columns(staffing, core_metrics, pnl):
    for report in (staffing, core_metrics, pnl):
        names = [m.field_id for m in report.metrics]
        filter_or_reject_columns(names)


def test_trajectory_break_summary_is_not_detail(core_metrics):
    # 轨迹断更是票数汇总，不是轨迹明细
    assert core_metrics.get("轨迹断更_当日").unit == "票"
    filter_or_reject_columns(["轨迹断更"])
