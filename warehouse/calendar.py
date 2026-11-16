"""由 as_of 推出日、周、月周期键。不把不同日期合成同一天。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pipeline.errors import PeriodMixError

PeriodGrain = Literal["day", "week", "month"]

_CALIBER_TO_GRAIN = {"当日": "day", "当周": "week", "当月": "month"}


def grain_for_caliber(caliber: str) -> PeriodGrain:
    try:
        return _CALIBER_TO_GRAIN[caliber]
    except KeyError as exc:
        raise PeriodMixError(f"口径必须是当日、当周或当月: {caliber!r}") from exc


def period_key_for(as_of: str, grain: PeriodGrain) -> str:
    try:
        day = datetime.strptime(as_of, "%Y-%m-%d").date()
    except ValueError as exc:
        raise PeriodMixError(f"周期键需要完整日期 as_of: {as_of!r}") from exc
    if grain == "day":
        return day.isoformat()
    if grain == "week":
        iso = day.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    if grain == "month":
        return f"{day.year:04d}-{day.month:02d}"
    raise PeriodMixError(f"未知周期粒度: {grain!r}")


def next_calendar_month(year_month: str) -> str:
    """下一个日历月。不是下一周。"""
    try:
        year_text, month_text = year_month.split("-")
        year, month = int(year_text), int(month_text)
        datetime(year, month, 1)
    except (ValueError, AttributeError) as exc:
        raise PeriodMixError(f"参照月必须是 YYYY-MM: {year_month!r}") from exc
    if month == 12:
        return f"{year + 1}-01"
    return f"{year}-{month + 1:02d}"
