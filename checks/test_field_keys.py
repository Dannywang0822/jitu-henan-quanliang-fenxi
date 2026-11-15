"""字段主键是字段标识，不以负责人姓名做主键。"""

import pytest

from kernel.fields import FieldId, PersonNameAsPrimaryKeyError, parse_field_id


def test_person_name_as_primary_key_rejected():
    with pytest.raises(PersonNameAsPrimaryKeyError):
        parse_field_id("负责人")
    with pytest.raises(PersonNameAsPrimaryKeyError):
        parse_field_id("姓名")
    with pytest.raises(PersonNameAsPrimaryKeyError):
        parse_field_id("负责人姓名")
    with pytest.raises(PersonNameAsPrimaryKeyError):
        FieldId("示例姓名")


def test_metric_field_ids_accepted(core_metrics):
    for metric in core_metrics.metrics:
        assert parse_field_id(metric.field_id) == metric.field_id


def test_fixture_notes_owner_column_but_not_as_key(core_metrics):
    assert core_metrics.has_owner_name_column is True
    assert core_metrics.owner_name_used_as_primary_key is False
    assert "不以人名为主键" in (core_metrics.owner_name_note or "")
    keys = {m.field_id for m in core_metrics.metrics}
    assert "负责人" not in keys
    assert "姓名" not in keys
