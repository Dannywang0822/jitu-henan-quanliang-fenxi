"""部门是同一内核上的视角，统一接口。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from kernel.departments import ALL_DEPARTMENTS, Department, parse_department


@dataclass(frozen=True)
class DepartmentView:
    department: Department
    # 运力视角只允许挂在营运之下
    includes_capacity: bool = False


def department_views() -> tuple[DepartmentView, ...]:
    views = []
    for dept in ALL_DEPARTMENTS:
        views.append(
            DepartmentView(
                department=dept,
                includes_capacity=(dept is Department.营运),
            )
        )
    return tuple(views)


def attach_capacity(department: Department | str) -> DepartmentView:
    dept = parse_department(department)
    if dept is not Department.营运:
        from kernel.departments import CapacityIsNotDepartmentError
        raise CapacityIsNotDepartmentError("运力只放在营运部之下")
    return DepartmentView(department=dept, includes_capacity=True)
