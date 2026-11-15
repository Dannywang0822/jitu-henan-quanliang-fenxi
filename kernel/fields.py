"""字段主键是字段标识，不用负责人姓名。"""

from __future__ import annotations

from typing import Any


class PersonNameAsPrimaryKeyError(ValueError):
    """以负责人姓名做主键。"""


# 字段标识允许字母数字下划线与中文指标名，不允许把「负责人/姓名」当键。
_FORBIDDEN_EXACT = frozenset({
    "负责人",
    "姓名",
    "负责人姓名",
    "责任人",
    "owner",
    "owner_name",
    "person_name",
    "person",
})

_FORBIDDEN_SUBSTRINGS = ("负责人姓名", "person_name", "owner_name")


class FieldId(str):
    """字段主键。构造时拒绝负责人姓名。"""

    def __new__(cls, raw: Any) -> "FieldId":
        return super().__new__(cls, parse_field_id(raw))


def looks_like_person_name_key(raw: str) -> bool:
    """只拦负责人/姓名类主键，不用「短中文词都是人名」的启发式，以免误伤指标名。"""
    text = raw.strip()
    lowered = text.lower()
    if text in _FORBIDDEN_EXACT or lowered in _FORBIDDEN_EXACT:
        return True
    # 含「姓名」或「负责人」的键一律拒绝；测试用「示例姓名」也走这条。
    if "姓名" in text or "负责人" in text:
        return True
    if any(s in text or s in lowered for s in _FORBIDDEN_SUBSTRINGS):
        return True
    return False


def parse_field_id(raw: Any) -> str:
    if raw is None or str(raw).strip() == "":
        raise ValueError("字段标识不能为空")
    text = str(raw).strip()
    if looks_like_person_name_key(text):
        raise PersonNameAsPrimaryKeyError(
            f"字段主键必须是字段标识，不能用负责人姓名: {text!r}"
        )
    return text
