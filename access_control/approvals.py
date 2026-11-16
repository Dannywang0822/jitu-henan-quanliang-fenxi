"""审批接口。审批决定本身不写正式层，也不自动晋升。"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, field_validator

from kernel.promotion import PromotionDenied
from pipeline.errors import AutoPromotionForbidden
from pipeline.permit import PROMOTION_PERMIT_TOKEN
from warehouse.local_dual import ExplicitPromotion


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    request_id: str
    kind: Literal["账号开通", "整包晋升"]
    subject_id: str
    approved: bool
    decided_by: str
    auto: Literal[False] = False

    @field_validator("auto")
    @classmethod
    def _no_auto(cls, value: bool) -> bool:
        if value is not False:
            raise AutoPromotionForbidden("不得自动审批或自动晋升")
        return value


class ApprovalBook:
    def __init__(self) -> None:
        self._records: dict[str, ApprovalRecord] = {}

    def submit(self, *, kind: Literal["账号开通", "整包晋升"], subject_id: str, requested_by: str) -> str:
        request_id = f"apr-{uuid4().hex[:12]}"
        if not requested_by.strip():
            raise ValueError("申请必须有提交人编号")
        self._records[request_id] = ApprovalRecord(
            request_id=request_id,
            kind=kind,
            subject_id=subject_id,
            approved=False,
            decided_by="",
        )
        return request_id

    def decide(self, request_id: str, *, approved: bool, decided_by: str) -> ApprovalRecord:
        current = self._records[request_id]
        record = current.model_copy(update={"approved": approved, "decided_by": decided_by, "auto": False})
        self._records[request_id] = record
        return record


def authorize_promotion(record: ApprovalRecord) -> ExplicitPromotion:
    """把 Danny 的整包点头换成晋升许可。调用方仍要自己执行晋升。"""
    if record.auto is not False:
        raise AutoPromotionForbidden("不得自动晋升正式层")
    if not (record.approved and record.decided_by == "Danny" and record.kind == "整包晋升"):
        raise PromotionDenied("未得到 Danny 对整包晋升的点头")
    return ExplicitPromotion(record.subject_id, PROMOTION_PERMIT_TOKEN)


def auto_promote(*_args, **_kwargs) -> None:
    raise AutoPromotionForbidden("不得自动晋升正式层")
