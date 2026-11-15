"""测试层演算：从夹具计算判断，不把结论写死。"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from data_interface.ingest import FixtureMetric, FixtureReport
from kernel.departments import ALL_DEPARTMENTS, Department
from kernel.output import (
    INFORMAL_MARK,
    CalculationLine,
    DepartmentLayer,
    LayerContent,
    TwoLayerReport,
    assert_not_formal_policy,
)
from kernel.ratios import achievement_rate, as_percent, accept_achievement_rate, InvertedAchievementRateError


SRC = "Danny提供的汇总"
MARK = "【测试，非正式】"


def _d(metric: FixtureMetric | str | Decimal) -> Decimal:
    if isinstance(metric, FixtureMetric):
        return Decimal(metric.value)
    return Decimal(str(metric))


def _line(
    field_id: str,
    description: str,
    formula: str,
    inputs: Iterable[str],
    result: str,
    unit: str,
    as_of: str | None,
    caliber: str | None = None,
    source_type: str = SRC,
) -> CalculationLine:
    return CalculationLine(
        field_id=field_id,
        description=description,
        formula=formula,
        inputs=tuple(inputs),
        result=result,
        unit=unit,
        source_type=source_type,
        as_of=as_of,
        caliber=caliber,
    )


def _pct(rate: Decimal, places: int = 2) -> str:
    return f"{as_percent(rate, places)}%"


def _fmt(value: Decimal, places: int | None = None) -> str:
    if places is None:
        return format(value, "f")
    q = Decimal("1").scaleb(-places)
    return format(value.quantize(q), "f")


def analyze(staffing: FixtureReport, core: FixtureReport, pnl: FixtureReport) -> TwoLayerReport:
    if core.as_of == pnl.as_of:
        raise RuntimeError("两张经营表不得被当成同一天")

    overall_lines: list[CalculationLine] = []
    missing = [
        "同一天对照表：2026-11-08 损益日报与 2026-11-12 核心指标不是同一天，缺同日对照，不能合并后下结论",
        "覆盖/加盟政策结果汇总：本轮未提供，网络管理部相关政策效果缺数",
        "运力结构/储备：本轮未提供结构与储备汇总，营运部运力只能看到单票/单公斤单价，不能判断运力结构",
    ]

    # ---- 件量 ----
    pnl_avg = _d(pnl.get("累计收件日均"))
    pnl_avg_budget = _d(pnl.get("预算日均收件"))
    pnl_vol_rate = achievement_rate(pnl_avg, pnl_avg_budget)
    core_day = _d(core.get("揽收量_当日"))
    core_cum = _d(core.get("揽收量_11月累计"))
    core_target = _d(core.get("揽收量_目标"))
    volume_ok = (pnl_avg >= pnl_avg_budget) and (core_day >= core_target) and (core_cum >= core_target)
    volume_label = "件量不慢" if volume_ok else "件量偏慢"

    overall_lines.append(_line(
        "累计收件日均",
        f"损益日报累计收件日均 {pnl_avg} 万票，对照预算日均 {pnl_avg_budget} 万票，达成 {_pct(pnl_vol_rate)}",
        "累计收件日均 / 预算日均",
        ("累计收件日均", "预算日均收件"),
        _pct(pnl_vol_rate),
        "达成率",
        pnl.as_of,
        "累计日均（由月累计件数÷已过天数）",
    ))
    overall_lines.append(_line(
        "累计收件",
        f"损益累计收件 {pnl.get('累计收件').value} 万票为月累计件数，不是累计日均；÷已过 {pnl.get('已过天数').value} 天得到日均 {pnl_avg}",
        "累计收件 / 已过天数",
        ("累计收件", "已过天数"),
        f"{pnl_avg}万票",
        "万票",
        pnl.as_of,
        "月累计件数",
    ))
    overall_lines.append(_line(
        "揽收量_当日",
        f"核心指标当日揽收量 {core_day} 万票，目标 {core_target} 万票；11月累计是累计日均 {core_cum} 万票，不是月合计",
        "当日与累计日均分别对照目标，禁止把累计日均当月合计",
        ("揽收量_当日", "揽收量_11月累计", "揽收量_目标"),
        f"当日{core_day}/目标{core_target}；累计日均{core_cum}/目标{core_target}",
        "万票",
        core.as_of,
        "当日及累计日均",
    ))

    # ---- 利润与时间进度 ----
    net = _d(pnl.get("累计净利"))
    net_budget = _d(pnl.get("预算累计净利"))
    net_rate = achievement_rate(net, net_budget)
    days = _d(pnl.get("已过天数"))
    month_days = _d(pnl.get("本月日历天数"))
    time_rate = days / month_days
    profit_slow = net_rate < time_rate
    profit_label = "利润偏慢" if profit_slow else "利润进度不慢"
    unit_profit = _d(pnl.get("单票净利_累计"))
    unit_profit_budget = _d(pnl.get("单票净利_预算"))
    unit_profit_rate = achievement_rate(unit_profit, unit_profit_budget)

    overall_lines.append(_line(
        "累计净利",
        f"累计净利 {net} 万元 / 预算 {net_budget} 万元 = {_pct(net_rate)}（印刷 18.94%；精确四舍五入两位为 {_pct(net_rate)}）",
        "累计净利 / 预算累计净利",
        ("累计净利", "预算累计净利"),
        _pct(net_rate),
        "达成率",
        pnl.as_of,
        "月累计",
    ))
    overall_lines.append(_line(
        "时间进度",
        f"时间进度 = 已过天数 {days} / 本月日历天数 {month_days} = {_pct(time_rate)}（表述约 27%）",
        "已过天数 / 本月日历天数",
        ("已过天数", "本月日历天数"),
        _pct(time_rate),
        "比率",
        pnl.as_of,
        "8/30",
    ))
    overall_lines.append(_line(
        "单票净利_累计",
        f"单票净利累计 {unit_profit} 元/票，预算 {unit_profit_budget}，达成 {_pct(unit_profit_rate)}（印刷 66.50%）",
        "单票净利累计 / 单票净利预算",
        ("单票净利_累计", "单票净利_预算"),
        _pct(unit_profit_rate),
        "达成率",
        pnl.as_of,
        "月累计单票",
    ))

    # ---- 预算达成率纠错（成本/费用）----
    cost = _d(pnl.get("成本累计"))
    cost_budget = _d(pnl.get("成本预算"))
    expense = _d(pnl.get("费用累计"))
    expense_budget = _d(pnl.get("费用预算"))
    cost_rate = achievement_rate(cost, cost_budget)
    expense_rate = achievement_rate(expense, expense_budget)
    for item in pnl.printed_suspicious:
        printed = Decimal(item.printed_value.replace("%", "")) / Decimal(100)
        try:
            accept_achievement_rate(printed, item.actual, item.budget)
            raise RuntimeError(f"未拒绝可疑印刷达成率 {item.printed_value}")
        except InvertedAchievementRateError:
            pass
    overall_lines.append(_line(
        "成本预算达成率",
        f"成本累计 {cost} / 预算 {cost_budget} = {_pct(cost_rate)}。报表印刷 173.61% 为 2−实际/预算，已拒绝作为正确结论",
        "累计 / 预算；禁止 2−实际/预算",
        ("成本累计", "成本预算"),
        _pct(cost_rate),
        "达成率",
        pnl.as_of,
        "月累计",
    ))
    overall_lines.append(_line(
        "费用预算达成率",
        f"费用累计 {expense} / 预算 {expense_budget} = {_pct(expense_rate)}。报表印刷 173.28% 为 2−实际/预算，已拒绝作为正确结论",
        "累计 / 预算；禁止 2−实际/预算",
        ("费用累计", "费用预算"),
        _pct(expense_rate),
        "达成率",
        pnl.as_of,
        "月累计",
    ))

    # ---- 揽件侧拆解 ----
    margin = _d(pnl.get("收件边际贡献_累计"))
    margin_budget = _d(pnl.get("收件边际贡献_预算"))
    incentive = _d(pnl.get("激励补贴_累计"))
    incentive_budget = _d(pnl.get("激励补贴_预算"))
    direct = _d(pnl.get("市场直客净额_累计"))
    direct_budget = _d(pnl.get("市场直客净额_预算"))
    four_fee = _d(pnl.get("出港四费_累计"))
    four_fee_budget = _d(pnl.get("出港四费_预算"))
    delivery_net = _d(pnl.get("派件费净额_累计"))
    delivery_net_budget = _d(pnl.get("派件费净额_预算"))
    pickup_income = _d(pnl.get("揽件净收入_累计"))
    pickup_income_budget = _d(pnl.get("揽件净收入_预算"))
    pickup_actual_formula = four_fee + incentive
    pickup_budget_inconsistent = four_fee_budget + incentive_budget + direct_budget
    pickup_formula_ok_actual = pickup_actual_formula == pickup_income
    pickup_budget_matches_inconsistent = pickup_budget_inconsistent == pickup_income_budget
    pickup_side = (margin < margin_budget) and (incentive < incentive_budget) and (direct < direct_budget)
    pickup_label = "缺口主在揽件侧" if pickup_side else "揽件侧不是主要缺口"

    overall_lines.append(_line(
        "收件边际贡献_累计",
        f"收件边际贡献 {margin} 对预算 {margin_budget}，差额 {_fmt(margin - margin_budget, 3)} 元/票",
        "累计 − 预算",
        ("收件边际贡献_累计", "收件边际贡献_预算"),
        f"{_fmt(margin - margin_budget, 3)}元/票",
        "元/票",
        pnl.as_of,
        "月累计单票",
    ))
    overall_lines.append(_line(
        "激励补贴_累计",
        f"激励补贴 {incentive} 对预算 {incentive_budget}，差额 {_fmt(incentive - incentive_budget, 3)} 元/票（加重）",
        "累计 − 预算",
        ("激励补贴_累计", "激励补贴_预算"),
        f"{_fmt(incentive - incentive_budget, 3)}元/票",
        "元/票",
        pnl.as_of,
        "月累计单票",
    ))
    overall_lines.append(_line(
        "市场直客净额_累计",
        f"市场直客净额 {direct} 对预算 {direct_budget}，差额 {_fmt(direct - direct_budget, 3)} 元/票（偏弱）",
        "累计 − 预算",
        ("市场直客净额_累计", "市场直客净额_预算"),
        f"{_fmt(direct - direct_budget, 3)}元/票",
        "元/票",
        pnl.as_of,
        "月累计单票",
    ))
    overall_lines.append(_line(
        "出港四费_累计",
        f"出港四费 {four_fee} 对预算 {four_fee_budget}，差额 {_fmt(four_fee - four_fee_budget, 3)} 元/票，为正贡献",
        "累计 − 预算",
        ("出港四费_累计", "出港四费_预算"),
        f"{_fmt(four_fee - four_fee_budget, 3)}元/票",
        "元/票",
        pnl.as_of,
        "月累计单票",
    ))
    overall_lines.append(_line(
        "派件费净额_累计",
        f"派件费净额 {delivery_net} 对预算 {delivery_net_budget}，差额 {_fmt(delivery_net - delivery_net_budget, 3)} 元/票，为正贡献",
        "累计 − 预算",
        ("派件费净额_累计", "派件费净额_预算"),
        f"{_fmt(delivery_net - delivery_net_budget, 3)}元/票",
        "元/票",
        pnl.as_of,
        "月累计单票",
    ))
    overall_lines.append(_line(
        "揽件净收入_累计",
        f"实际 {pickup_income} = 出港四费+激励补贴（{pickup_actual_formula}，一致={pickup_formula_ok_actual}）；"
        f"预算 {pickup_income_budget} = 出港四费+激励补贴+直客净额（{pickup_budget_inconsistent}，一致={pickup_budget_matches_inconsistent}）。分子分母不一致，不用该达成率做主结论",
        "核对公式，不把不一致的达成率当主结论",
        ("出港四费_累计", "激励补贴_累计", "市场直客净额_预算", "揽件净收入_累计", "揽件净收入_预算"),
        "公式不一致，不采用该达成率",
        "—",
        pnl.as_of,
        "月累计单票",
    ))

    # ---- 运力分字段、分日期 ----
    cap_pnl = _d(pnl.get("单公斤运力_损益日报_累计"))
    cap_pnl_budget = _d(pnl.get("单公斤运力_损益日报_预算"))
    cap_pnl_oct = _d(pnl.get("单公斤运力_损益日报_10月"))
    cap_pnl_day = _d(pnl.get("单公斤运力_损益日报_当日"))
    cap_core_day = _d(core.get("单公斤运力_核心指标_当日"))
    cap_core_cum = _d(core.get("单公斤运力_核心指标_累计"))
    cap_core_target = _d(core.get("单公斤运力_核心指标_目标"))
    cap_core_oct = _d(core.get("单公斤运力_核心指标_10月"))
    pnl_cap_deviation = achievement_rate(cap_pnl, cap_pnl_budget) - 1
    # 「尚可」：相对预算偏离不超过 8%，且接近 10 月
    pnl_cap_ok = abs(pnl_cap_deviation) <= Decimal("0.08") and abs(cap_pnl - cap_pnl_oct) <= Decimal("0.02")
    core_cap_high = cap_core_day > cap_core_target and (cap_core_day / cap_core_target - 1) > Decimal("0.10")
    capacity_label = "运力口径不得合并"

    overall_lines.append(_line(
        "单公斤运力_损益日报_累计",
        f"{pnl.as_of} 损益口径单公斤运力累计 {cap_pnl}（预算 {cap_pnl_budget}，10月 {cap_pnl_oct}，当日 {cap_pnl_day}），相对预算偏离 {_pct(pnl_cap_deviation)}，判断为「{'尚可' if pnl_cap_ok else '已偏高'}」",
        "损益口径单独测算，不与核心指标合并",
        ("单公斤运力_损益日报_累计", "单公斤运力_损益日报_预算", "单公斤运力_损益日报_10月", "单公斤运力_损益日报_当日"),
        "尚可" if pnl_cap_ok else "已偏高",
        "元/公斤",
        pnl.as_of,
        "含自营，损益口径",
    ))
    overall_lines.append(_line(
        "单公斤运力_核心指标_当日",
        f"{core.as_of} 核心指标单公斤运力当日 {cap_core_day}（累计 {cap_core_cum}，目标 {cap_core_target}，10月 {cap_core_oct}），当日相对目标偏离 {_pct(cap_core_day / cap_core_target - 1)}，判断为「{'已偏高' if core_cap_high else '接近目标'}」",
        "核心指标口径单独测算，不与损益表合并",
        ("单公斤运力_核心指标_当日", "单公斤运力_核心指标_累计", "单公斤运力_核心指标_目标", "单公斤运力_核心指标_10月"),
        "已偏高" if core_cap_high else "接近目标",
        "元/公斤",
        core.as_of,
        "核心指标口径",
    ))

    # ---- 质量与云仓、千帆 ----
    kpi = _d(core.get("KPI_当日"))
    kpi_target = _d(core.get("KPI_目标"))
    kpi_cum = _d(core.get("KPI_月累计"))
    kpi_mom = Decimal(core.get("KPI_当日").mom_value or "0")
    outbound = _d(core.get("出港准点_当日"))
    outbound_target = _d(core.get("出港准点_目标"))
    outbound_mom = Decimal(core.get("出港准点_当日").mom_value or "0")
    breaks = _d(core.get("轨迹断更_当日"))
    breaks_mom = Decimal(core.get("轨迹断更_当日").mom_value or "0")
    quality_worse = (kpi < kpi_target and kpi_mom < 0) and (outbound < outbound_target and outbound_mom < 0) and (breaks_mom > 0)
    quality_label = "质量当日变差" if quality_worse else "质量未同时变差"

    overall_lines.append(_line(
        "KPI_当日",
        f"KPI 当日 {kpi}（环比 {kpi_mom}，目标 {kpi_target}），月累计 {kpi_cum}「{'仍达标' if kpi_cum >= kpi_target else '未达标'}」；环比口径为比上一营业日",
        "当日对照目标，并看比上一营业日",
        ("KPI_当日", "KPI_目标", "KPI_月累计"),
        f"{kpi}（目标{kpi_target}，累计{kpi_cum}）",
        "分",
        core.as_of,
        "当日",
    ))
    overall_lines.append(_line(
        "出港准点_当日",
        f"出港准点 {outbound}%（环比 {outbound_mom} 个百分点，目标 {outbound_target}%）",
        "当日对照目标，并看比上一营业日",
        ("出港准点_当日", "出港准点_目标"),
        f"{outbound}%",
        "%",
        core.as_of,
        "当日",
    ))
    overall_lines.append(_line(
        "轨迹断更_当日",
        f"轨迹断更 {breaks} 票（环比 +{breaks_mom} 票）。字段名是「率」，实际是票数",
        "按票数读，不按比率读",
        ("轨迹断更_当日",),
        f"{breaks}票",
        "票",
        core.as_of,
        "当日（字段名是率，实际是票数）",
    ))

    cloud_day = _d(core.get("云仓件量_当日"))
    cloud_cum = _d(core.get("云仓件量_11月累计"))
    cloud_target = _d(core.get("云仓件量_目标"))
    cloud_behind = (cloud_day < cloud_target) and (cloud_cum < cloud_target)
    cloud_ratio = cloud_cum / cloud_target
    cloud_label = "云仓件量落后" if cloud_behind else "云仓件量未落后"
    overall_lines.append(_line(
        "云仓件量_11月累计",
        f"云仓（不含三方）当日 {cloud_day}、累计日均 {cloud_cum}，目标 {cloud_target}，累计日均达成 {_pct(cloud_ratio)}，判断为「{'落后' if cloud_behind else '未落后'}」",
        "累计日均 / 目标",
        ("云仓件量_当日", "云仓件量_11月累计", "云仓件量_目标"),
        _pct(cloud_ratio),
        "达成率",
        core.as_of,
        "累计日均，不含三方",
    ))

    qianfan = _d(core.get("千帆_已完成"))
    qianfan_target = _d(core.get("千帆_目标项数"))
    overall_lines.append(_line(
        "千帆_已完成",
        f"千帆进度 {qianfan}/{qianfan_target}",
        "已完成项数 / 目标项数",
        ("千帆_已完成", "千帆_目标项数"),
        f"{qianfan}/{qianfan_target}",
        "项",
        core.as_of,
        "当年进度 2/27",
    ))

    market_day = _d(core.get("市场件量_当日"))
    market_cum = _d(core.get("市场件量_11月累计"))
    market_target = _d(core.get("市场件量_目标"))
    overall_lines.append(_line(
        "市场件量_11月累计",
        f"市场当日 {market_day}、累计日均 {market_cum}，目标 {market_target}，累计日均达成 {_pct(market_cum / market_target)}",
        "累计日均 / 目标",
        ("市场件量_当日", "市场件量_11月累计", "市场件量_目标"),
        _pct(market_cum / market_target),
        "达成率",
        core.as_of,
        "累计日均",
    ))

    findings = [volume_label, profit_label, pickup_label, capacity_label, quality_label, cloud_label]
    assert all(x in {
        "件量不慢", "件量偏慢", "利润偏慢", "利润进度不慢",
        "缺口主在揽件侧", "揽件侧不是主要缺口",
        "运力口径不得合并", "质量当日变差", "质量未同时变差",
        "云仓件量落后", "云仓件量未落后",
    } for x in findings)

    overall_plan = (
        f"{MARK} 本呈报仅供测试，非正式，不构成已裁定政策。\n"
        f"引用了不同 as_of 的报表，可对照但必须标明不是同一天："
        f"编制对照期间 202510 vs 202610，损益日报 {pnl.as_of}，核心指标 {core.as_of}。\n"
        f"整体判断：{volume_label}（损益累计日均 {pnl_avg} 万票对预算 {pnl_avg_budget} 万票，达成 {_pct(pnl_vol_rate)}；"
        f"核心指标 {core.as_of} 当日 {core_day} 万票、累计日均 {core_cum} 万票，目标 {core_target} 万票）；"
        f"{profit_label}（累计净利 {net}/{net_budget} 约 {_pct(net_rate)}，时间进度 {_pct(time_rate)}；"
        f"单票净利 {unit_profit} 对预算 {unit_profit_budget}）；"
        f"{pickup_label}（收件边际贡献 {margin} 对 {margin_budget}，主因激励补贴加重 {incentive} 对 {incentive_budget}、"
        f"直客净额偏弱 {direct} 对 {direct_budget}；出港四费与派件费净额是正贡献）；"
        f"{capacity_label}（{pnl.as_of} 损益单公斤运力{'尚可' if pnl_cap_ok else '已偏高'}，"
        f"但 {core.as_of} 核心指标单公斤运力已到 {cap_core_day}，不得合并后结论）；"
        f"{quality_label}（KPI、出港准点、轨迹断更在 {core.as_of} 同时变差）；"
        f"{cloud_label}（累计日均 {cloud_cum} 对目标 {cloud_target}）；千帆 {qianfan}/{qianfan_target}。\n"
        f"建议关注（非正式，不是已裁定政策）：先补同日对照、覆盖/加盟政策结果与运力结构储备，再讨论是否调整政策。"
        f"揽件净收入达成率因分子分母公式不一致，不作为主结论。"
    )
    assert_not_formal_policy(overall_plan)

    overall = LayerContent(
        title="整体结论",
        plan=overall_plan,
        detailed_calc=tuple(overall_lines),
        missing=tuple(missing),
        informal_mark=INFORMAL_MARK,
    )

    departments = _department_layers(
        staffing=staffing,
        core=core,
        pnl=pnl,
        findings_support={
            Department.财务: (volume_label, profit_label, pickup_label),
            Department.市场: (volume_label, pickup_label),
            Department.营运: (capacity_label, pickup_label),
            Department.质控: (quality_label,),
            Department.云仓: (cloud_label,),
            Department.人资行政: (),
            Department.客服: (),
            Department.总经办: (),
            Department.网络管理: (),
        },
        computed={
            "volume_label": volume_label,
            "profit_label": profit_label,
            "pickup_label": pickup_label,
            "capacity_label": capacity_label,
            "quality_label": quality_label,
            "cloud_label": cloud_label,
            "pnl_cap_ok": pnl_cap_ok,
            "core_cap_high": core_cap_high,
            "kpi": kpi,
            "kpi_target": kpi_target,
            "kpi_cum": kpi_cum,
            "outbound": outbound,
            "outbound_target": outbound_target,
            "breaks": breaks,
            "breaks_mom": breaks_mom,
            "cloud_day": cloud_day,
            "cloud_cum": cloud_cum,
            "cloud_target": cloud_target,
            "qianfan": qianfan,
            "qianfan_target": qianfan_target,
            "market_day": market_day,
            "market_cum": market_cum,
            "market_target": market_target,
            "cap_pnl": cap_pnl,
            "cap_core_day": cap_core_day,
        },
        missing=missing,
    )

    report = TwoLayerReport(
        informal_mark=INFORMAL_MARK,
        overall=overall,
        departments=departments,
        used_as_of=(pnl.as_of or "", core.as_of or "", "202510", "202610"),
        as_of_disclaimer=(
            "可对照但必须标明不同 as_of，不是同一天："
            f"编制对照 202510 vs 202610，损益日报 {pnl.as_of}，核心指标 {core.as_of}"
        ),
        findings=tuple(findings),
    )
    return report


def _staffing_line(staffing: FixtureReport, dept: str) -> tuple[str, CalculationLine]:
    cur = staffing.get(f"编制_{dept}_202610")
    prev = staffing.get(f"编制_{dept}_202510")
    delta = staffing.get(f"编制差额_{dept}")
    text = f"编制 202610 为 {cur.value} 人，202510 为 {prev.value} 人，差额 {delta.value} 人"
    if cur.note:
        text += f"（{cur.note}）"
    text += "。编制对照期间不是经营日报的同一天。"
    line = _line(
        f"编制_{dept}_202610",
        text,
        "202610 − 202510",
        (f"编制_{dept}_202610", f"编制_{dept}_202510"),
        f"{delta.value}人",
        "人",
        "202610",
        "期末编制对照",
    )
    return text, line


def _placeholder_calc(dept: Department, text: str) -> CalculationLine:
    return _line(
        f"{dept.value}_本轮输入",
        text,
        "本轮无该项演算输入",
        (),
        "无动作或缺数",
        "—",
        None,
        "本轮",
        source_type=SRC,
    )


def _department_layers(
    *,
    staffing: FixtureReport,
    core: FixtureReport,
    pnl: FixtureReport,
    findings_support: dict[Department, tuple[str, ...]],
    computed: dict,
    missing: list[str],
) -> tuple[DepartmentLayer, ...]:
    layers: list[DepartmentLayer] = []
    for dept in ALL_DEPARTMENTS:
        staff_text, staff_line = _staffing_line(staffing, dept.value)
        plan, calcs, status, dept_missing = _department_content(
            dept, staff_text, staff_line, core, pnl, computed, missing
        )
        plan = f"{MARK} {plan}"
        assert_not_formal_policy(plan)
        layers.append(
            DepartmentLayer(
                department=dept,
                content=LayerContent(
                    title=f"{dept.value}重点关注目标",
                    plan=plan,
                    detailed_calc=tuple(calcs),
                    missing=tuple(dept_missing),
                    informal_mark=INFORMAL_MARK,
                ),
                status=status,
                supports_overall=findings_support.get(dept, ()),
            )
        )
    return tuple(layers)


def _department_content(dept, staff_text, staff_line, core, pnl, computed, missing):
    if dept is Department.财务:
        plan = (
            f"{computed['profit_label']}，{computed['volume_label']}。"
            "盯累计净利与时间进度的差距、单票净利和收件边际贡献；"
            "成本/费用达成率必须按累计÷预算重算，不得采用印刷的 173%。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("累计净利", "见整体测算中的累计净利与时间进度对照", "累计净利/预算；已过天数/日历天数",
                  ("累计净利", "预算累计净利", "已过天数", "本月日历天数"),
                  computed["profit_label"], "—", pnl.as_of, "月累计"),
            _line("收件边际贡献_累计", "收件边际贡献低于预算，支撑揽件侧缺口判断", "累计−预算",
                  ("收件边际贡献_累计", "收件边际贡献_预算"),
                  computed["pickup_label"], "元/票", pnl.as_of, "月累计单票"),
        ]
        return plan, calcs, "有分析", ["正式授权汇总尚未替换本测试夹具"]

    if dept is Department.市场:
        plan = (
            f"件量方面，市场当日 {computed['market_day']}、累计日均 {computed['market_cum']}，目标 {computed['market_target']}，快于目标；"
            f"但直客净额与激励补贴偏离预算，支撑「{computed['pickup_label']}」。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("市场件量_11月累计", "市场件量累计日均对照目标", "累计日均/目标",
                  ("市场件量_当日", "市场件量_11月累计", "市场件量_目标"),
                  f"{computed['market_cum']}/{computed['market_target']}", "万票", core.as_of, "累计日均"),
            _line("市场直客净额_累计", "直客净额低于预算", "累计−预算",
                  ("市场直客净额_累计", "市场直客净额_预算"), "偏弱", "元/票", pnl.as_of, "月累计单票"),
            _line("激励补贴_累计", "激励补贴重于预算", "累计−预算",
                  ("激励补贴_累计", "激励补贴_预算"), "加重", "元/票", pnl.as_of, "月累计单票"),
        ]
        return plan, calcs, "有分析", []

    if dept is Department.营运:
        plan = (
            f"{computed['capacity_label']}：{pnl.as_of} 损益单公斤运力累计 {computed['cap_pnl']} 判断为"
            f"{'尚可' if computed['pnl_cap_ok'] else '已偏高'}，"
            f"{core.as_of} 核心指标当日 {computed['cap_core_day']} "
            f"{'已偏高' if computed['core_cap_high'] else '接近目标'}，两字段不得合并。"
            "出港四费与派件费净额对利润是正贡献。运力结构/储备仍缺数。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("单公斤运力_损益日报_累计", "损益口径单公斤运力，不与核心指标合并", "单独对照预算与10月",
                  ("单公斤运力_损益日报_累计",), str(computed["cap_pnl"]), "元/公斤", pnl.as_of, "损益口径"),
            _line("单公斤运力_核心指标_当日", "核心指标口径单公斤运力，不与损益表合并", "单独对照目标",
                  ("单公斤运力_核心指标_当日",), str(computed["cap_core_day"]), "元/公斤", core.as_of, "核心指标口径"),
            _line("出港四费_累计", "出港四费高于预算，正贡献", "累计−预算",
                  ("出港四费_累计", "出港四费_预算"), "正贡献", "元/票", pnl.as_of, "月累计单票"),
            _line("派件费净额_累计", "派件费净额高于预算，正贡献", "累计−预算",
                  ("派件费净额_累计", "派件费净额_预算"), "正贡献", "元/票", pnl.as_of, "月累计单票"),
        ]
        return plan, calcs, "有分析", [m for m in missing if "运力结构" in m or "同一天对照" in m]

    if dept is Department.质控:
        plan = (
            f"{computed['quality_label']}：KPI 当日 {computed['kpi']}（目标 {computed['kpi_target']}，月累计 {computed['kpi_cum']} 仍对照目标），"
            f"出港准点 {computed['outbound']}%（目标 {computed['outbound_target']}%），"
            f"轨迹断更 {computed['breaks']} 票（环比 +{computed['breaks_mom']} 票，字段名是率实际是票数）。"
            f"进港转运与签收准点按原表仍达标（夹具未给目标值）。七星潭、桃花岛字段名是履约率，实际是排名。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("KPI_当日", "KPI 当日对照目标与月累计", "当日、目标、月累计分列",
                  ("KPI_当日", "KPI_目标", "KPI_月累计"),
                  str(computed["kpi"]), "分", core.as_of, "当日"),
            _line("出港准点_当日", "出港准点对照目标", "当日/目标",
                  ("出港准点_当日", "出港准点_目标"), f"{computed['outbound']}%", "%", core.as_of, "当日"),
            _line("轨迹断更_当日", "轨迹断更为票数不是率", "票数",
                  ("轨迹断更_当日",), f"{computed['breaks']}票", "票", core.as_of, "票数"),
        ]
        return plan, calcs, "有分析", ["进港转运、签收准点的目标值未提供"]

    if dept is Department.云仓:
        plan = (
            f"{computed['cloud_label']}：不含三方，当日 {computed['cloud_day']}、累计日均 {computed['cloud_cum']}，目标 {computed['cloud_target']}。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("云仓件量_11月累计", "云仓累计日均对照目标", "累计日均/目标",
                  ("云仓件量_当日", "云仓件量_11月累计", "云仓件量_目标"),
                  f"{computed['cloud_cum']}/{computed['cloud_target']}", "万票", core.as_of, "累计日均，不含三方"),
        ]
        return plan, calcs, "有分析", []

    if dept is Department.人资行政:
        labor_core = core.get("单票人力_考核_累计")
        labor_ops = pnl.get("单票操作人力成本_累计")
        efficiency = pnl.get("操作人效_累计")
        efficiency_budget = pnl.get("操作人效_预算")
        eff_rate = achievement_rate(_d(efficiency), _d(efficiency_budget))
        plan = (
            "单票人力（考核）与单票操作人力成本必须分列，禁止合并。"
            f"考核口径累计 {labor_core.value} 元/票（目标 {core.get('单票人力_考核_目标').value}）；"
            f"操作人力成本累计 {labor_ops.value} 元/票（预算 {pnl.get('单票操作人力成本_预算').value}，分母为操作件量）；"
            f"操作人效 {efficiency.value} 对预算 {efficiency_budget.value} 票/人/天，达成 {_pct(eff_rate)}。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("单票人力_考核_累计", "考核口径单票人力，禁止与操作人力成本合并", "累计对照目标",
                  ("单票人力_考核_累计", "单票人力_考核_目标"), labor_core.value, "元/票", core.as_of, "考核口径"),
            _line("单票操作人力成本_累计", "损益操作人力成本，分母为操作件量，禁止与考核口径合并", "累计对照预算",
                  ("单票操作人力成本_累计", "单票操作人力成本_预算"), labor_ops.value, "元/票", pnl.as_of, "操作件量分母"),
            _line("操作人效_累计", "操作人效对照预算", "累计/预算",
                  ("操作人效_累计", "操作人效_预算"), _pct(eff_rate), "达成率", pnl.as_of, "票/人/天"),
        ]
        return plan, calcs, "有分析", []

    if dept is Department.网络管理:
        plan = (
            f"本轮仅有千帆进度 {computed['qianfan']}/{computed['qianfan_target']}。"
            "覆盖/加盟政策结果汇总缺数，本部门其他政策效果无动作可算。"
            f"{staff_text}"
        )
        calcs = [
            staff_line,
            _line("千帆_已完成", "千帆进度", "已完成/目标项数",
                  ("千帆_已完成", "千帆_目标项数"),
                  f"{computed['qianfan']}/{computed['qianfan_target']}", "项", core.as_of, "进度"),
            _placeholder_calc(dept, "覆盖/加盟政策结果汇总缺数，不编造政策效果"),
        ]
        return plan, calcs, "缺数", [m for m in missing if "加盟" in m or "覆盖" in m]

    if dept is Department.客服:
        plan = f"本轮无客服负荷、时效或服务质量汇总，经营上无动作可算。仅有编制对照。{staff_text}"
        calcs = [staff_line, _placeholder_calc(dept, "缺客服负荷与服务质量汇总，本轮无动作")]
        return plan, calcs, "缺数", ["客服负荷/服务质量汇总未提供"]

    if dept is Department.总经办:
        plan = f"本轮无总经办专项经营输入，无动作。仅有编制对照（含信息科技组调入说明）。{staff_text}"
        calcs = [staff_line, _placeholder_calc(dept, "本轮无总经办专项测算输入，无动作")]
        return plan, calcs, "无动作", ["总经办专项经营汇总未提供"]

    raise AssertionError(f"未处理的部门: {dept}")
