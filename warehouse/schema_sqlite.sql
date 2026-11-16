-- 本地双：sqlite 内存库。checks 只加载本文件，不连接 PostgreSQL 云实例。
-- 测试层与正式层分表。正式表默认空，没有从测试表自动复制的触发器。

CREATE TABLE test_wide (
  row_id TEXT PRIMARY KEY,
  source_file_id TEXT NOT NULL CHECK (length(source_file_id) > 0),
  department TEXT NOT NULL CHECK (length(department) > 0),
  field_id TEXT NOT NULL,
  value_text TEXT NOT NULL,
  unit TEXT NOT NULL,
  caliber TEXT NOT NULL,
  as_of TEXT NOT NULL,
  period_grain TEXT NOT NULL CHECK (period_grain IN ('day', 'week', 'month')),
  period_key TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('假设', '公开来源', '合规授权汇总', 'Danny提供的汇总')),
  informal_mark TEXT NOT NULL CHECK (informal_mark = '测试，非正式'),
  layer TEXT NOT NULL CHECK (layer = 'test')
);

CREATE TABLE formal_wide (
  row_id TEXT PRIMARY KEY,
  source_file_id TEXT NOT NULL CHECK (length(source_file_id) > 0),
  department TEXT NOT NULL CHECK (length(department) > 0),
  field_id TEXT NOT NULL,
  value_text TEXT NOT NULL,
  unit TEXT NOT NULL,
  caliber TEXT NOT NULL,
  as_of TEXT NOT NULL,
  period_grain TEXT NOT NULL CHECK (period_grain IN ('day', 'week', 'month')),
  period_key TEXT NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('假设', '公开来源', '合规授权汇总', 'Danny提供的汇总')),
  formal_mark TEXT NOT NULL CHECK (formal_mark = '正式'),
  layer TEXT NOT NULL CHECK (layer = 'formal')
);
