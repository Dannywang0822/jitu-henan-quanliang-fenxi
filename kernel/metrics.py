"""禁止合并的分字段：两种单票人力、两表单公斤运力。"""

from __future__ import annotations

from typing import Iterable

from kernel.fields import FieldId, parse_field_id


class FieldMergeForbidden(ValueError):
    """禁止合并的字段被请求合并。"""


# 字段主键是字段标识。两种单票人力不得合并。
LABOR_COST_ASSESSMENT = "单票人力_考核"
LABOR_COST_OPS = "单票操作人力成本"

# 不同报表中的单公斤运力先分字段，禁止自动合并。
CAPACITY_PER_KG_CORE = "单公斤运力_核心指标"
CAPACITY_PER_KG_PNL = "单公斤运力_损益日报"

# 其它容易混淆、必须分列的标识。
INTAKE_CUM_DAILY_AVG_CORE = "揽收量_11月累计"
INTAKE_CUM_COUNT_PNL = "累计收件"
UNIT_NET_PROFIT = "单票净利"
UNIT_PICKUP_CONTRIBUTION = "收件边际贡献"

FORBIDDEN_MERGE_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({LABOR_COST_ASSESSMENT, LABOR_COST_OPS}),
    frozenset({CAPACITY_PER_KG_CORE, CAPACITY_PER_KG_PNL}),
})

ALIASES_TO_CANONICAL: dict[str, str] = {
    "单票人力（考核）": LABOR_COST_ASSESSMENT,
    "单票人力(考核)": LABOR_COST_ASSESSMENT,
    "单票人力考核": LABOR_COST_ASSESSMENT,
    "单票人力": LABOR_COST_ASSESSMENT,  # 核心指标表口径；与操作人力成本仍禁止合并
    "单票操作人力成本": LABOR_COST_OPS,
    "操作人力成本": LABOR_COST_OPS,
    "单公斤运力": CAPACITY_PER_KG_CORE,  # 仅当来源表已标明时才应调用 canonicalize_capacity
}


def _retain_or_map(text: str, canonical: str, aliases: tuple[str, ...]) -> str:
    """已是规范标识或其后缀形式则保留；仅短名/别名才映射到规范标识。"""
    if text == canonical or text.startswith(canonical + "_"):
        return text
    if text in aliases:
        return canonical
    return text


def canonicalize_labor(field_name: str, report_id: str | None = None) -> str:
    text = parse_field_id(field_name)
    mapped = _retain_or_map(
        text,
        LABOR_COST_OPS,
        ("单票操作人力成本", "操作人力成本"),
    )
    if mapped != text or text.startswith(LABOR_COST_OPS):
        return mapped if mapped.startswith(LABOR_COST_OPS) or mapped == LABOR_COST_OPS else mapped
    if "操作人力" in text:
        return _retain_or_map(text, LABOR_COST_OPS, ("单票操作人力成本", "操作人力成本"))
    mapped = _retain_or_map(
        text,
        LABOR_COST_ASSESSMENT,
        ("单票人力（考核）", "单票人力(考核)", "单票人力考核", "单票人力"),
    )
    if mapped != text or text.startswith(LABOR_COST_ASSESSMENT):
        return mapped
    if "考核" in text and "人力" in text:
        return LABOR_COST_ASSESSMENT
    if report_id == "core_metrics" and "人力" in text and "操作" not in text:
        if text == "单票人力":
            return LABOR_COST_ASSESSMENT
    if text in ALIASES_TO_CANONICAL and "运力" not in text:
        return ALIASES_TO_CANONICAL[text]
    return text


def canonicalize_capacity(field_name: str, report_id: str) -> str:
    text = parse_field_id(field_name)
    if "单公斤运力" not in text:
        return text
    if text.startswith(CAPACITY_PER_KG_CORE) or text.startswith(CAPACITY_PER_KG_PNL):
        # 已经是分字段标识，保留后缀（当日/累计/目标等）
        return text
    if report_id in {"core_metrics", "核心指标", "河南代理区核心指标项"}:
        return CAPACITY_PER_KG_CORE if text == "单公斤运力" else text.replace("单公斤运力", CAPACITY_PER_KG_CORE, 1)
    if report_id in {"pnl", "pnl_daily", "损益日报", "河南代理区损益日报"}:
        return CAPACITY_PER_KG_PNL if text == "单公斤运力" else text.replace("单公斤运力", CAPACITY_PER_KG_PNL, 1)
    raise FieldMergeForbidden(
        f"单公斤运力必须先标明来源报表再分字段，不能无表名自动归并: {field_name!r} / {report_id!r}"
    )


def forbid_merge(field_a: str, field_b: str) -> None:
    a = parse_field_id(field_a)
    b = parse_field_id(field_b)
    if a == b:
        return
    if frozenset({a, b}) in FORBIDDEN_MERGE_PAIRS:
        raise FieldMergeForbidden(f"禁止合并字段: {a} 与 {b}")
    # 即使用别名呼叫，也要拦住。
    mapped = {ALIASES_TO_CANONICAL.get(a, a), ALIASES_TO_CANONICAL.get(b, b)}
    if frozenset(mapped) in FORBIDDEN_MERGE_PAIRS:
        raise FieldMergeForbidden(f"禁止合并字段: {a} 与 {b}")


def auto_merge(field_ids: Iterable[str]) -> str:
    """任何自动合并入口。命中禁止配对或跨表单公斤运力则失败。"""
    ids = [parse_field_id(x) for x in field_ids]
    unique = list(dict.fromkeys(ids))
    if len(unique) <= 1:
        raise FieldMergeForbidden("自动合并至少需要两个不同字段；禁止把分字段悄悄合成一个")
    for i, a in enumerate(unique):
        for b in unique[i + 1 :]:
            forbid_merge(a, b)
    raise FieldMergeForbidden(f"禁止自动合并不同字段: {unique}")
