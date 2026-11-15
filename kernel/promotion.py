"""正式层晋升：必须整包且 Danny 点头；未点头失败；支持回滚。"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class PromotionDenied(PermissionError):
    """未点头或条件不满足，晋升失败。"""


class IncompletePackageError(ValueError):
    """晋升包不完整。"""


class FormalLayerReadOnlyError(PermissionError):
    """正式层在测试期间只读；测试层不能写入。"""


SHANGHAI = timezone(timedelta(hours=8))

ALLOWED_PLACEHOLDERS = frozenset({".gitkeep", "README.md"})


class DannyApproval(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    approved: bool
    package_id: str
    signed_off_by: str
    signed_off_at: str | None = None
    note: str | None = None

    @field_validator("package_id")
    @classmethod
    def _pid(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("点头标志必须指向明确的包编号")
        return v


class PromotionPackage(BaseModel):
    """整包：方案 + 测算 + 输入快照 + 目标 + 裁定记录。缺一不可。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    package_id: str
    plan: str
    detailed_calc: str
    input_snapshot: dict[str, Any]
    targets: dict[str, Any]
    ruling_record: dict[str, Any]

    @field_validator("plan", "detailed_calc")
    @classmethod
    def _nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise IncompletePackageError("晋升包必须同时包含方案和详细测算")
        return v

    def assert_complete(self) -> None:
        if not self.input_snapshot:
            raise IncompletePackageError("晋升包缺少输入快照")
        if not self.targets:
            raise IncompletePackageError("晋升包缺少目标")
        required_ruling = ("裁定人", "方案", "依据", "生效时间")
        missing = [k for k in required_ruling if k not in self.ruling_record]
        if missing:
            raise IncompletePackageError(f"晋升包裁定记录缺字段: {missing}")


class FormalStore:
    """正式输出层存储。测试期间目录保持只读，除非带点头标志的整包晋升。"""

    def __init__(self, formal_dir: Path):
        self.formal_dir = Path(formal_dir)
        self.published_dir = self.formal_dir / "published"
        self.history_dir = self.formal_dir / "history"
        self._history_index = self.history_dir / "index.json"

    def published_entries(self) -> list[Path]:
        if not self.published_dir.exists():
            return []
        return [p for p in self.published_dir.iterdir() if p.name not in {".gitkeep"}]

    def assert_empty_if_unpromoted(self) -> None:
        unexpected = []
        if not self.formal_dir.exists():
            return
        for path in self.formal_dir.rglob("*"):
            if path.is_dir():
                continue
            rel = path.relative_to(self.formal_dir)
            if path.name in ALLOWED_PLACEHOLDERS and len(rel.parts) == 1:
                continue
            unexpected.append(str(rel))
        if unexpected:
            raise FormalLayerReadOnlyError(
                f"未整包晋升前正式层必须为空，发现: {unexpected}"
            )

    def promote(self, package: PromotionPackage, approval: DannyApproval) -> Path:
        package.assert_complete()
        if not approval.approved:
            raise PromotionDenied("未点头时 promote 必须失败")
        if approval.package_id != package.package_id:
            raise PromotionDenied("点头标志与晋升包编号不一致")
        if approval.signed_off_by.strip() != "Danny":
            raise PromotionDenied("正式层晋升需要明确的 Danny 点头标志")
        # 本轮不执行真正写入：即使条件满足，调用方若在测试期间也应谨慎。
        # 为保留可回滚接口，点头后才允许写入 published 并归档旧包。
        self.published_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        current = self.published_entries()
        if current:
            stamp = datetime.now(SHANGHAI).strftime("%Y%m%d%H%M%S")
            archive = self.history_dir / stamp
            archive.mkdir(parents=True, exist_ok=True)
            for item in current:
                shutil.move(str(item), archive / item.name)
        dest = self.published_dir / f"{package.package_id}.json"
        dest.write_text(
            package.model_dump_json(indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self._append_history({"action": "promote", "package_id": package.package_id})
        return dest

    def rollback(self, to_package_id: str | None = None) -> None:
        """回滚接口：撤回当前正式包，恢复上一归档；无归档则回到空目录。"""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        current = self.published_entries()
        stamp = datetime.now(SHANGHAI).strftime("%Y%m%d%H%M%S")
        if current:
            archive = self.history_dir / f"rollback-{stamp}"
            archive.mkdir(parents=True, exist_ok=True)
            for item in current:
                shutil.move(str(item), archive / item.name)
        if to_package_id:
            found = list(self.history_dir.rglob(f"{to_package_id}.json"))
            if not found:
                raise FileNotFoundError(f"没有可回滚的包: {to_package_id}")
            self.published_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(found[0], self.published_dir / found[0].name)
        self._append_history({"action": "rollback", "to_package_id": to_package_id})

    def _append_history(self, event: dict[str, Any]) -> None:
        event = dict(event)
        event["at"] = datetime.now(SHANGHAI).isoformat()
        records = []
        if self._history_index.exists():
            records = json.loads(self._history_index.read_text(encoding="utf-8"))
        records.append(event)
        self._history_index.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
