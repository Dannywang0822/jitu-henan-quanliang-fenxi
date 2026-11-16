"""两路上传。明细拒收；不完全一致只留在对象存储，不进宽表。"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from access_control.accounts import LANE_ROLE, AccountDirectory
from ingest.dictionary import (
    ColumnSpec,
    ConsistencyReport,
    DictField,
    RecognitionItem,
    require_exact,
    verify_exact,
)
from kernel.departments import parse_department
from kernel.detail import is_detail_column
from kernel.output import INFORMAL_MARK
from kernel.source import parse_source_type
from parse.wide_table import build_wide_rows
from pipeline.boundaries import assert_data_not_demand
from pipeline.errors import LaneRoleMismatch
from storage.objects import DetailUploadRejected, LocalObjectStore
from warehouse.local_dual import LocalWarehouse
from warehouse.rows import WideRow


class DataRow(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    as_of: str
    values: dict[str, str]

    @field_validator("values", mode="before")
    @classmethod
    def _text(cls, value: dict) -> dict[str, str]:
        return {str(key): str(item) for key, item in value.items()}


class UploadFile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    file_id: str
    lane: Literal["基层原始底表", "经营分析组汇总表"]
    department: str
    source_type: str
    uploader_account_id: str
    columns: tuple[ColumnSpec, ...]
    rows: tuple[DataRow, ...] = ()

    @field_validator("department", mode="before")
    @classmethod
    def _department(cls, value: str) -> str:
        return parse_department(value).value

    @field_validator("source_type", mode="before")
    @classmethod
    def _source(cls, value: str) -> str:
        return parse_source_type(value).value

    @field_validator("file_id")
    @classmethod
    def _file_id(cls, value: str) -> str:
        text = value.strip()
        if not text or "/" in text or "\\" in text:
            raise ValueError("来源文件编号必须是不含路径的编号")
        return text


class UploadOutcome(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    file_id: str
    lane: str
    stored: bool
    storage_key: str | None
    wide_rows: tuple[WideRow, ...]
    fully_consistent: bool
    recognition: tuple[RecognitionItem, ...] = ()
    informal_mark: Literal["测试，非正式"] = INFORMAL_MARK
    rejected_reason: str | None = None


def headers_of(upload: UploadFile) -> list[str]:
    names = [column.header for column in upload.columns]
    for row in upload.rows:
        names.extend(row.values.keys())
    return names


def submit_upload(
    upload: UploadFile,
    *,
    directory: AccountDirectory,
    store: LocalObjectStore,
    warehouse: LocalWarehouse,
    dictionary: tuple[DictField, ...],
    entry: str | None = None,
    demand_type: str | None = None,
) -> UploadOutcome:
    assert_data_not_demand(entry, demand_type)
    account = directory.require(upload.uploader_account_id)
    if account.role != LANE_ROLE[upload.lane]:
        raise LaneRoleMismatch(f"{upload.lane} 只能由{LANE_ROLE[upload.lane].value}账号上传")
    if account.department != upload.department:
        raise LaneRoleMismatch("上传部门必须与指定开通账号的部门一致")
    headers = headers_of(upload)
    detail_headers = [name for name in headers if is_detail_column(name)]
    if detail_headers:
        raise DetailUploadRejected(f"明细一律拒收，不落存: {', '.join(dict.fromkeys(detail_headers))}")

    report: ConsistencyReport = verify_exact(upload.columns, dictionary, department=upload.department)
    body = json.dumps(upload.model_dump(), ensure_ascii=False).encode("utf-8")
    stored = store.put_summary(
        file_id=upload.file_id,
        lane=upload.lane,
        department=upload.department,
        source_type=upload.source_type,
        headers=headers,
        body=body,
    )
    if not report.fully_consistent:
        store.mark(stored.key, "字典不一致")
        return UploadOutcome(
            file_id=upload.file_id,
            lane=upload.lane,
            stored=True,
            storage_key=stored.key,
            wide_rows=(),
            fully_consistent=False,
            recognition=report.recognition,
            rejected_reason="字段字典验证未完全一致",
        )
    require_exact(report)
    rows = build_wide_rows(upload, dictionary, report)
    warehouse.insert_test_rows(rows)
    store.mark(stored.key, "已入测试层宽表")
    return UploadOutcome(
        file_id=upload.file_id,
        lane=upload.lane,
        stored=True,
        storage_key=stored.key,
        wide_rows=tuple(rows),
        fully_consistent=True,
        recognition=report.recognition,
    )
