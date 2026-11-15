"""检查共用夹具与仓库根路径。"""

from __future__ import annotations

from pathlib import Path

import pytest

from data_interface.ingest import load_fixture


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def staffing(repo_root: Path):
    return load_fixture(repo_root / "fixtures" / "staffing_202510_202610.json")


@pytest.fixture(scope="session")
def core_metrics(repo_root: Path):
    return load_fixture(repo_root / "fixtures" / "core_metrics_2026-11-12.json")


@pytest.fixture(scope="session")
def pnl(repo_root: Path):
    return load_fixture(repo_root / "fixtures" / "pnl_2026-11-08.json")
