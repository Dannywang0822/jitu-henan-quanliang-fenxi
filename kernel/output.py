"""两层输出必须同时有方案和详细测算；对不上不能作为完整呈报。"""

from __future__ import annotations

from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from kernel.departments import ALL_DEPARTMENTS, Department, parse_department


class IncompleteReportError(ValueError):
    """输出不完整或两层对不上。"""


InformalMark = Literal["测试，非正式"]
INFORMAL_MARK: InformalMark = "测试，非正式"


class CalculationLine(BaseModel):
    """一条可复核测算。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    field_id: str
    description: str
    formula: str
    inputs: tuple[str, ...]
    result: str
    unit: str
    source_type: str
    as_of: str | None = None
    caliber: str | None = None


class LayerContent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    title: str
    plan: str
    detailed_calc: tuple[CalculationLine, ...]
    missing: tuple[str, ...] = ()
    informal_mark: InformalMark = INFORMAL_MARK

    @field_validator("plan")
    @classmethod
    def _plan_present(cls, v: str) -> str:
        if not v or not v.strip():
            raise IncompleteReportError("缺少方案")
        return v

    @field_validator("detailed_calc")
    @classmethod
    def _calc_present(cls, v: tuple[CalculationLine, ...]) -> tuple[CalculationLine, ...]:
        if not v:
            raise IncompleteReportError("缺少详细测算")
        return v

    @field_validator("informal_mark")
    @classmethod
    def _mark(cls, v: str) -> str:
        if v != INFORMAL_MARK:
            raise IncompleteReportError("测试层输出必须标明「测试，非正式」")
        return v


class DepartmentLayer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    department: Department
    content: LayerContent
    status: Literal["有分析", "无动作", "缺数"]
    supports_overall: tuple[str, ...] = ()

    @field_validator("department", mode="before")
    @classmethod
    def _dept(cls, v: Any) -> Department:
        return parse_department(v)


class TwoLayerReport(BaseModel):
    """完整呈报：整体结论 + 各部门重点关注目标，每层都有方案和详细测算。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    informal_mark: InformalMark = INFORMAL_MARK
    overall: LayerContent
    departments: tuple[DepartmentLayer, ...]
    used_as_of: tuple[str, ...]
    as_of_disclaimer: str
    findings: tuple[str, ...] = ()

    @field_validator("informal_mark")
    @classmethod
    def _mark(cls, v: str) -> str:
        if v != INFORMAL_MARK:
            raise IncompleteReportError("测试层输出必须标明「测试，非正式」")
        return v

    @model_validator(mode="after")
    def _complete_and_aligned(self) -> "TwoLayerReport":
        if not self.overall.plan.strip():
            raise IncompleteReportError("整体结论缺少方案")
        if not self.overall.detailed_calc:
            raise IncompleteReportError("整体结论缺少详细测算")

        present = {layer.department for layer in self.departments}
        missing = [d for d in ALL_DEPARTMENTS if d not in present]
        if missing:
            names = "、".join(d.value for d in missing)
            raise IncompleteReportError(f"第二层必须覆盖全部九个部门，缺: {names}")
        if len(self.departments) != len(present):
            raise IncompleteReportError("第二层部门重复")

        for layer in self.departments:
            if not layer.content.plan.strip():
                raise IncompleteReportError(f"{layer.department.value} 缺少方案")
            if not layer.content.detailed_calc:
                raise IncompleteReportError(f"{layer.department.value} 缺少详细测算")
            if layer.content.informal_mark != INFORMAL_MARK:
                raise IncompleteReportError(f"{layer.department.value} 未标明测试非正式")

        if len(set(self.used_as_of)) > 1:
            if "不同" not in self.as_of_disclaimer and "不是同一天" not in self.as_of_disclaimer:
                raise IncompleteReportError("引用不同 as_of 的报表时，必须标明不是同一天")

        overall_text = self.overall.plan + "\n" + "\n".join(
            line.description + line.result for line in self.overall.detailed_calc
        )
        finding_support = {f for layer in self.departments for f in layer.supports_overall}
        for finding in self.findings:
            if finding not in overall_text and finding not in self.overall.plan:
                # 允许 findings 是结构化标签，必须在方案或测算中有对应说明
                if finding not in self.overall.plan and not any(
                    finding in line.description or finding in line.result
                    for line in self.overall.detailed_calc
                ):
                    raise IncompleteReportError(f"整体结论未写明发现项: {finding}")
            if finding not in finding_support:
                raise IncompleteReportError(
                    f"两层内容对不上：整体发现「{finding}」没有部门层支撑"
                )
        return self


def assert_not_formal_policy(text: str) -> None:
    import re
    # 允许否定表述（不构成/不是已裁定政策），只拦截把测试结果写成正式结论的肯定句。
    cleaned = re.sub(r"(不构成|不是|并非|未写成|禁止写成|不能写成)已裁定政策", "", text)
    forbidden = ("已裁定政策", "正式政策已生效", "本结果为正式输出")
    for token in forbidden:
        if token in cleaned:
            raise IncompleteReportError(f"测试层不能把测试参数写成已裁定政策: {token}")
