"""部门枚举只有九个；运力不是独立部门。"""

from __future__ import annotations

from enum import Enum
from typing import Any


class UnknownDepartmentError(ValueError):
    """无法识别或不在九个部门之内。"""


class CapacityIsNotDepartmentError(ValueError):
    """运力不是独立部门，必须归属营运。"""


class Department(str, Enum):
    客服 = "客服"
    人资行政 = "人资行政"
    总经办 = "总经办"
    市场 = "市场"
    质控 = "质控"
    网络管理 = "网络管理"
    财务 = "财务"
    营运 = "营运"
    云仓 = "云仓"


_ALIASES = {
    "客服": Department.客服,
    "客服部": Department.客服,
    "人资行政": Department.人资行政,
    "人资行政部": Department.人资行政,
    "人资": Department.人资行政,
    "总经办": Department.总经办,
    "市场": Department.市场,
    "市场部": Department.市场,
    "质控": Department.质控,
    "质控部": Department.质控,
    "网络管理": Department.网络管理,
    "网络管理部": Department.网络管理,
    "网络": Department.网络管理,
    "财务": Department.财务,
    "财务部": Department.财务,
    "营运": Department.营运,
    "营运部": Department.营运,
    "云仓": Department.云仓,
    "云仓部": Department.云仓,
}

_CAPACITY_ALIASES = frozenset({"运力", "运力部", "运力部门", "capacity", "transport"})


def parse_department(raw: Any) -> Department:
    if raw is None or str(raw).strip() == "":
        raise UnknownDepartmentError("部门不能为空")
    if isinstance(raw, Department):
        return raw
    text = str(raw).strip()
    if text in _CAPACITY_ALIASES:
        raise CapacityIsNotDepartmentError("运力不是独立部门，只放在营运部之下")
    if text in _ALIASES:
        return _ALIASES[text]
    raise UnknownDepartmentError(f"部门必须是已确认的九个之一，不能是: {text!r}")


ALL_DEPARTMENTS: tuple[Department, ...] = tuple(Department)
