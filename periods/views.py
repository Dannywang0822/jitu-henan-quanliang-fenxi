"""按日、按周、按月分面呈现。三种粒度不共用行。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from kernel.output import INFORMAL_MARK
from pipeline.errors import PeriodMixError
from warehouse.rows import WideRow

Horizon = Literal["当日", "当周", "当月"]
Grain = Literal["day", "week", "month"]

_HORIZON: dict[Grain, Horizon] = {"day": "当日", "week": "当周", "month": "当月"}


class PeriodResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    grain: Grain
    period_key: str
    horizon: Horizon
    rows: tuple[WideRow, ...]
    plan: str
    detailed_calc: str
    informal_mark: Literal["测试，非正式"] = INFORMAL_MARK
    layer: Literal["test"] = "test"

    @model_validator(mode="after")
    def _one_period(self) -> "PeriodResult":
        if _HORIZON[self.grain] != self.horizon:
            raise PeriodMixError("呈现名称与周期粒度不一致")
        if not self.plan.strip() or not self.detailed_calc.strip():
            raise ValueError("周期结果必须同时有方案和详细测算")
        for row in self.rows:
            if row.period_grain != self.grain or row.period_key != self.period_key:
                raise PeriodMixError(
                    f"不得串期: {row.period_grain}:{row.period_key} 不能放进 {self.horizon} {self.period_key}"
                )
            if row.informal_mark != INFORMAL_MARK or row.layer != "test":
                raise PeriodMixError("周期结果只能收测试层行")
        return self


class LinkageBoard(BaseModel):
    """三档对照。联动是分面，不是把一日改标成一周或一月。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    day: PeriodResult
    week: PeriodResult
    month: PeriodResult
    informal_mark: Literal["测试，非正式"] = INFORMAL_MARK

    @model_validator(mode="after")
    def _separate(self) -> "LinkageBoard":
        if self.day.grain != "day" or self.week.grain != "week" or self.month.grain != "month":
            raise PeriodMixError("联动板必须分别是当日、当周、当月")
        day_ids = {row.row_id for row in self.day.rows}
        week_ids = {row.row_id for row in self.week.rows}
        month_ids = {row.row_id for row in self.month.rows}
        if day_ids & week_ids or day_ids & month_ids or week_ids & month_ids:
            raise PeriodMixError("日、周、月结果不得共用同一行")
        return self


def present(rows: tuple[WideRow, ...] | list[WideRow], grain: Grain, period_key: str) -> PeriodResult:
    selected = tuple(row for row in rows if row.period_grain == grain and row.period_key == period_key)
    horizon = _HORIZON[grain]
    if selected:
        calc = "；".join(
            (
                f"{row.field_id}={row.value}{row.unit}"
                f"（{row.caliber}，{row.source_type}，来源文件 {row.source_file_id}，{row.department}）"
            )
            for row in selected
        )
    else:
        calc = f"{horizon} {period_key} 没有已入测试层宽表的行"
    return PeriodResult(
        grain=grain,
        period_key=period_key,
        horizon=horizon,
        rows=selected,
        plan=f"只呈现{horizon} {period_key} 的测试层结果，不串到其他周期",
        detailed_calc=calc,
    )
