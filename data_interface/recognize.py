"""字段识别：新字段只进候选字典，不得改写正式定义。"""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from kernel.detail import is_detail_column, reject_detail_column
from kernel.fields import parse_field_id
from kernel.isolation import FormalWriteForbidden, write_text_from_test_layer
from data_interface.ingest import FixtureReport

SHANGHAI = timezone(timedelta(hours=8))


def recognize_fields(
    report: FixtureReport,
    repo_root: Path,
) -> dict:
    root = Path(repo_root)
    formal_dir = root / "dictionary" / "formal"
    candidates_dir = root / "dictionary" / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)

    # 正式目录应保持空（占位除外）
    formal_extra = [
        p for p in formal_dir.iterdir() if p.is_file() and p.name not in {".gitkeep", "README.md"}
    ] if formal_dir.exists() else []
    if formal_extra:
        raise FormalWriteForbidden("正式字典非空且测试识别不得改写正式定义")

    recognized: list[dict] = []
    rejected: list[dict] = []
    for metric in report.metrics:
        try:
            parse_field_id(metric.field_id)
        except Exception as exc:  # noqa: BLE001
            rejected.append({"field_id": metric.field_id, "reason": str(exc)})
            continue
        if is_detail_column(metric.field_id):
            reject_detail_column(metric.field_id)
        recognized.append(
            {
                "field_id": metric.field_id,
                "standard_name": metric.standard_name,
                "unit": metric.unit,
                "caliber": metric.caliber,
                "role": metric.role,
                "source_type_allowed": [report.source_type],
                "as_of_example": metric.as_of,
                "recognition_source": f"测试夹具:{report.report_id}",
                "status": "候选",
                "confidence": "高（已交汇总夹具）",
            }
        )

    payload = {
        "report_id": report.report_id,
        "generated_at": datetime.now(SHANGHAI).isoformat(),
        "informal_mark": "测试，非正式",
        "fields": recognized,
        "rejected": rejected,
    }
    dest = candidates_dir / f"{report.report_id}.json"
    # 只允许写入 candidates，不能写 formal
    write_text_from_test_layer(root, dest, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return payload
