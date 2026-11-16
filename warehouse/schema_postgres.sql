-- 目标库：PostgreSQL。本文件是 schema 设计，不在仓库检查里执行，也不连接云实例。
-- 测试层与正式层分 schema。原始文件不在本库，在对象存储。
-- 不建文档集合。

CREATE SCHEMA IF NOT EXISTS mgmt_test;
CREATE SCHEMA IF NOT EXISTS mgmt_formal;

CREATE TABLE mgmt_test.wide_row (
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

CREATE TABLE mgmt_formal.wide_row (
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
