"""下个月测算。期限是下一个日历月，不是下个周。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from kernel.output import INFORMAL_MARK
from pipeline.errors import NextMonthIsNotNextWeek
from warehouse.calendar import next_calendar_month
from warehouse.rows import WideRow

_TOPICS = ("投入", "打法", "政策调动", "成本优化")


class NextMonthForecast(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    horizon: Literal["下个月"] = "下个月"
    reference_month: str
    target_month: str
    topics: dict[str, str]
    input_field_ids: tuple[str, ...]
    plan: str
    detailed_calc: str
    informal_mark: Literal["测试，非正式"] = INFORMAL_MARK
    layer: Literal["test"] = "test"

    @model_validator(mode="after")
    def _month_not_week(self) -> "NextMonthForecast":
        if self.horizon != "下个月" or "周" in self.horizon:
            raise NextMonthIsNotNextWeek("下个月测算不得写成下个周")
        if self.target_month != next_calendar_month(self.reference_month):
            raise NextMonthIsNotNextWeek("下个月必须是参照月的下一个日历月")
        if "W" in self.target_month or "周" in self.target_month:
            raise NextMonthIsNotNextWeek("下个月目标不能是周键")
        missing = [topic for topic in _TOPICS if not str(self.topics.get(topic, "")).strip()]
        if missing:
            raise ValueError(f"下个月测算缺少: {', '.join(missing)}")
        blob = self.plan + self.detailed_calc + "".join(self.topics.values())
        if "下个周" in blob or "下周" in blob:
            raise NextMonthIsNotNextWeek("下个月测算不得写成下个周")
        if not self.plan.strip() or not self.detailed_calc.strip():
            raise ValueError("下个月测算必须同时有方案和详细测算")
        return self


def forecast_next_month(rows: tuple[WideRow, ...] | list[WideRow], reference_month: str) -> NextMonthForecast:
    month_rows = [row for row in rows if row.period_grain == "month" and row.period_key == reference_month]
    by_field = {row.field_id: row for row in month_rows}
    target = next_calendar_month(reference_month)
    volume = by_field.get("揽收量_当月")
    cost = by_field.get("成本_当月")
    volume_text = f"{volume.value}{volume.unit}" if volume else "缺当月揽收"
    cost_text = f"{cost.value}{cost.unit}" if cost else "缺当月成本"
    topics = {
        "投入": f"合成假设：维持当月测试层投入规模，测算到 {target}，不新增明细",
        "打法": f"合成假设：按 {reference_month} 的当月口径延续到 {target}，不改用周口径",
        "政策调动": f"合成假设：政策参数只在测试层试算，生效月为 {target}",
        "成本优化": f"合成假设：下月成本沿当月成本 {cost_text} 外推到 {target}",
    }
    calc = (
        f"参照月 {reference_month} 只使用当月粒度。"
        f"揽收量_当月={volume_text}；成本_当月={cost_text}。"
        f"目标月={target}。不使用当周行，不把目标写成周。"
    )
    return NextMonthForecast(
        reference_month=reference_month,
        target_month=target,
        topics=topics,
        input_field_ids=tuple(row.field_id for row in month_rows),
        plan=f"对 {target} 做投入、打法、政策调动和成本优化的测试层测算",
        detailed_calc=calc,
    )


def forecast_next_week(*_args, **_kwargs) -> None:
    raise NextMonthIsNotNextWeek("下个月测算不得写成下个周")
