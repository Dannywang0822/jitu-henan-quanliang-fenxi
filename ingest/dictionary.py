"""字段字典门禁：不完全一致不得入宽表。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from kernel.departments import parse_department
from kernel.detail import is_detail_column
from kernel.fields import parse_field_id
from pipeline.errors import DictionaryNotExact
from warehouse.calendar import grain_for_caliber


class DictField(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    field_id: str
    standard_name: str
    aliases: tuple[str, ...] = ()
    unit: str
    caliber: Literal["当日", "当周", "当月"]
    grain: Literal["day", "week", "month"]
    department: str
    value_type: Literal["数值"] = "数值"
    role: Literal["数据"] = "数据"
    status: Literal["测试层种子"] = "测试层种子"

    @field_validator("field_id", mode="before")
    @classmethod
    def _field(cls, value: str) -> str:
        return parse_field_id(value)

    @field_validator("department", mode="before")
    @classmethod
    def _department(cls, value: str) -> str:
        return parse_department(value).value

    @model_validator(mode="after")
    def _grain(self) -> "DictField":
        if grain_for_caliber(self.caliber) != self.grain:
            raise ValueError(f"{self.field_id} 的口径和粒度不一致")
        names = (self.field_id, self.standard_name, *self.aliases)
        if any(is_detail_column(name) for name in names):
            raise ValueError(f"字典种子不能收录明细列: {self.field_id}")
        return self

    def names(self) -> set[str]:
        return {self.field_id, self.standard_name, *self.aliases}


class ColumnSpec(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    header: str
    unit: str
    caliber: str


class RecognitionItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    header: str
    status: Literal["已映射", "待复核", "拒绝"]
    field_id: str | None = None
    reason: str


class ConsistencyReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    fully_consistent: bool
    bindings: tuple[tuple[str, str], ...]
    mismatches: tuple[str, ...]
    recognition: tuple[RecognitionItem, ...]

    @model_validator(mode="after")
    def _exact_flag(self) -> "ConsistencyReport":
        if self.fully_consistent and (self.mismatches or not self.bindings):
            raise DictionaryNotExact("不完全一致不能标成验证通过")
        mapped = [item for item in self.recognition if item.status == "已映射"]
        if self.fully_consistent and len(mapped) != len(self.recognition):
            raise DictionaryNotExact("存在未映射或被拒列时不能标成验证通过")
        return self


def load_dictionary(path: Path) -> tuple[DictField, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return tuple(DictField.model_validate(item) for item in payload["fields"])


def match_column(
    column: ColumnSpec,
    fields: tuple[DictField, ...],
    *,
    department: str | None = None,
) -> DictField | None:
    hits = [
        field
        for field in fields
        if column.header in field.names()
        and column.unit == field.unit
        and column.caliber == field.caliber
        and (department is None or field.department == department)
    ]
    if len(hits) == 1:
        return hits[0]
    return None


def verify_exact(
    columns: tuple[ColumnSpec, ...],
    fields: tuple[DictField, ...],
    *,
    department: str | None = None,
) -> ConsistencyReport:
    recognition: list[RecognitionItem] = []
    bindings: list[tuple[str, str]] = []
    mismatches: list[str] = []
    seen: set[str] = set()
    for column in columns:
        if is_detail_column(column.header):
            recognition.append(
                RecognitionItem(header=column.header, status="拒绝", reason="明细拒收，不入字典")
            )
            mismatches.append(f"{column.header}: 明细拒收")
            continue
        hit = match_column(column, fields, department=department)
        if hit is None:
            recognition.append(
                RecognitionItem(header=column.header, status="待复核", reason="表头、单位或口径与字典不完全一致")
            )
            mismatches.append(f"{column.header}: 与字典不完全一致")
            continue
        if hit.field_id in seen:
            recognition.append(
                RecognitionItem(
                    header=column.header,
                    status="待复核",
                    field_id=hit.field_id,
                    reason="同一字段被重复映射",
                )
            )
            mismatches.append(f"{column.header}: 重复映射到 {hit.field_id}")
            continue
        seen.add(hit.field_id)
        recognition.append(
            RecognitionItem(
                header=column.header,
                status="已映射",
                field_id=hit.field_id,
                reason="标准名或别名、单位、口径完全一致",
            )
        )
        bindings.append((column.header, hit.field_id))
    fully = bool(columns) and not mismatches and len(bindings) == len(columns)
    return ConsistencyReport(
        fully_consistent=fully,
        bindings=tuple(bindings),
        mismatches=tuple(mismatches),
        recognition=tuple(recognition),
    )


def require_exact(report: ConsistencyReport) -> None:
    if not report.fully_consistent:
        detail = "；".join(report.mismatches) or "没有可写入的列"
        raise DictionaryNotExact(f"字段字典验证未完全一致，不得写入宽表: {detail}")
