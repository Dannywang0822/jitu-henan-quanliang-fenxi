"""指定开通账号。不开放注册，不实现登录，不接飞书。"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from kernel.departments import parse_department
from pipeline.errors import OpenRegistrationForbidden


class Role(str, Enum):
    决策中枢 = "决策中枢"
    经理 = "经理"
    主管 = "主管"
    基层上传 = "基层上传"
    经营分析 = "经营分析"


LANE_ROLE = {
    "基层原始底表": Role.基层上传,
    "经营分析组汇总表": Role.经营分析,
}


class Account(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    account_id: str
    role: Role
    department: str | None
    opened_by: Literal["平台指定"] = "平台指定"
    registration: Literal["指定开通"] = "指定开通"

    @field_validator("account_id")
    @classmethod
    def _id(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("账号编号不能为空")
        return text


class AccountDirectory:
    def __init__(self) -> None:
        self._items: dict[str, Account] = {}

    def open_designated(
        self,
        *,
        account_id: str,
        role: Role | str,
        department: str | None,
        opened_by: str = "平台指定",
    ) -> Account:
        if opened_by != "平台指定":
            raise OpenRegistrationForbidden("账号按需指定开通，不开放注册")
        if account_id in self._items:
            raise OpenRegistrationForbidden("账号已指定开通，不能自行再注册")
        parsed_role = Role(role)
        dept: str | None = None
        if department not in (None, ""):
            dept = parse_department(department).value
        if parsed_role != Role.决策中枢 and dept is None:
            raise OpenRegistrationForbidden("除决策中枢外，指定开通必须绑定部门")
        account = Account(account_id=account_id, role=parsed_role, department=dept)
        self._items[account_id] = account
        return account

    def register(self, *_args, **_kwargs) -> None:
        raise OpenRegistrationForbidden("不开放注册")

    def require(self, account_id: str) -> Account:
        try:
            return self._items[account_id]
        except KeyError as exc:
            raise OpenRegistrationForbidden("账号未指定开通，不能上传") from exc
