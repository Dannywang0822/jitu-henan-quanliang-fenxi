"""部门只有九个；运力不是独立部门。"""

import pytest

from departments.interface import attach_capacity, department_views
from kernel.departments import CapacityIsNotDepartmentError, Department, UnknownDepartmentError, parse_department


def test_nine_departments_only():
    assert len(Department) == 9
    names = {d.value for d in Department}
    assert names == {"客服", "人资行政", "总经办", "市场", "质控", "网络管理", "财务", "营运", "云仓"}
    assert "运力" not in names


def test_capacity_is_not_a_department():
    with pytest.raises(CapacityIsNotDepartmentError):
        parse_department("运力")
    with pytest.raises(CapacityIsNotDepartmentError):
        parse_department("运力部")
    with pytest.raises(CapacityIsNotDepartmentError):
        attach_capacity("市场")
    view = attach_capacity("营运")
    assert view.includes_capacity is True
    views = department_views()
    assert len(views) == 9
    assert sum(1 for v in views if v.includes_capacity) == 1


def test_unknown_department_rejected():
    with pytest.raises(UnknownDepartmentError):
        parse_department("独立运力中心")


def test_staffing_uses_nine_departments(staffing):
    depts = {m.department for m in staffing.metrics if m.department}
    assert depts == {"客服", "人资行政", "总经办", "市场", "质控", "网络管理", "财务", "营运", "云仓"}
