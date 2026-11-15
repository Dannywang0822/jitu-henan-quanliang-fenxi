"""夹具与上传录入校验。默认只进测试层。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from kernel.dates import parse_as_of
from kernel.departments import Department, parse_department
from kernel.detail import reject_detail_column
from kernel.fields import parse_field_id
from kernel.metrics import canonicalize_capacity, canonicalize_labor
from kernel.pnl import assert_pnl_identity
from kernel.ratios import CumulativeKind, MomType, parse_mom_type
from kernel.source import SourcedDecimal, parse_source_type


class PrintedSuspiciousRate(BaseModel):
    """报表印刷的达成率（可疑），模型不得把它当成正确结论。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    field_id: str
    printed_value: str
    status: str
    actual: str
    budget: str
    recalc_formula: str = "累计/预算"

    @field_validator("status")
    @classmethod
    def _status(cls, v: str) -> str:
        if "可疑" not in v:
            raise ValueError("印刷达成率必须标明可疑，不得当作正确结论")
        return v


class FixtureMetric(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    field_id: str
    standard_name: str
    value: str
    unit: str
    caliber: str
    as_of: str
    source_type: str
    role: str = "数据"
    department: str | None = None
    mom_type: str | None = None
    mom_value: str | None = None
    mom_unit: str | None = None
    note: str | None = None
    target: str | None = None
    target_unit: str | None = None
    october_value: str | None = None
    budget: str | None = None

    @field_validator("field_id", mode="before")
    @classmethod
    def _fid(cls, v: Any) -> str:
        return parse_field_id(v)

    @field_validator("source_type", mode="before")
    @classmethod
    def _src(cls, v: Any) -> str:
        return parse_source_type(v).value

    @field_validator("as_of", mode="before")
    @classmethod
    def _as_of(cls, v: Any) -> str:
        return parse_as_of(v)

    def to_sourced(self) -> SourcedDecimal:
        return SourcedDecimal(
            field_id=self.field_id,
            value=self.value,
            unit=self.unit,
            source_type=self.source_type,
            as_of=self.as_of,
            caliber=self.caliber,
            note=self.note,
        )


class FixtureReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    report_id: str
    title: str
    as_of: str | None = None
    period_from: str | None = None
    period_to: str | None = None
    source_type: str
    default_mom_type: str | None = None
    has_owner_name_column: bool = False
    owner_name_used_as_primary_key: bool = False
    owner_name_note: str | None = None
    notes: tuple[str, ...] = ()
    metrics: tuple[FixtureMetric, ...]
    printed_suspicious: tuple[PrintedSuspiciousRate, ...] = ()
    identity: dict[str, str] | None = None

    @field_validator("source_type", mode="before")
    @classmethod
    def _src(cls, v: Any) -> str:
        return parse_source_type(v).value

    @field_validator("default_mom_type", mode="before")
    @classmethod
    def _mom(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return parse_mom_type(v).value

    @model_validator(mode="after")
    def _invariants(self) -> "FixtureReport":
        if self.owner_name_used_as_primary_key:
            raise ValueError("模型不以负责人姓名为主键")
        if self.has_owner_name_column and not self.owner_name_note:
            raise ValueError("表含负责人姓名列时，夹具须注明不以人名为主键")
        if self.as_of is None and not (self.period_from and self.period_to):
            raise ValueError("报表必须有 as_of 或期间口径")
        if self.as_of:
            parse_as_of(self.as_of)
        # 所有指标必须自带 as_of、口径、单位、来源
        as_ofs = set()
        for m in self.metrics:
            if m.source_type != self.source_type and m.source_type not in {s.value for s in __import__("kernel.source", fromlist=["SourceType"]).SourceType}:
                raise ValueError("来源类型非法")
            if self.as_of and m.as_of != self.as_of:
                # 允许 T-1 等对照行，但必须在口径或 note 里说明不同日期
                if "T-1" not in (m.caliber or "") and (not m.note or "不同" not in m.note and "T-1" not in m.note and m.as_of not in (m.caliber or "")):
                    raise ValueError(
                        f"{m.field_id} 的 as_of={m.as_of} 与报表 as_of={self.as_of} 不同，必须在口径或备注标明"
                    )
            as_ofs.add(m.as_of)
        if self.identity:
            assert_pnl_identity(
                revenue=self.identity.get("收入累计"),
                cost=self.identity.get("成本累计"),
                expense=self.identity.get("费用累计"),
                gross_profit=self.identity.get("毛利累计"),
                net_profit=self.identity.get("累计净利"),
            )
        return self

    def metric_map(self) -> dict[str, FixtureMetric]:
        return {m.field_id: m for m in self.metrics}

    def get(self, field_id: str) -> FixtureMetric:
        return self.metric_map()[field_id]


def load_fixture(path: Path | str) -> FixtureReport:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    # 明细列在入库前拒绝
    for col in data.get("rejected_detail_columns", []):
        reject_detail_column(col)
    for metric in data.get("metrics", []):
        reject_detail_column(metric.get("field_id", ""))
        # 规范化易混字段
        rid = data.get("report_id", "")
        fid = metric.get("field_id", "")
        if "单公斤运力" in fid:
            metric["field_id"] = canonicalize_capacity(fid, rid)
        elif "人力" in fid and ("票" in fid or "操作" in fid or "考核" in fid):
            metric["field_id"] = canonicalize_labor(fid, rid)
    return FixtureReport.model_validate(data)


def ingest_records(records: list[dict[str, Any]], *, default_report_id: str = "adhoc") -> list[SourcedDecimal]:
    """通用录入：缺来源、明细列、非法主键当场拒绝。"""
    out: list[SourcedDecimal] = []
    for raw in records:
        reject_detail_column(str(raw.get("field_id", raw.get("column", ""))))
        if "source_type" not in raw or raw.get("source_type") in (None, ""):
            from kernel.source import MissingSourceError
            raise MissingSourceError("每个数字必须带来源类型")
        parsed = FixtureMetric.model_validate(
            {
                "field_id": raw["field_id"],
                "standard_name": raw.get("standard_name", raw["field_id"]),
                "value": raw["value"],
                "unit": raw["unit"],
                "caliber": raw["caliber"],
                "as_of": raw["as_of"],
                "source_type": raw["source_type"],
                "note": raw.get("note"),
            }
        )
        out.append(parsed.to_sourced())
    return out
