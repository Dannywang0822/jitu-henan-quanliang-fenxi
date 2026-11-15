"""测试层内核：测算须从夹具算出，方向与已核对判断一致。"""

from __future__ import annotations

import json
from pathlib import Path

from kernel.isolation import list_non_placeholder
from kernel.output import INFORMAL_MARK
from test_layer.run import run


def test_kernel_computes_expected_directions(repo_root: Path):
    result = run(repo_root)
    report = result["report"]
    assert report.informal_mark == INFORMAL_MARK
    assert "件量不慢" in report.findings
    assert "利润偏慢" in report.findings
    assert "缺口主在揽件侧" in report.findings
    assert "运力口径不得合并" in report.findings
    assert "质量当日变差" in report.findings
    assert "云仓件量落后" in report.findings
    # 两表不同日
    assert "2026-11-08" in report.used_as_of
    assert "2026-11-12" in report.used_as_of
    assert "不同" in report.as_of_disclaimer
    # 不得把 173% 当正确结论
    text = report.overall.plan + "\n".join(x.description + x.result for x in report.overall.detailed_calc)
    assert "173.61" in text or "173%" in text or "173.61%" in "".join(x.description for x in report.overall.detailed_calc)
    assert "拒绝" in text or "禁止" in text
    # 正确达成率应出现
    calc_text = "\n".join(x.result + x.description for x in report.overall.detailed_calc)
    assert "26.39%" in calc_text
    assert "26.68%" in calc_text
    # 单公斤运力不得写成合并结论
    assert "不得合并" in report.overall.plan
    assert "0.437" in report.overall.plan
    # 揽件净收入达成率不作主结论
    assert "不一致" in report.overall.plan


def test_all_departments_present_and_missing_marked(repo_root: Path):
    report = run(repo_root)["report"]
    names = [layer.department.value for layer in report.departments]
    assert names == ["客服", "人资行政", "总经办", "市场", "质控", "网络管理", "财务", "营运", "云仓"]
    status = {layer.department.value: layer.status for layer in report.departments}
    assert status["客服"] == "缺数"
    assert status["总经办"] == "无动作"
    assert status["网络管理"] == "缺数"
    assert status["财务"] == "有分析"
    assert status["营运"] == "有分析"
    missing = "\n".join(report.overall.missing)
    assert "同一天对照" in missing
    assert "加盟" in missing or "覆盖" in missing
    assert "运力结构" in missing


def test_outputs_written_and_formal_stays_empty(repo_root: Path):
    result = run(repo_root)
    overall = result["paths"]["overall"].read_text(encoding="utf-8")
    depts = result["paths"]["departments"].read_text(encoding="utf-8")
    payload = json.loads(result["paths"]["json"].read_text(encoding="utf-8"))
    assert INFORMAL_MARK in overall
    assert INFORMAL_MARK in depts
    assert "## 方案" in overall and "## 详细测算" in overall
    assert "## 方案" in depts and "## 详细测算" in depts
    assert payload["informal_mark"] == INFORMAL_MARK
    assert list_non_placeholder(repo_root / "formal_layer") == []
    assert list_non_placeholder(repo_root / "dictionary" / "formal") == []
    # 候选字典有识别结果，正式字典仍空
    candidates = list((repo_root / "dictionary" / "candidates").glob("*.json"))
    assert candidates, "应写入候选字段"


def test_candidates_do_not_contain_detail_or_person_keys(repo_root: Path):
    run(repo_root)
    for path in (repo_root / "dictionary" / "candidates").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for field in data.get("fields", []):
            fid = field["field_id"]
            assert "姓名" not in fid and "负责人" not in fid
            assert "薪酬明细" not in fid
