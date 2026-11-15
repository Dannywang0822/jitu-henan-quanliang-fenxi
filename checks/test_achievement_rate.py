"""预算达成率必须是实际/预算，拒绝 2−实际/预算。"""

from decimal import Decimal

import pytest

from kernel.ratios import (
    InvertedAchievementRateError,
    accept_achievement_rate,
    achievement_rate,
    as_percent,
    is_inverted_achievement,
)


def test_formula_is_actual_over_budget():
    assert achievement_rate("12853", "48711") == Decimal("12853") / Decimal("48711")


def test_reject_inverted_formula_result(pnl):
    cost = next(x for x in pnl.printed_suspicious if x.field_id.startswith("成本"))
    expense = next(x for x in pnl.printed_suspicious if x.field_id.startswith("费用"))
    for item in (cost, expense):
        printed = Decimal(item.printed_value.replace("%", "")) / Decimal(100)
        assert is_inverted_achievement(printed, Decimal(item.actual), Decimal(item.budget))
        with pytest.raises(InvertedAchievementRateError):
            accept_achievement_rate(printed, item.actual, item.budget)
        correct = achievement_rate(item.actual, item.budget)
        # 成本约 26.39%，费用约 26.68%
        pct = as_percent(correct, 2)
        if item.field_id.startswith("成本"):
            assert pct == Decimal("26.39")
        else:
            assert pct == Decimal("26.68")


def test_cannot_accept_173_as_correct_conclusion(pnl):
    # 模型重算必须用 12853/48711 与 171/641
    cost_rate = achievement_rate("12853", "48711")
    expense_rate = achievement_rate("171", "641")
    assert cost_rate < 1
    assert expense_rate < 1
    with pytest.raises(InvertedAchievementRateError):
        accept_achievement_rate("1.7361", "12853", "48711")
    with pytest.raises(InvertedAchievementRateError):
        accept_achievement_rate("1.7328", "171", "641")


def test_legal_volume_and_profit_achievement(pnl):
    vol = achievement_rate(pnl.get("累计收件日均").value, pnl.get("预算日均收件").value)
    profit = achievement_rate(pnl.get("累计净利").value, pnl.get("预算累计净利").value)
    assert as_percent(vol, 2) == Decimal("106.79")
    # 411/2169=18.9488...%，报表印刷 18.94%；模型用实际/预算，四舍五入到两位为 18.95
    assert profit == Decimal("411") / Decimal("2169")
    assert abs(as_percent(profit, 2) - Decimal("18.94")) <= Decimal("0.02")
