"""云边界与需求入口。这些函数只拒绝，不发起网络调用。"""

from __future__ import annotations

from pipeline.errors import (
    CloudResourceNotOpened,
    DemandEntrySeparated,
    DocumentDatabaseWriteForbidden,
)

DEMAND_TYPES = frozenset({"功能易用性", "扩展需求"})


def write_raw_or_wide_to_cloudbase_document(*_args, **_kwargs) -> None:
    raise DocumentDatabaseWriteForbidden("原始表和宽表不得写入 CloudBase 文档库")


def open_management_env(*_args, **_kwargs) -> None:
    raise CloudResourceNotOpened(
        "经营管理 CloudBase 环境只写在设计中，与家校、家庭自用隔离，本骨架不开通"
    )


def purchase_cloud_plan(*_args, **_kwargs) -> None:
    raise CloudResourceNotOpened("不购买任何云套餐")


def deploy_production(*_args, **_kwargs) -> None:
    raise CloudResourceNotOpened("不实施上线，不改现网，不部署")


def assert_data_not_demand(entry: str | None, demand_type: str | None = None) -> None:
    if entry == "提需求" or demand_type in DEMAND_TYPES:
        raise DemandEntrySeparated("提需求入口保留在 change_requests，不并进交数流水线")
