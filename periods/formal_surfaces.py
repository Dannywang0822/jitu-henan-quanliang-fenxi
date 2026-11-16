"""周运营台、决策逻辑、历史对比只读正式层。"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from pipeline.errors import FormalSurfaceUnavailable

SurfaceName = Literal["周运营台", "决策逻辑", "历史对比"]
SURFACES: tuple[SurfaceName, ...] = ("周运营台", "决策逻辑", "历史对比")


class SurfaceView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    name: SurfaceName
    available: bool
    status: Literal["不可用", "可用"]
    reason: str


def inspect_surface(name: SurfaceName, formal_count: int) -> SurfaceView:
    if name not in SURFACES:
        raise ValueError(f"未知正式层表面: {name}")
    if formal_count == 0:
        return SurfaceView(
            name=name,
            available=False,
            status="不可用",
            reason="正式层为空，周运营台、决策逻辑、历史对比只跑正式层",
        )
    return SurfaceView(name=name, available=True, status="可用", reason="正式层已有整包，只读正式层")


def require_surface(name: SurfaceName, formal_count: int) -> SurfaceView:
    view = inspect_surface(name, formal_count)
    if not view.available:
        raise FormalSurfaceUnavailable(view.reason)
    return view
