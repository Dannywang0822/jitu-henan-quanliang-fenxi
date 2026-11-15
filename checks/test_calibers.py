"""用错环比或 11 月累计口径必须失败。"""

import pytest
from pydantic import ValidationError

from kernel.ratios import (
    CumulativeKind,
    CumulativeMetric,
    MissingMomTypeError,
    MomChange,
    MomType,
    WrongCumulativeCaliberError,
    as_daily_average,
    as_monthly_total,
    merge_mom,
    parse_mom_type,
)


def test_mom_requires_type():
    with pytest.raises(MissingMomTypeError):
        parse_mom_type(None)
    with pytest.raises((MissingMomTypeError, ValidationError)):
        MomChange(field_id="揽收量_当日", value="8.6", unit="万票", mom_type="")


def test_cannot_mix_mom_types():
    a = MomChange(field_id="揽收量_当日", value="8.6", unit="万票", mom_type=MomType.比上一营业日)
    b = MomChange(field_id="收入累计", value="0.01", unit="比率", mom_type=MomType.比上月同期进度)
    with pytest.raises(MissingMomTypeError):
        merge_mom(a, b)


def test_core_november_cumulative_is_daily_avg_not_monthly_total(core_metrics):
    m = core_metrics.get("揽收量_11月累计")
    assert m.caliber == "累计日均"
    metric = CumulativeMetric(
        field_id=m.field_id,
        value=m.value,
        unit=m.unit,
        kind=CumulativeKind.累计日均,
        as_of=m.as_of,
    )
    assert as_daily_average(metric) == metric.value
    with pytest.raises(WrongCumulativeCaliberError):
        as_monthly_total(metric)


def test_pnl_cumulative_intake_is_monthly_count(pnl):
    m = pnl.get("累计收件")
    assert m.caliber == "月累计件数"
    metric = CumulativeMetric(
        field_id=m.field_id,
        value=m.value,
        unit=m.unit,
        kind=CumulativeKind.月累计件数,
        as_of=m.as_of,
        days_elapsed=8,
    )
    assert as_monthly_total(metric) == metric.value
    with pytest.raises(WrongCumulativeCaliberError):
        as_daily_average(
            CumulativeMetric(
                field_id=m.field_id,
                value=m.value,
                unit=m.unit,
                kind=CumulativeKind.月累计件数,
                as_of=m.as_of,
            )
        )
    assert as_daily_average(metric) == metric.value / 8


def test_fixture_mom_types(core_metrics, pnl):
    assert core_metrics.default_mom_type == "比上一营业日"
    assert pnl.default_mom_type == "比上月同期进度"
