"""禁止合并两种单票人力，禁止跨表自动合并单公斤运力。"""

import pytest

from kernel.metrics import (
    CAPACITY_PER_KG_CORE,
    CAPACITY_PER_KG_PNL,
    LABOR_COST_ASSESSMENT,
    LABOR_COST_OPS,
    FieldMergeForbidden,
    auto_merge,
    canonicalize_capacity,
    forbid_merge,
)


def test_cannot_merge_two_labor_cost_fields():
    with pytest.raises(FieldMergeForbidden):
        forbid_merge(LABOR_COST_ASSESSMENT, LABOR_COST_OPS)
    with pytest.raises(FieldMergeForbidden):
        auto_merge([LABOR_COST_ASSESSMENT, LABOR_COST_OPS])


def test_cannot_auto_merge_capacity_across_reports():
    with pytest.raises(FieldMergeForbidden):
        forbid_merge(CAPACITY_PER_KG_CORE, CAPACITY_PER_KG_PNL)
    with pytest.raises(FieldMergeForbidden):
        auto_merge([CAPACITY_PER_KG_CORE, CAPACITY_PER_KG_PNL])
    with pytest.raises(FieldMergeForbidden):
        canonicalize_capacity("单公斤运力", "unknown_report")


def test_capacity_canonical_names_depend_on_report():
    assert canonicalize_capacity("单公斤运力", "core_metrics") == CAPACITY_PER_KG_CORE
    assert canonicalize_capacity("单公斤运力", "pnl_daily") == CAPACITY_PER_KG_PNL


def test_legal_fixtures_keep_fields_separate(core_metrics, pnl):
    core_ids = {m.field_id for m in core_metrics.metrics}
    pnl_ids = {m.field_id for m in pnl.metrics}
    assert any(LABOR_COST_ASSESSMENT in i for i in core_ids)
    assert any(LABOR_COST_OPS in i or i == LABOR_COST_OPS or i.startswith("单票操作人力成本") for i in pnl_ids)
    assert any("单公斤运力_核心指标" in i for i in core_ids)
    assert any("单公斤运力_损益日报" in i for i in pnl_ids)
    # 不存在一个合并后的字段
    assert "单公斤运力" not in core_ids
    assert "单公斤运力" not in pnl_ids
    assert "单票人力" not in pnl_ids
