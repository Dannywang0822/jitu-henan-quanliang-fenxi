"""把已通过字典的文件合并成测试层宽表行。"""

from __future__ import annotations

from ingest.dictionary import ConsistencyReport, DictField, require_exact
from warehouse.calendar import period_key_for
from warehouse.rows import WideRow


def build_wide_rows(upload, dictionary: tuple[DictField, ...], report: ConsistencyReport) -> list[WideRow]:
    require_exact(report)
    by_id = {field.field_id: field for field in dictionary}
    rows: list[WideRow] = []
    for data in upload.rows:
        for header, field_id in report.bindings:
            field = by_id[field_id]
            if header not in data.values:
                raise ValueError(f"{upload.file_id} 缺少 {header} 的值，不能写入宽表")
            grain = field.grain
            rows.append(
                WideRow(
                    row_id=f"{upload.file_id}:{data.as_of}:{field.field_id}",
                    source_file_id=upload.file_id,
                    department=upload.department,
                    field_id=field.field_id,
                    value=data.values[header],
                    unit=field.unit,
                    caliber=field.caliber,
                    as_of=data.as_of,
                    period_grain=grain,
                    period_key=period_key_for(data.as_of, grain),
                    source_type=upload.source_type,
                )
            )
    if not rows:
        raise ValueError("完全一致的文件必须至少写出一行宽表")
    return rows
