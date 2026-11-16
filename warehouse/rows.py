"""宽表行。测试层行必须能表达来源文件、部门和「测试，非正式」。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from kernel.departments import parse_department
from kernel.fields import parse_field_id
from kernel.output import INFORMAL_MARK
from kernel.source import parse_source_type
from pipeline.errors import PeriodMixError
from warehouse.calendar import grain_for_caliber, period_key_for


class WideRow(BaseModel):
    """测试层宽表行。正式层行不能用这个类型构造。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    row_id: str
    layer: Literal["test"] = "test"
    source_file_id: str
    department: str
    field_id: str
    value: str
    unit: str
    caliber: str
    as_of: str
    period_grain: Literal["day", "week", "month"]
    period_key: str
    source_type: str
    informal_mark: Literal["测试，非正式"] = INFORMAL_MARK

    @field_validator("informal_mark")
    @classmethod
    def _mark(cls, value: str) -> str:
        if value != INFORMAL_MARK:
            raise ValueError("测试层宽表必须标明「测试，非正式」")
        return value

    @field_validator("source_file_id")
    @classmethod
    def _file_id(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("宽表行必须带来源文件编号")
        return text

    @field_validator("department", mode="before")
    @classmethod
    def _department(cls, value: str) -> str:
        return parse_department(value).value

    @field_validator("field_id", mode="before")
    @classmethod
    def _field(cls, value: str) -> str:
        return parse_field_id(value)

    @field_validator("source_type", mode="before")
    @classmethod
    def _source(cls, value: str) -> str:
        return parse_source_type(value).value

    @model_validator(mode="after")
    def _period_alignment(self) -> "WideRow":
        if grain_for_caliber(self.caliber) != self.period_grain:
            raise PeriodMixError(f"{self.field_id} 的口径 {self.caliber} 与粒度 {self.period_grain} 不一致")
        expected = period_key_for(self.as_of, self.period_grain)
        if self.period_key != expected:
            raise PeriodMixError(
                f"{self.field_id} 的周期键 {self.period_key} 与 as_of {self.as_of} 不一致，应为 {expected}"
            )
        if not self.value.strip():
            raise ValueError("宽表行必须有值")
        return self
