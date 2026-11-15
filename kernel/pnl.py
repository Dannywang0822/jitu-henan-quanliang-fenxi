"""有损益恒等式输入时，利润分项加总必须平衡。"""

from __future__ import annotations

from decimal import Decimal
from typing import Mapping


class PnlIdentityError(ValueError):
    """损益恒等式不平衡。"""


def _dec(value: Decimal | str | int | float) -> Decimal:
    return Decimal(str(value))


def assert_pnl_identity(
    *,
    revenue: Decimal | str | int | float | None = None,
    cost: Decimal | str | int | float | None = None,
    expense: Decimal | str | int | float | None = None,
    gross_profit: Decimal | str | int | float | None = None,
    net_profit: Decimal | str | int | float | None = None,
    tolerance: Decimal | str | int | float = "0.5",
) -> None:
    """
    当对应分项都提供时检查：
    - 毛利 = 收入 − 成本
    - 净利 = 毛利 − 费用
    缺项则跳过该条恒等式，不编造。
    """
    tol = _dec(tolerance)
    if revenue is not None and cost is not None and gross_profit is not None:
        expected = _dec(revenue) - _dec(cost)
        actual = _dec(gross_profit)
        if abs(expected - actual) > tol:
            raise PnlIdentityError(
                f"毛利不平衡: 收入 {revenue} − 成本 {cost} = {expected}，但毛利为 {actual}"
            )
    if gross_profit is not None and expense is not None and net_profit is not None:
        expected = _dec(gross_profit) - _dec(expense)
        actual = _dec(net_profit)
        if abs(expected - actual) > tol:
            raise PnlIdentityError(
                f"净利不平衡: 毛利 {gross_profit} − 费用 {expense} = {expected}，但净利为 {actual}"
            )
    if revenue is not None and cost is not None and expense is not None and net_profit is not None:
        expected = _dec(revenue) - _dec(cost) - _dec(expense)
        actual = _dec(net_profit)
        if abs(expected - actual) > tol:
            raise PnlIdentityError(
                f"净利不平衡: 收入 {revenue} − 成本 {cost} − 费用 {expense} = {expected}，但净利为 {actual}"
            )


def assert_pnl_identity_from_mapping(data: Mapping[str, Decimal | str | int | float]) -> None:
    assert_pnl_identity(
        revenue=data.get("收入累计"),
        cost=data.get("成本累计"),
        expense=data.get("费用累计"),
        gross_profit=data.get("毛利累计"),
        net_profit=data.get("累计净利"),
    )
