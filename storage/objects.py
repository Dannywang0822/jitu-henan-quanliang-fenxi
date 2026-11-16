"""对象存储接口的本地夹具。不连接 CloudBase 存储或 COS。"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from kernel.detail import is_detail_column
from kernel.detail import DetailColumnRejected


class DetailUploadRejected(DetailColumnRejected):
    """明细整份拒收，不进对象存储，也不进宽表。"""


class StoredObject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    key: str
    file_id: str
    lane: str
    department: str
    source_type: str
    body_sha256: str
    byte_length: int
    validation: Literal["待字典校验", "字典不一致", "已入测试层宽表"]
    contains_detail: Literal[False] = False

    @field_validator("key")
    @classmethod
    def _key(cls, value: str) -> str:
        if value.startswith("formal/") or "document" in value:
            raise ValueError("对象键只能落在测试层存储前缀，不能指向正式层或文档库")
        if not value.startswith("test/"):
            raise ValueError("对象键必须以 test/ 开头")
        return value


class LocalObjectStore:
    """内存对象存储。进程结束即消失，不把上传内容提交进 git。"""

    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}
        self._bodies: dict[str, bytes] = {}

    def put_summary(
        self,
        *,
        file_id: str,
        lane: str,
        department: str,
        source_type: str,
        headers: list[str],
        body: bytes,
    ) -> StoredObject:
        for header in headers:
            if is_detail_column(header):
                raise DetailUploadRejected(f"明细一律拒收，不落存: {header}")
        slug = "frontline" if lane == "基层原始底表" else "analysis"
        stored = StoredObject(
            key=f"test/{slug}/{file_id}",
            file_id=file_id,
            lane=lane,
            department=department,
            source_type=source_type,
            body_sha256=hashlib.sha256(body).hexdigest(),
            byte_length=len(body),
            validation="待字典校验",
        )
        self._objects[stored.key] = stored
        self._bodies[stored.key] = body
        return stored

    def mark(self, key: str, validation: Literal["字典不一致", "已入测试层宽表"]) -> None:
        current = self._objects[key]
        self._objects[key] = current.model_copy(update={"validation": validation})

    def get(self, key: str) -> StoredObject:
        return self._objects[key]

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._objects))

    def body_text(self) -> str:
        return "\n".join(body.decode("utf-8") for body in self._bodies.values())
