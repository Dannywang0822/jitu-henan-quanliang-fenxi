"""缺来源类型，或来源不在四类之内，必须失败。"""

import pytest
from pydantic import ValidationError

from data_interface.ingest import ingest_records
from kernel.source import InvalidSourceError, MissingSourceError, SourcedDecimal, SourceType


def _base(**kwargs):
    data = {
        "field_id": "揽收量_当日",
        "value": "666.7",
        "unit": "万票",
        "source_type": "Danny提供的汇总",
        "as_of": "2026-11-12",
        "caliber": "当日",
    }
    data.update(kwargs)
    return data


def test_missing_source_type_on_value():
    with pytest.raises((MissingSourceError, ValidationError)):
        SourcedDecimal(**_base()) if False else SourcedDecimal(
            field_id="揽收量_当日",
            value="666.7",
            unit="万票",
            source_type=None,  # type: ignore[arg-type]
            as_of="2026-11-12",
            caliber="当日",
        )


def test_missing_source_type_on_ingest():
    with pytest.raises(MissingSourceError):
        ingest_records([
            {
                "field_id": "揽收量_当日",
                "value": "666.7",
                "unit": "万票",
                "caliber": "当日",
                "as_of": "2026-11-12",
            }
        ])


def test_invalid_source_type_rejected():
    with pytest.raises((InvalidSourceError, ValidationError)):
        SourcedDecimal(**_base(source_type="公司系统导出"))


def test_four_legal_source_types_accepted():
    for src in SourceType:
        item = SourcedDecimal(**_base(source_type=src.value))
        assert item.source_type is src


def test_legal_fixtures_all_have_danny_source(staffing, core_metrics, pnl):
    for report in (staffing, core_metrics, pnl):
        assert report.source_type == "Danny提供的汇总"
        for metric in report.metrics:
            assert metric.source_type == "Danny提供的汇总"
            metric.to_sourced()  # 可构造
