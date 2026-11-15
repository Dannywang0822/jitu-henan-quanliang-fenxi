"""合法夹具必须通过校验，且数字与已核对汇总一致。"""

from decimal import Decimal

from kernel.ratios import achievement_rate, as_percent


def test_staffing_totals_and_deltas(staffing):
    assert staffing.get("编制_总计_202610").value == "280"
    assert staffing.get("编制_总计_202510").value == "208"
    assert staffing.get("编制差额_总计").value == "72"
    total_610 = sum(Decimal(staffing.get(f"编制_{d}_202610").value) for d in
                    ["客服", "人资行政", "总经办", "市场", "质控", "网络管理", "财务", "营运", "云仓"])
    total_510 = sum(Decimal(staffing.get(f"编制_{d}_202510").value) for d in
                    ["客服", "人资行政", "总经办", "市场", "质控", "网络管理", "财务", "营运", "云仓"])
    assert total_610 == Decimal("280")
    assert total_510 == Decimal("208")
    assert staffing.get("编制_客服_202610").note and "13" in staffing.get("编制_客服_202610").note


def test_core_key_numbers(core_metrics):
    assert core_metrics.as_of == "2026-11-12"
    assert core_metrics.get("揽收量_当日").value == "666.7"
    assert core_metrics.get("揽收量_11月累计").value == "592.2"
    assert core_metrics.get("揽收量_11月累计").caliber == "累计日均"
    assert core_metrics.get("市场件量_当日").value == "42.8"
    assert core_metrics.get("云仓件量_11月累计").value == "17.2"
    assert core_metrics.get("千帆_已完成").value == "2"
    assert core_metrics.get("千帆_目标项数").value == "27"
    assert core_metrics.get("单公斤运力_核心指标_当日").value == "0.437"
    assert core_metrics.get("单票人力_考核_当日").value == "0.073"
    assert core_metrics.get("KPI_当日").value == "82.50"
    assert core_metrics.get("轨迹断更_当日").unit == "票"
    assert core_metrics.get("七星潭排名_当日").value == "4"


def test_pnl_key_numbers(pnl):
    assert pnl.as_of == "2026-11-08"
    assert pnl.get("累计收件").value == "4528"
    assert pnl.get("累计收件").caliber == "月累计件数"
    assert pnl.get("累计收件日均").value == "566"
    # 4528 / 8 = 566
    assert Decimal("4528") / Decimal("8") == Decimal("566")
    assert pnl.get("累计净利").value == "411"
    assert pnl.get("激励补贴_累计").value == "-1.220"
    assert pnl.get("市场直客净额_累计").value == "0.201"
    assert pnl.get("收件边际贡献_累计").value == "0.032"
    assert pnl.get("单票操作人力成本_累计").value == "0.086"
    assert pnl.get("单公斤运力_损益日报_累计").value == "0.367"
    # 揽件净收入实际公式 = 出港四费 + 激励补贴
    pickup = Decimal(pnl.get("出港四费_累计").value) + Decimal(pnl.get("激励补贴_累计").value)
    assert pickup == Decimal(pnl.get("揽件净收入_累计").value)
    # 预算公式不一致：出港四费+激励补贴+直客净额
    budget_inconsistent = (
        Decimal(pnl.get("出港四费_预算").value)
        + Decimal(pnl.get("激励补贴_预算").value)
        + Decimal(pnl.get("市场直客净额_预算").value)
    )
    assert budget_inconsistent == Decimal(pnl.get("揽件净收入_预算").value)
    assert (
        Decimal(pnl.get("出港四费_预算").value) + Decimal(pnl.get("激励补贴_预算").value)
        != Decimal(pnl.get("揽件净收入_预算").value)
    )


def test_income_achievement_printed_ok(pnl):
    assert as_percent(achievement_rate("13435", "51520"), 2) == Decimal("26.08")
    assert achievement_rate("582", "2809") == Decimal("582") / Decimal("2809")
    # 582/2809=20.719...%，印刷 20.71%；模型四舍五入到两位为 20.72
    assert abs(as_percent(achievement_rate("582", "2809"), 2) - Decimal("20.71")) <= Decimal("0.02")
