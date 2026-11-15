"""运力视角：挂在营运部之下，不另起部门。"""

from __future__ import annotations

from dataclasses import dataclass

from kernel.departments import Department
from kernel.metrics import CAPACITY_PER_KG_CORE, CAPACITY_PER_KG_PNL


@dataclass(frozen=True)
class CapacityView:
    department: Department = Department.营运
    core_field_id: str = CAPACITY_PER_KG_CORE
    pnl_field_id: str = CAPACITY_PER_KG_PNL

    def unified_field(self) -> str:
        from kernel.metrics import auto_merge
        return auto_merge([self.core_field_id, self.pnl_field_id])
