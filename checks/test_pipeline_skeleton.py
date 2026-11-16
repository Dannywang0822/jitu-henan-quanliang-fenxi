"""经营管理流水线骨架不变量。合成数，不碰已交三张汇总。"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from access_control.accounts import AccountDirectory
from access_control.approvals import ApprovalBook, ApprovalRecord, authorize_promotion, auto_promote
from ingest.dictionary import ConsistencyReport, load_dictionary, require_exact, verify_exact
from ingest.upload import UploadFile, submit_upload
from kernel.dates import DifferentAsOfCannotBeSameDay, as_same_day
from kernel.isolation import list_non_placeholder
from kernel.output import INFORMAL_MARK
from kernel.promotion import PromotionDenied
from periods.formal_surfaces import inspect_surface, require_surface
from periods.next_month import NextMonthForecast, forecast_next_month, forecast_next_week
from periods.views import PeriodResult
from pipeline.boundaries import (
    assert_data_not_demand,
    deploy_production,
    open_management_env,
    purchase_cloud_plan,
    write_raw_or_wide_to_cloudbase_document,
)
from pipeline.errors import (
    AutoPromotionForbidden,
    CloudResourceNotOpened,
    DemandEntrySeparated,
    DictionaryNotExact,
    DocumentDatabaseWriteForbidden,
    FormalSurfaceUnavailable,
    LaneRoleMismatch,
    NextMonthIsNotNextWeek,
    OpenRegistrationForbidden,
    PeriodMixError,
    TableTooLarge,
)
from pipeline.walkthrough import load_upload, run_synthetic_walkthrough
from storage.objects import DetailUploadRejected, LocalObjectStore
from warehouse.local_dual import ExplicitPromotion, LocalWarehouse
from warehouse.rows import WideRow


def test_design_records_start_without_cloud(repo_root: Path):
    text = (repo_root / "PIPELINE_DESIGN.md").read_text(encoding="utf-8")
    assert "2026-11-17" in text
    assert "开工" in text
    assert "云资源尚未开通" in text
    assert "家校" in text and "家庭自用" in text
    assert "不单独买 COS" in text
    assert "CloudBase 文档库" in text


def test_synthetic_walkthrough_keeps_formal_layer_empty(repo_root: Path):
    report = run_synthetic_walkthrough(repo_root)
    assert report.informal_mark == INFORMAL_MARK
    assert report.detail_rejected is True
    assert report.detail_stored is False
    assert report.formal_count == 0
    assert report.daily_header == "揽收件数(票)"
    assert report.daily_field_id == "揽收量_当日"
    assert set(report.blocked_file_ids) == {
        "syn-front-partial",
        "syn-front-mismatch",
        "syn-analysis-mismatch",
    }
    assert {row.source_file_id for row in report.wide_rows}.isdisjoint(report.blocked_file_ids)
    assert "syn-detail-001" not in "\n".join(report.storage_keys)
    file_ids = {row.source_file_id for row in report.wide_rows}
    assert file_ids == {
        "syn-front-daily",
        "syn-front-week",
        "syn-front-month",
        "syn-analysis-month",
    }
    departments = {row.department for row in report.wide_rows}
    assert departments == {"营运", "财务"}
    assert all(row.source_file_id and row.department for row in report.wide_rows)
    assert all(row.informal_mark == INFORMAL_MARK and row.layer == "test" for row in report.wide_rows)
    assert {row.value for row in report.linkage.day.rows} == {"100"}
    assert {row.value for row in report.other_day.rows} == {"80"}
    assert {row.value for row in report.linkage.week.rows} == {"180"}
    assert {row.field_id: row.value for row in report.linkage.month.rows} == {
        "揽收量_当月": "400",
        "成本_当月": "50",
    }
    assert report.linkage.day.horizon == "当日"
    assert report.linkage.week.horizon == "当周"
    assert report.linkage.month.horizon == "当月"
    assert report.linkage.informal_mark == INFORMAL_MARK
    assert report.next_month.horizon == "下个月"
    assert report.next_month.reference_month == "2026-11"
    assert report.next_month.target_month == "2026-12"
    assert report.next_month.layer == "test"
    assert set(report.next_month.topics) == {"投入", "打法", "政策调动", "成本优化"}
    assert "下个周" not in report.next_month.detailed_calc
    assert set(report.next_month.input_field_ids) == {"揽收量_当月", "成本_当月"}
    assert len(report.storage_keys) == 7
    assert {view.name: view.status for view in report.surfaces} == {
        "周运营台": "不可用",
        "决策逻辑": "不可用",
        "历史对比": "不可用",
    }
    assert {row.as_of for row in report.wide_rows}.isdisjoint({"2026-11-08", "2026-11-12"})
    assert list_non_placeholder(repo_root / "formal_layer") == []
    assert list_non_placeholder(repo_root / "dictionary" / "formal") == []


def test_detail_values_are_not_stored(repo_root: Path):
    payload = json.loads((repo_root / "storage" / "fixtures" / "detail_rejected.json").read_text(encoding="utf-8"))
    payload["rows"] = [{"as_of": "2026-11-02", "values": {"运单号": "SENTINEL_DETAIL_VALUE"}}]
    upload = UploadFile.model_validate(payload)
    directory, store, warehouse, dictionary = _runtime(repo_root)
    with pytest.raises(DetailUploadRejected) as caught:
        submit_upload(upload, directory=directory, store=store, warehouse=warehouse, dictionary=dictionary)
    assert "SENTINEL_DETAIL_VALUE" not in str(caught.value)
    assert store.keys() == ()
    assert warehouse.stored_values() == ()
    assert "SENTINEL_DETAIL_VALUE" not in store.body_text()


def test_inconsistent_header_cannot_enter_wide_table(repo_root: Path):
    directory, store, warehouse, dictionary = _runtime(repo_root)
    upload = load_upload(repo_root / "storage" / "fixtures" / "frontline_mismatch.json")
    outcome = submit_upload(
        upload, directory=directory, store=store, warehouse=warehouse, dictionary=dictionary
    )
    assert outcome.stored is True
    assert outcome.fully_consistent is False
    assert outcome.wide_rows == ()
    assert warehouse.test_count() == 0
    report = verify_exact(upload.columns, dictionary, department=upload.department)
    with pytest.raises(DictionaryNotExact):
        require_exact(report)


def test_partial_match_is_not_exact(repo_root: Path):
    dictionary = load_dictionary(repo_root / "storage" / "fixtures" / "synthetic_dictionary.json")
    upload = load_upload(repo_root / "storage" / "fixtures" / "frontline_partial.json")
    report = verify_exact(upload.columns, dictionary, department=upload.department)
    assert report.fully_consistent is False
    assert any(item.status == "已映射" for item in report.recognition)
    assert any(item.status == "待复核" and item.header == "随手备注" for item in report.recognition)
    with pytest.raises((DictionaryNotExact, ValidationError)):
        ConsistencyReport(
            fully_consistent=True,
            bindings=(("揽收件数(票)", "揽收量_当日"),),
            mismatches=("随手备注: 与字典不完全一致",),
            recognition=report.recognition,
        )


def test_wrong_lane_and_open_registration_rejected(repo_root: Path):
    directory = AccountDirectory()
    directory.open_designated(account_id="acct-front-ops", role="基层上传", department="营运")
    directory.open_designated(account_id="acct-analysis-fin", role="经营分析", department="财务")
    with pytest.raises(OpenRegistrationForbidden):
        directory.register(account_id="stranger")
    with pytest.raises(OpenRegistrationForbidden):
        directory.open_designated(account_id="acct-public", role="主管", department="市场", opened_by="自行注册")
    with pytest.raises(OpenRegistrationForbidden):
        directory.require("nobody")
    store = LocalObjectStore()
    warehouse = LocalWarehouse.open_memory()
    dictionary = load_dictionary(repo_root / "storage" / "fixtures" / "synthetic_dictionary.json")
    daily = load_upload(repo_root / "storage" / "fixtures" / "frontline_daily.json")
    swapped = daily.model_copy(update={"uploader_account_id": "acct-analysis-fin"})
    with pytest.raises(LaneRoleMismatch):
        submit_upload(swapped, directory=directory, store=store, warehouse=warehouse, dictionary=dictionary)
    assert warehouse.test_count() == 0


def test_no_auto_promotion_and_formal_surfaces_refuse(repo_root: Path):
    warehouse = LocalWarehouse.open_memory()
    row = _sample_row("pkg-row")
    warehouse.insert_test_rows([row])
    book = ApprovalBook()
    request_id = book.submit(kind="整包晋升", subject_id="pkg-1", requested_by="acct-hub")
    record = book.decide(request_id, approved=True, decided_by="Danny")
    assert warehouse.formal_count() == 0
    with pytest.raises(AutoPromotionForbidden):
        warehouse.promote([row], record)  # type: ignore[arg-type]
    with pytest.raises(AutoPromotionForbidden):
        warehouse.auto_promote([row])
    with pytest.raises(AutoPromotionForbidden):
        auto_promote(warehouse, record)
    with pytest.raises(AutoPromotionForbidden):
        warehouse.insert_formal_directly([row])
    with pytest.raises((TypeError, AutoPromotionForbidden)):
        ExplicitPromotion("pkg-1")
    with pytest.raises(AutoPromotionForbidden):
        ExplicitPromotion("pkg-1", object())
    permit = authorize_promotion(record)
    assert isinstance(permit, ExplicitPromotion)
    warehouse.promote([row], permit)
    assert warehouse.formal_count() == 1
    assert warehouse.test_count() == 1
    warehouse.rollback()
    assert warehouse.formal_count() == 0
    denied = book.decide(request_id, approved=False, decided_by="Danny")
    with pytest.raises(PromotionDenied):
        authorize_promotion(denied)
    for name in ("周运营台", "决策逻辑", "历史对比"):
        view = inspect_surface(name, 0)
        assert view.status == "不可用"
        with pytest.raises(FormalSurfaceUnavailable):
            require_surface(name, 0)
    assert list_non_placeholder(repo_root / "formal_layer") == []


def test_periods_do_not_mix_and_next_month_is_not_next_week():
    day = _sample_row("day-row", as_of="2026-11-02")
    other = _sample_row("other-row", as_of="2026-11-03", value="80")
    with pytest.raises((PeriodMixError, ValidationError)) as mixed:
        PeriodResult(
            grain="day",
            period_key="2026-11-02",
            horizon="当日",
            rows=(day, other),
            plan="只看一天",
            detailed_calc="两天不能合成当日",
        )
    assert "不得串期" in str(mixed.value)
    with pytest.raises(NextMonthIsNotNextWeek):
        forecast_next_week(reference="2026-11")
    with pytest.raises((NextMonthIsNotNextWeek, ValidationError)):
        NextMonthForecast(
            reference_month="2026-11",
            target_month="2026-W46",
            topics={"投入": "a", "打法": "b", "政策调动": "c", "成本优化": "d"},
            input_field_ids=(),
            plan="错误地写成周",
            detailed_calc="目标不是下个月",
        )
    forecast = forecast_next_month((day,), "2026-11")
    assert forecast.target_month == "2026-12"
    assert forecast.informal_mark == INFORMAL_MARK
    assert "下周" not in forecast.plan


def test_november_8_and_12_are_not_the_same_day():
    with pytest.raises(DifferentAsOfCannotBeSameDay):
        as_same_day(
            {"report_id": "pnl", "as_of": "2026-11-08"},
            {"report_id": "core", "as_of": "2026-11-12"},
        )


def test_wide_row_requires_source_file_and_department():
    with pytest.raises(ValidationError):
        WideRow(
            row_id="x",
            source_file_id="",
            department="营运",
            field_id="揽收量_当日",
            value="1",
            unit="票",
            caliber="当日",
            as_of="2026-11-02",
            period_grain="day",
            period_key="2026-11-02",
            source_type="假设",
        )
    payload = _sample_row("bad").model_dump()
    payload["layer"] = "formal"
    with pytest.raises(ValidationError):
        WideRow.model_validate(payload)


def test_cloud_and_demand_boundaries_refuse():
    with pytest.raises(DocumentDatabaseWriteForbidden):
        write_raw_or_wide_to_cloudbase_document([{"a": 1}])
    with pytest.raises(CloudResourceNotOpened):
        open_management_env("经营管理")
    with pytest.raises(CloudResourceNotOpened):
        purchase_cloud_plan("postgres")
    with pytest.raises(CloudResourceNotOpened):
        deploy_production()
    with pytest.raises(DemandEntrySeparated):
        assert_data_not_demand("提需求", "功能易用性")
    with pytest.raises(ValidationError):
        ApprovalRecord(
            request_id="x",
            kind="整包晋升",
            subject_id="pkg",
            approved=True,
            decided_by="Danny",
            auto=True,  # type: ignore[arg-type]
        )


def test_postgres_schema_is_design_only(repo_root: Path):
    sql = (repo_root / "warehouse" / "schema_postgres.sql").read_text(encoding="utf-8")
    assert "CREATE SCHEMA IF NOT EXISTS mgmt_test" in sql
    assert "CREATE SCHEMA IF NOT EXISTS mgmt_formal" in sql
    assert "source_file_id TEXT NOT NULL" in sql
    assert "department TEXT NOT NULL" in sql
    assert "测试，非正式" in sql
    assert "https://" not in sql
    warehouse = LocalWarehouse.open_memory(repo_root / "warehouse" / "schema_sqlite.sql")
    assert warehouse.backend == "sqlite-memory"
    assert warehouse.formal_count() == 0


def test_table_stays_small():
    warehouse = LocalWarehouse.open_memory()
    rows = [_sample_row(f"bulk-{index}", file_id=f"file-{index}") for index in range(33)]
    with pytest.raises(TableTooLarge):
        warehouse.insert_test_rows(rows)


def test_new_code_does_not_import_cloud_sdks(repo_root: Path):
    pattern = re.compile(r"^\s*(import|from)\s+(lark|qcloud|boto3|psycopg|tencentcloud|requests)\b", re.M)
    roots = ("storage", "warehouse", "ingest", "parse", "periods", "pipeline", "access_control")
    for name in roots:
        for path in (repo_root / name).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert pattern.search(text) is None, path


def _runtime(repo_root: Path):
    directory = AccountDirectory()
    directory.open_designated(account_id="acct-front-ops", role="基层上传", department="营运")
    directory.open_designated(account_id="acct-analysis-fin", role="经营分析", department="财务")
    return (
        directory,
        LocalObjectStore(),
        LocalWarehouse.open_memory(),
        load_dictionary(repo_root / "storage" / "fixtures" / "synthetic_dictionary.json"),
    )


def _sample_row(row_id: str, *, as_of: str = "2026-11-02", value: str = "100", file_id: str = "syn-file") -> WideRow:
    return WideRow(
        row_id=row_id,
        source_file_id=file_id,
        department="营运",
        field_id="揽收量_当日",
        value=value,
        unit="票",
        caliber="当日",
        as_of=as_of,
        period_grain="day",
        period_key=as_of,
        source_type="假设",
    )
