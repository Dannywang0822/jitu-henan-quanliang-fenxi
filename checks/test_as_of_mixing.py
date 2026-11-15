"""将 2026-11-08 损益与 2026-11-12 核心指标当作同一天必须失败。"""

import pytest
from pydantic import ValidationError

from kernel.dates import DatedReport, DifferentAsOfCannotBeSameDay, CrossDateContrast, as_same_day


def test_cannot_merge_pnl_and_core_as_same_day(core_metrics, pnl):
    left = DatedReport(report_id=pnl.report_id, as_of=pnl.as_of, title=pnl.title)
    right = DatedReport(report_id=core_metrics.report_id, as_of=core_metrics.as_of, title=core_metrics.title)
    with pytest.raises(DifferentAsOfCannotBeSameDay):
        as_same_day(left, right)


def test_cross_date_contrast_requires_label(core_metrics, pnl):
    reports = (
        DatedReport(report_id=pnl.report_id, as_of=pnl.as_of),
        DatedReport(report_id=core_metrics.report_id, as_of=core_metrics.as_of),
    )
    with pytest.raises((DifferentAsOfCannotBeSameDay, ValidationError)):
        CrossDateContrast(reports=reports, note="同一天经营对照")
    with pytest.raises((DifferentAsOfCannotBeSameDay, ValidationError)):
        CrossDateContrast(reports=reports, note="对照")
    ok = CrossDateContrast(reports=reports, note="可对照但必须标明不同 as_of，不是同一天")
    assert ok.is_same_day is False


def test_same_day_ok_for_single_report(core_metrics):
    a = DatedReport(report_id=core_metrics.report_id, as_of=core_metrics.as_of)
    b = DatedReport(report_id="core_metrics_copy", as_of=core_metrics.as_of)
    assert as_same_day(a, b) == "2026-11-12"
