"""输出缺方案、缺详细测算，或两层内容对不上，不能作为完整呈报。"""

import pytest
from pydantic import ValidationError

from kernel.departments import ALL_DEPARTMENTS, Department
from kernel.output import (
    CalculationLine,
    DepartmentLayer,
    IncompleteReportError,
    INFORMAL_MARK,
    LayerContent,
    TwoLayerReport,
)


def _line(field_id="累计净利", result="411万元") -> CalculationLine:
    return CalculationLine(
        field_id=field_id,
        description="测算",
        formula="见夹具",
        inputs=(field_id,),
        result=result,
        unit="万元",
        source_type="Danny提供的汇总",
        as_of="2026-11-08",
        caliber="月累计",
    )


def _layer(title: str, plan: str, lines=None, missing=()) -> LayerContent:
    return LayerContent(
        title=title,
        plan=plan,
        detailed_calc=tuple(lines or [_line()]),
        missing=tuple(missing),
        informal_mark=INFORMAL_MARK,
    )


def _dept_layers(supports=("件量不慢",)):
    layers = []
    for dept in ALL_DEPARTMENTS:
        status = "缺数" if dept not in {Department.财务, Department.市场, Department.营运, Department.质控, Department.云仓, Department.人资行政} else "有分析"
        layers.append(
            DepartmentLayer(
                department=dept,
                content=_layer(
                    f"{dept.value}重点关注目标",
                    f"【测试，非正式】本部门本轮{'缺数，待补' if status=='缺数' else '关注已测算缺口'}。",
                ),
                status=status if status != "有分析" else "有分析",
                supports_overall=supports,
            )
        )
    return tuple(layers)


def test_missing_plan_rejected():
    with pytest.raises((IncompleteReportError, Exception)):
        LayerContent(title="整体", plan="  ", detailed_calc=(_line(),), informal_mark=INFORMAL_MARK)


def test_missing_detailed_calc_rejected():
    with pytest.raises((IncompleteReportError, Exception)):
        LayerContent(title="整体", plan="有方案", detailed_calc=(), informal_mark=INFORMAL_MARK)


def test_missing_department_layer_rejected():
    layers = list(_dept_layers())[:-1]
    with pytest.raises((IncompleteReportError, ValidationError)):
        TwoLayerReport(
            overall=_layer("整体结论", "【测试，非正式】件量不慢。"),
            departments=tuple(layers),
            used_as_of=("2026-11-08",),
            as_of_disclaimer="本层只用 11-08",
            findings=("件量不慢",),
        )


def test_unaligned_layers_rejected():
    with pytest.raises((IncompleteReportError, ValidationError)):
        TwoLayerReport(
            overall=_layer("整体结论", "【测试，非正式】件量不慢，利润偏慢。"),
            departments=_dept_layers(supports=("件量不慢",)),
            used_as_of=("2026-11-08", "2026-11-12"),
            as_of_disclaimer="可对照但必须标明不同 as_of，不是同一天",
            findings=("件量不慢", "利润偏慢"),
        )


def test_different_as_of_must_be_labeled():
    with pytest.raises((IncompleteReportError, ValidationError)):
        TwoLayerReport(
            overall=_layer("整体结论", "【测试，非正式】件量不慢。"),
            departments=_dept_layers(),
            used_as_of=("2026-11-08", "2026-11-12"),
            as_of_disclaimer="对照",
            findings=("件量不慢",),
        )


def test_complete_aligned_report_accepted():
    report = TwoLayerReport(
        overall=_layer("整体结论", "【测试，非正式】件量不慢。"),
        departments=_dept_layers(),
        used_as_of=("2026-11-08", "2026-11-12"),
        as_of_disclaimer="可对照但必须标明不同 as_of，不是同一天",
        findings=("件量不慢",),
    )
    assert report.informal_mark == INFORMAL_MARK
    assert len(report.departments) == 9
