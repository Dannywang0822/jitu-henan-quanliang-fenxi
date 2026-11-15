"""录入与上传校验；默认只进测试层。"""

from data_interface.ingest import load_fixture, ingest_records, FixtureReport
from data_interface.recognize import recognize_fields

__all__ = ["load_fixture", "ingest_records", "FixtureReport", "recognize_fields"]
