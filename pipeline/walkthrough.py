"""用合成夹具跑通本地流水线。不写正式层，不读取已交三张汇总的经营数。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from access_control.accounts import AccountDirectory
from ingest.dictionary import load_dictionary
from ingest.upload import UploadFile, submit_upload
from kernel.output import INFORMAL_MARK
from parse.function import handle
from periods.formal_surfaces import SURFACES, SurfaceView, inspect_surface
from periods.next_month import NextMonthForecast, forecast_next_month
from periods.views import LinkageBoard, PeriodResult, present
from storage.objects import DetailUploadRejected, LocalObjectStore
from warehouse.local_dual import LocalWarehouse
from warehouse.rows import WideRow


class WalkthroughReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    informal_mark: Literal["测试，非正式"] = INFORMAL_MARK
    detail_rejected: bool
    detail_stored: bool
    blocked_file_ids: tuple[str, ...]
    wide_rows: tuple[WideRow, ...]
    daily_header: str
    daily_field_id: str
    linkage: LinkageBoard
    other_day: PeriodResult
    next_month: NextMonthForecast
    surfaces: tuple[SurfaceView, ...]
    formal_count: int
    storage_keys: tuple[str, ...]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_upload(path: Path) -> UploadFile:
    return UploadFile.model_validate(json.loads(path.read_text(encoding="utf-8")))


def run_synthetic_walkthrough(root: Path | None = None) -> WalkthroughReport:
    root = root or repo_root()
    fixture_dir = root / "storage" / "fixtures"
    dictionary = load_dictionary(fixture_dir / "synthetic_dictionary.json")
    directory = AccountDirectory()
    directory.open_designated(account_id="acct-front-ops", role="基层上传", department="营运")
    directory.open_designated(account_id="acct-analysis-fin", role="经营分析", department="财务")
    store = LocalObjectStore()
    warehouse = LocalWarehouse.open_memory(root / "warehouse" / "schema_sqlite.sql")

    detail = load_upload(fixture_dir / "detail_rejected.json")
    try:
        submit_upload(detail, directory=directory, store=store, warehouse=warehouse, dictionary=dictionary)
    except DetailUploadRejected:
        detail_rejected = True
    else:
        detail_rejected = False
    detail_stored = any(detail.file_id in key for key in store.keys())

    blocked: list[str] = []
    for name in ("frontline_partial.json", "frontline_mismatch.json", "analysis_mismatch.json"):
        outcome = submit_upload(
            load_upload(fixture_dir / name),
            directory=directory,
            store=store,
            warehouse=warehouse,
            dictionary=dictionary,
        )
        if outcome.fully_consistent or outcome.wide_rows:
            raise RuntimeError(f"{name} 未完全一致，不能进入宽表")
        blocked.append(outcome.file_id)

    daily_payload = json.loads((fixture_dir / "frontline_daily.json").read_text(encoding="utf-8"))
    daily_result = handle(
        {"upload": daily_payload, "entry": "交数"},
        directory=directory,
        store=store,
        warehouse=warehouse,
        dictionary=dictionary,
        context={"local": True},
    )
    if daily_result["informal_mark"] != INFORMAL_MARK or daily_result["wide_row_count"] != 2:
        raise RuntimeError("基层日表应识别后写入两行测试层宽表")
    daily_upload = UploadFile.model_validate(daily_payload)
    daily_outcome = next(
        item
        for item in _recognize_only(daily_upload, dictionary)
        if item.header == "揽收件数(票)"
    )

    for name in ("frontline_week.json", "frontline_month.json", "analysis_month.json"):
        outcome = submit_upload(
            load_upload(fixture_dir / name),
            directory=directory,
            store=store,
            warehouse=warehouse,
            dictionary=dictionary,
        )
        if not outcome.fully_consistent or not outcome.wide_rows:
            raise RuntimeError(f"{name} 应完全一致并进入测试层宽表")
        if any(row.informal_mark != INFORMAL_MARK for row in outcome.wide_rows):
            raise RuntimeError("测试层宽表缺少非正式标记")

    rows = warehouse.test_rows()
    linkage = LinkageBoard(
        day=present(rows, "day", "2026-11-02"),
        week=present(rows, "week", "2026-W45"),
        month=present(rows, "month", "2026-11"),
    )
    other_day = present(rows, "day", "2026-11-03")
    forecast = forecast_next_month(rows, "2026-11")
    surfaces = tuple(inspect_surface(name, warehouse.formal_count()) for name in SURFACES)
    report = WalkthroughReport(
        detail_rejected=detail_rejected,
        detail_stored=detail_stored,
        blocked_file_ids=tuple(blocked),
        wide_rows=rows,
        daily_header=daily_outcome.header,
        daily_field_id=daily_outcome.field_id or "",
        linkage=linkage,
        other_day=other_day,
        next_month=forecast,
        surfaces=surfaces,
        formal_count=warehouse.formal_count(),
        storage_keys=store.keys(),
    )
    warehouse.close()
    return report


def _recognize_only(upload: UploadFile, dictionary):
    from ingest.dictionary import verify_exact

    return verify_exact(upload.columns, dictionary, department=upload.department).recognition
