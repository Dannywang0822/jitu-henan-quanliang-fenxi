"""解析入口按云函数形态设计：一次调用进、一次调用出。不部署，不代替已开通的服务器。"""

from __future__ import annotations

from access_control.accounts import AccountDirectory
from ingest.dictionary import DictField
from ingest.upload import UploadFile, UploadOutcome, submit_upload
from pipeline.boundaries import assert_data_not_demand
from pipeline.errors import CloudResourceNotOpened
from storage.objects import LocalObjectStore
from warehouse.local_dual import LocalWarehouse


def handle(
    event: dict,
    *,
    directory: AccountDirectory,
    store: LocalObjectStore,
    warehouse: LocalWarehouse,
    dictionary: tuple[DictField, ...],
    context: dict | None = None,
) -> dict:
    if event.get("deploy") or event.get("purchase"):
        raise CloudResourceNotOpened("解析函数不购买套餐，也不在云上部署")
    if context not in (None, {"local": True}):
        raise CloudResourceNotOpened("解析入口只在本地骨架运行")
    assert_data_not_demand(event.get("entry"), event.get("类型"))
    upload = UploadFile.model_validate(event["upload"])
    outcome: UploadOutcome = submit_upload(
        upload,
        directory=directory,
        store=store,
        warehouse=warehouse,
        dictionary=dictionary,
        entry=event.get("entry"),
        demand_type=event.get("类型"),
    )
    return {
        "informal_mark": outcome.informal_mark,
        "file_id": outcome.file_id,
        "stored": outcome.stored,
        "fully_consistent": outcome.fully_consistent,
        "wide_row_count": len(outcome.wide_rows),
        "source_file_ids": sorted({row.source_file_id for row in outcome.wide_rows}),
        "departments": sorted({row.department for row in outcome.wide_rows}),
    }
