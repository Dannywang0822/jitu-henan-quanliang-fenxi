"""把两层测试报告渲染为可读文稿。"""

from __future__ import annotations

from kernel.output import INFORMAL_MARK, DepartmentLayer, LayerContent, TwoLayerReport


BANNER = "测试，非正式"


def render_layer(content: LayerContent) -> str:
    lines = [
        f"# {content.title}",
        "",
        f"> 标记：{content.informal_mark}",
        "",
        "## 方案",
        "",
        content.plan,
        "",
        "## 详细测算",
        "",
    ]
    for i, item in enumerate(content.detailed_calc, 1):
        lines.extend([
            f"### {i}. {item.field_id}",
            "",
            f"- 说明：{item.description}",
            f"- 公式：{item.formula}",
            f"- 输入：{', '.join(item.inputs) if item.inputs else '（无）'}",
            f"- 结果：{item.result}" + (f" {item.unit}" if item.unit and item.unit not in item.result and item.unit != "—" else ""),
            f"- 来源类型：{item.source_type}",
            f"- as_of：{item.as_of or '（不适用）'}",
            f"- 口径：{item.caliber or '（未单列）'}",
            "",
        ])
    if content.missing:
        lines.extend(["## 缺数与不确定项", ""])
        for miss in content.missing:
            lines.append(f"- {miss}")
        lines.append("")
    return "\n".join(lines)


def render_departments(layers: tuple[DepartmentLayer, ...]) -> str:
    parts = [
        "# 各部门重点关注目标",
        "",
        f"> 标记：{INFORMAL_MARK}",
        "",
        "九个部门同一套拆分；运力放在营运部。本轮无动作或缺数的部门仍列出，避免漏看联动。",
        "",
    ]
    for layer in layers:
        parts.append(f"# {layer.department.value}（状态：{layer.status}）")
        parts.append("")
        if layer.supports_overall:
            parts.append("支撑的整体判断：" + "、".join(layer.supports_overall))
            parts.append("")
        # 去掉部门文稿里重复的一级标题
        body = render_layer(layer.content)
        body = "\n".join(body.splitlines()[1:]).strip()
        parts.append(body)
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def render_overall(report: TwoLayerReport) -> str:
    header = [
        f"> {BANNER}",
        "",
        f"{report.as_of_disclaimer}",
        "",
    ]
    return "\n".join(header) + render_layer(report.overall)
