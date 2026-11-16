"""PostgreSQL 的本地双：sqlite 内存库。不要求真实 Postgres。"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from kernel.promotion import PromotionDenied
from pipeline.errors import AutoPromotionForbidden, TableTooLarge
from pipeline.permit import PROMOTION_PERMIT_TOKEN
from warehouse.rows import WideRow

MAX_TEST_ROWS = 32

_TEST_COLUMNS = (
    "row_id",
    "source_file_id",
    "department",
    "field_id",
    "value_text",
    "unit",
    "caliber",
    "as_of",
    "period_grain",
    "period_key",
    "source_type",
    "informal_mark",
    "layer",
)


class ExplicitPromotion:
    """只有审批模块在 Danny 点头后能构造。决定记录本身不是晋升许可。"""

    def __init__(self, subject_id: str, token: object):
        if token is not PROMOTION_PERMIT_TOKEN:
            raise AutoPromotionForbidden("晋升许可只能由审批模块在 Danny 点头后签发，不得自动晋升")
        if not str(subject_id).strip():
            raise PromotionDenied("晋升许可必须指向明确的包")
        self.subject_id = subject_id
        self.auto = False


class LocalWarehouse:
    def __init__(self, schema_sql: str):
        self.backend = "sqlite-memory"
        self._conn = sqlite3.connect(":memory:")
        self._conn.executescript(schema_sql)
        self._formal_history: list[list[tuple]] = []

    @classmethod
    def open_memory(cls, schema_path: Path | None = None) -> "LocalWarehouse":
        path = schema_path or Path(__file__).with_name("schema_sqlite.sql")
        return cls(path.read_text(encoding="utf-8"))

    def close(self) -> None:
        self._conn.close()

    def test_count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM test_wide").fetchone()[0])

    def formal_count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM formal_wide").fetchone()[0])

    def insert_test_rows(self, rows: list[WideRow] | tuple[WideRow, ...]) -> None:
        incoming = list(rows)
        if self.test_count() + len(incoming) > MAX_TEST_ROWS:
            raise TableTooLarge(f"测试阶段宽表最多 {MAX_TEST_ROWS} 行")
        for row in incoming:
            if row.layer != "test" or row.informal_mark != "测试，非正式":
                raise AutoPromotionForbidden("测试层写入不能改成正式层")
            self._conn.execute(
                f"INSERT INTO test_wide ({', '.join(_TEST_COLUMNS)}) VALUES ({', '.join('?' for _ in _TEST_COLUMNS)})",
                (
                    row.row_id,
                    row.source_file_id,
                    row.department,
                    row.field_id,
                    row.value,
                    row.unit,
                    row.caliber,
                    row.as_of,
                    row.period_grain,
                    row.period_key,
                    row.source_type,
                    row.informal_mark,
                    row.layer,
                ),
            )
        self._conn.commit()

    def test_rows(self) -> tuple[WideRow, ...]:
        found = self._conn.execute(
            f"SELECT {', '.join(_TEST_COLUMNS)} FROM test_wide ORDER BY row_id"
        ).fetchall()
        rows: list[WideRow] = []
        for item in found:
            payload = dict(zip(_TEST_COLUMNS, item, strict=True))
            payload["value"] = payload.pop("value_text")
            rows.append(WideRow.model_validate(payload))
        return tuple(rows)

    def stored_values(self) -> tuple[str, ...]:
        test_values = self._conn.execute("SELECT value_text FROM test_wide").fetchall()
        formal_values = self._conn.execute("SELECT value_text FROM formal_wide").fetchall()
        return tuple(row[0] for row in test_values + formal_values)

    def insert_formal_directly(self, *_args, **_kwargs) -> None:
        raise AutoPromotionForbidden("不得直接写入正式宽表")

    def auto_promote(self, *_args, **_kwargs) -> None:
        raise AutoPromotionForbidden("不得自动晋升正式层")

    def promote(self, rows: list[WideRow] | tuple[WideRow, ...], permit: ExplicitPromotion) -> None:
        if not isinstance(permit, ExplicitPromotion) or permit.auto is not False:
            raise AutoPromotionForbidden("晋升许可必须是单独签发的整包许可")
        if not permit.subject_id.strip():
            raise PromotionDenied("晋升许可必须指向明确的包")
        self._formal_history.append(self._formal_tuples())
        self._conn.execute("DELETE FROM formal_wide")
        for row in rows:
            self._conn.execute(
                """
                INSERT INTO formal_wide (
                  row_id, source_file_id, department, field_id, value_text, unit, caliber,
                  as_of, period_grain, period_key, source_type, formal_mark, layer
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '正式', 'formal')
                """,
                (
                    row.row_id,
                    row.source_file_id,
                    row.department,
                    row.field_id,
                    row.value,
                    row.unit,
                    row.caliber,
                    row.as_of,
                    row.period_grain,
                    row.period_key,
                    row.source_type,
                ),
            )
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.execute("DELETE FROM formal_wide")
        if self._formal_history:
            previous = self._formal_history.pop()
            for item in previous:
                self._conn.execute(
                    """
                    INSERT INTO formal_wide (
                      row_id, source_file_id, department, field_id, value_text, unit, caliber,
                      as_of, period_grain, period_key, source_type, formal_mark, layer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    item,
                )
        self._conn.commit()

    def _formal_tuples(self) -> list[tuple]:
        return list(
            self._conn.execute(
                """
                SELECT row_id, source_file_id, department, field_id, value_text, unit, caliber,
                       as_of, period_grain, period_key, source_type, formal_mark, layer
                FROM formal_wide ORDER BY row_id
                """
            ).fetchall()
        )
