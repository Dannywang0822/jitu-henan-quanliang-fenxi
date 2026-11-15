"""九个部门模块的统一接口；运力只放在营运部之下。"""

from departments.interface import DepartmentView, department_views
from kernel.departments import Department, parse_department, CapacityIsNotDepartmentError

__all__ = [
    "Department",
    "DepartmentView",
    "department_views",
    "parse_department",
    "CapacityIsNotDepartmentError",
]
