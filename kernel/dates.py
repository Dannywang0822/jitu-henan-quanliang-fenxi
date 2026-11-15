"""不同 as_of 日期的报表不得合成「同一天」记录。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class DifferentAsOfCannotBeSameDay(ValueError):
    """试图把不同 as_of 的报表当成同一天。"""


def parse_as_of(raw: Any) -> str:
    if raw is None or str(raw).strip() == "":
        raise ValueError("记录必须带 as_of 日期或期间口径")
    text = str(raw).strip()
    # 允许完整日期，或编制对照用的 YYYYMM 期间。
    if re_full_date(text):
        return text
    if re_period(text):
        return text
    raise ValueError(f"无法识别的 as_of: {text!r}")


def re_full_date(text: str) -> bool:
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def re_period(text: str) -> bool:
    if len(text) == 6 and text.isdigit():
        month = int(text[4:6])
        return 1 <= month <= 12
    return False


def as_of_to_date(raw: str) -> date | None:
    if re_full_date(raw):
        return datetime.strptime(raw, "%Y-%m-%d").date()
    return None


class AsOf(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    value: str

    @field_validator("value", mode="before")
    @classmethod
    def _parse(cls, v: Any) -> str:
        return parse_as_of(v)


class DatedReport(BaseModel):
    """带单一 as_of 的报表容器。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    report_id: str
    as_of: str
    title: str | None = None

    @field_validator("as_of", mode="before")
    @classmethod
    def _as_of(cls, v: Any) -> str:
        return parse_as_of(v)


def as_same_day(*reports: DatedReport | Mapping[str, Any]) -> str:
    """仅当全部 as_of 相同才允许称为同一天，并返回该日期。"""
    parsed: list[DatedReport] = []
    for item in reports:
        if isinstance(item, DatedReport):
            parsed.append(item)
        else:
            parsed.append(DatedReport.model_validate(item))
    if not parsed:
        raise ValueError("没有可合成的报表")
    dates = {r.as_of for r in parsed}
    if len(dates) != 1:
        ids = ", ".join(f"{r.report_id}@{r.as_of}" for r in parsed)
        raise DifferentAsOfCannotBeSameDay(
            f"不同 as_of 日期的报表不得合成同一天记录: {ids}"
        )
    return parsed[0].as_of


class CrossDateContrast(BaseModel):
    """允许对照不同 as_of 的报表，但必须标明不是同一天。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    reports: tuple[DatedReport, ...]
    note: str

    @model_validator(mode="after")
    def _must_label_if_different(self) -> "CrossDateContrast":
        dates = {r.as_of for r in self.reports}
        if len(dates) > 1:
            if "同一天" in self.note and "不是" not in self.note and "不得" not in self.note and "不同" not in self.note:
                raise DifferentAsOfCannotBeSameDay(
                    "对照说明不能把不同 as_of 说成同一天"
                )
            if "不同" not in self.note and "不是同一天" not in self.note:
                raise DifferentAsOfCannotBeSameDay(
                    "跨日对照必须标明不同 as_of，不得当作同一天"
                )
        return self

    @property
    def is_same_day(self) -> bool:
        return len({r.as_of for r in self.reports}) == 1


def collect_as_ofs(items: Iterable[Mapping[str, Any] | DatedReport]) -> set[str]:
    result: set[str] = set()
    for item in items:
        if isinstance(item, DatedReport):
            result.add(item.as_of)
        else:
            result.add(parse_as_of(item["as_of"]))
    return result
