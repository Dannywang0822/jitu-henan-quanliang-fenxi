"""测试层入口：读夹具 → 校验识别 → 两层非正式输出。不写正式层。"""

from __future__ import annotations

import json
from pathlib import Path

from data_interface.ingest import load_fixture
from data_interface.recognize import recognize_fields
from kernel.analysis import analyze
from kernel.isolation import FormalWriteForbidden, list_non_placeholder, write_text_from_test_layer
from kernel.output import INFORMAL_MARK
from test_layer.render import render_departments, render_overall

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "test_layer" / "outputs"


def run(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root else REPO_ROOT
    staffing = load_fixture(root / "fixtures" / "staffing_202510_202610.json")
    core = load_fixture(root / "fixtures" / "core_metrics_2026-11-12.json")
    pnl = load_fixture(root / "fixtures" / "pnl_2026-11-08.json")

    recognition = {
        "staffing": recognize_fields(staffing, root),
        "core_metrics": recognize_fields(core, root),
        "pnl": recognize_fields(pnl, root),
    }

    report = analyze(staffing, core, pnl)

    out_dir = root / "test_layer" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    overall_path = out_dir / "整体结论.md"
    dept_path = out_dir / "各部门重点关注目标.md"
    json_path = out_dir / "test_report.json"

    write_text_from_test_layer(root, overall_path, render_overall(report))
    write_text_from_test_layer(root, dept_path, render_departments(report.departments))
    payload = {
        "informal_mark": report.informal_mark,
        "used_as_of": list(report.used_as_of),
        "as_of_disclaimer": report.as_of_disclaimer,
        "findings": list(report.findings),
        "overall_plan": report.overall.plan,
        "overall_missing": list(report.overall.missing),
        "departments": [
            {
                "department": layer.department.value,
                "status": layer.status,
                "supports_overall": list(layer.supports_overall),
                "plan": layer.content.plan,
                "missing": list(layer.content.missing),
            }
            for layer in report.departments
        ],
        "output_paths": [str(overall_path.relative_to(root)), str(dept_path.relative_to(root))],
    }
    write_text_from_test_layer(root, json_path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    formal_extra = list_non_placeholder(root / "formal_layer")
    formal_dict = list_non_placeholder(root / "dictionary" / "formal")
    if formal_extra or formal_dict:
        raise FormalWriteForbidden(
            f"测试层运行后正式层或正式字典非空: {formal_extra} / {formal_dict}"
        )
    if INFORMAL_MARK not in overall_path.read_text(encoding="utf-8"):
        raise RuntimeError("整体结论未标明测试，非正式")

    return {
        "report": report,
        "recognition": recognition,
        "paths": {
            "overall": overall_path,
            "departments": dept_path,
            "json": json_path,
        },
    }


def main() -> None:
    result = run()
    print("[test_layer] 标记:", INFORMAL_MARK)
    print("[test_layer] 发现:", "、".join(result["report"].findings))
    for key, path in result["paths"].items():
        print(f"[test_layer] {key}: {path}")


if __name__ == "__main__":
    main()
