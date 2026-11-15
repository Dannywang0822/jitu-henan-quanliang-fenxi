"""来源类型不变量：每个数字必须带来源，且只允许四类。"""

from __future__ import annotations

from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MissingSourceError(ValueError):
    """缺来源类型。"""


class InvalidSourceError(ValueError):
    """来源类型不在允许的四类之内。"""


class SourceType(str, Enum):
    """只允许这四类来源。"""

    假设 = "假设"
    公开来源 = "公开来源"
    合规授权汇总 = "合规授权汇总"
    Danny提供的汇总 = "Danny提供的汇总"


def parse_source_type(raw: Any) -> SourceType:
    if raw is None or raw == "":
        raise MissingSourceError("每个数字必须带来源类型")
    if isinstance(raw, SourceType):
        return raw
    if not isinstance(raw, str):
        raise InvalidSourceError(f"来源类型不在四类之内: {raw!r}")
    try:
        return SourceType(raw)
    except ValueError as exc:
        raise InvalidSourceError(f"来源类型不在四类之内: {raw!r}") from exc


class SourcedDecimal(BaseModel):
    """带齐来源与口径的数值。缺来源或非法来源无法构造。"""

    model_config = ConfigDict(frozen=True, extra="forbid")

    field_id: str
    value: Decimal
    unit: str
    source_type: SourceType
    as_of: str | None = None
    caliber: str
    note: str | None = None

    @field_validator("source_type", mode="before")
    @classmethod
    def _require_source(cls, v: Any) -> SourceType:
        return parse_source_type(v)

    @field_validator("value", mode="before")
    @classmethod
    def _as_decimal(cls, v: Any) -> Decimal:
        if isinstance(v, Decimal):
            return v
        if isinstance(v, bool) or v is None:
            raise ValueError("数值不能为空或布尔值")
        return Decimal(str(v))

    @field_validator("field_id")
    @classmethod
    def _field_id_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("字段标识不能为空")
        return str(v)

    @model_validator(mode="after")
    def _caliber_present(self) -> "SourcedDecimal":
        if not self.caliber or not self.caliber.strip():
            raise ValueError(f"字段 {self.field_id} 缺少口径")
        if not self.unit or not str(self.unit).strip():
            raise ValueError(f"字段 {self.field_id} 缺少单位")
        return self
