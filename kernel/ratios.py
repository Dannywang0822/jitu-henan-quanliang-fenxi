"""环比口径、累计口径，以及预算达成率 = 实际 / 预算。"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class MissingMomTypeError(ValueError):
    """环比缺少口径类型。"""


class WrongCumulativeCaliberError(ValueError):
    """用错累计口径（累计日均 vs 月累计件数）。"""


class InvertedAchievementRateError(ValueError):
    """使用或接受了 2 − 实际/预算 的错误达成率。"""


class MomType(str, Enum):
    比上一营业日 = "比上一营业日"
    比上月同期进度 = "比上月同期进度"


class CumulativeKind(str, Enum):
    累计日均 = "累计日均"
    月累计件数 = "月累计件数"


def parse_mom_type(raw: Any) -> MomType:
    if raw is None or str(raw).strip() == "":
        raise MissingMomTypeError("环比必须标明口径：比上一营业日，或比上月同期进度")
    if isinstance(raw, MomType):
        return raw
    text = str(raw).strip()
    try:
        return MomType(text)
    except ValueError as exc:
        raise MissingMomTypeError(f"环比口径无法识别或禁止无类型混用: {text!r}") from exc


class MomChange(BaseModel):
    """带类型的环比变化。无类型无法构造，不同类型不得当作同一口径合并。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    field_id: str
    value: Decimal
    unit: str
    mom_type: MomType

    @field_validator("mom_type", mode="before")
    @classmethod
    def _mom(cls, v: Any) -> MomType:
        return parse_mom_type(v)

    @field_validator("value", mode="before")
    @classmethod
    def _dec(cls, v: Any) -> Decimal:
        return Decimal(str(v))


def merge_mom(a: MomChange, b: MomChange) -> None:
    if a.mom_type != b.mom_type:
        raise MissingMomTypeError(
            f"禁止把不同环比口径混用: {a.field_id} 为 {a.mom_type.value}，"
            f"{b.field_id} 为 {b.mom_type.value}"
        )
    raise MissingMomTypeError("即使口径相同，环比变化也不得无说明地合并成一项")


class CumulativeMetric(BaseModel):
    """累计指标必须声明是累计日均还是月累计件数。"""

    model_config = ConfigDict(frozen=True, extra="forbid")
    field_id: str
    value: Decimal
    unit: str
    kind: CumulativeKind
    as_of: str
    days_elapsed: int | None = None

    @field_validator("kind", mode="before")
    @classmethod
    def _kind(cls, v: Any) -> CumulativeKind:
        if v is None or str(v).strip() == "":
            raise WrongCumulativeCaliberError("累计指标必须声明口径")
        if isinstance(v, CumulativeKind):
            return v
        text = str(v).strip()
        try:
            return CumulativeKind(text)
        except ValueError as exc:
            raise WrongCumulativeCaliberError(f"累计口径无法识别: {text!r}") from exc

    @field_validator("value", mode="before")
    @classmethod
    def _dec(cls, v: Any) -> Decimal:
        return Decimal(str(v))


def as_monthly_total(metric: CumulativeMetric) -> Decimal:
    if metric.kind is not CumulativeKind.月累计件数:
        raise WrongCumulativeCaliberError(
            f"{metric.field_id} 的累计口径是 {metric.kind.value}，不能当作月累计件数使用"
        )
    return metric.value


def as_daily_average(metric: CumulativeMetric) -> Decimal:
    if metric.kind is CumulativeKind.累计日均:
        return metric.value
    if metric.kind is CumulativeKind.月累计件数:
        if not metric.days_elapsed:
            raise WrongCumulativeCaliberError(
                f"{metric.field_id} 是月累计件数，换算日均必须提供已过天数，禁止把合计直接当累计日均"
            )
        return metric.value / Decimal(metric.days_elapsed)
    raise WrongCumulativeCaliberError(f"无法从 {metric.kind} 取累计日均")


def achievement_rate(actual: Decimal | str | int | float, budget: Decimal | str | int | float) -> Decimal:
    """预算达成率 = 实际 / 预算。禁止 2 − 实际/预算。"""
    a = Decimal(str(actual))
    b = Decimal(str(budget))
    if b == 0:
        raise ValueError("预算为 0，无法计算达成率")
    return a / b


def is_inverted_achievement(reported: Decimal, actual: Decimal, budget: Decimal, tol: Decimal | None = None) -> bool:
    if budget == 0:
        return False
    correct = actual / budget
    inverted = Decimal(2) - correct
    epsilon = tol if tol is not None else Decimal("0.005")
    return abs(reported - inverted) <= epsilon and abs(reported - correct) > epsilon


def accept_achievement_rate(
    reported: Decimal | str | int | float,
    actual: Decimal | str | int | float,
    budget: Decimal | str | int | float,
) -> Decimal:
    """若报送值等于 2−实际/预算，则拒绝；否则返回正确的 实际/预算。"""
    rep = Decimal(str(reported))
    a = Decimal(str(actual))
    b = Decimal(str(budget))
    if is_inverted_achievement(rep, a, b):
        correct = achievement_rate(a, b)
        raise InvertedAchievementRateError(
            f"拒绝使用或接受 2−实际/预算 的达成率: 报送 {rep}，"
            f"按该错误公式约为 {Decimal(2) - a / b}，正确值应为 实际/预算 = {correct}"
        )
    return achievement_rate(a, b)


def as_percent(rate: Decimal, places: int = 2) -> Decimal:
    q = Decimal("1").scaleb(-places)
    return (rate * Decimal(100)).quantize(q, rounding=ROUND_HALF_UP)
