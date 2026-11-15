/**
 * 解析测试层 Markdown 的「详细测算」小节。
 * 只拆分结构，正文逐字保留，不改写数字。
 */
(function (global) {
  "use strict";

  const FIELD_KEYS = ["说明", "公式", "输入", "结果", "来源类型", "as_of", "口径"];

  function splitByHeading(text, re) {
    const lines = text.replace(/\r\n/g, "\n").split("\n");
    const parts = [];
    let current = null;
    for (const line of lines) {
      const m = line.match(re);
      if (m) {
        if (current) parts.push(current);
        current = { title: m[1].trim(), body: [] };
      } else if (current) {
        current.body.push(line);
      }
    }
    if (current) parts.push(current);
    return parts;
  }

  function parseMetricBullets(bodyLines) {
    const metric = {
      说明: "",
      公式: "",
      输入: "",
      结果: "",
      来源类型: "",
      as_of: "",
      口径: "",
    };
    let currentKey = null;
    for (const raw of bodyLines) {
      const line = raw.trimEnd();
      const trimmed = line.trim();
      if (!trimmed) continue;
      const bullet = trimmed.match(/^- ([^：:]+)[：:](.*)$/);
      if (bullet) {
        const key = bullet[1].trim();
        const rest = bullet[2].trim();
        if (FIELD_KEYS.includes(key)) {
          currentKey = key;
          metric[key] = rest;
          continue;
        }
      }
      if (currentKey) {
        metric[currentKey] = (metric[currentKey] ? metric[currentKey] + "\n" : "") + trimmed.replace(/^- /, "");
      }
    }
    return metric;
  }

  function parseDetailedMetrics(markdown) {
    const sectionMatch = markdown.match(/## 详细测算\s*\n([\s\S]*?)(?=\n## |\s*$)/);
    const block = sectionMatch ? sectionMatch[1] : "";
    if (!block.trim()) return [];
    return splitByHeading(block, /^###\s+(.+)$/).map((part) => {
      const fields = parseMetricBullets(part.body);
      return { title: part.title, ...fields };
    });
  }

  function parseOverallMarkdown(markdown) {
    return { metrics: parseDetailedMetrics(markdown) };
  }

  function parseDepartmentMarkdown(markdown) {
    const parts = splitByHeading(markdown, /^# (?!各部门)(.+)$/);
    const byName = {};
    for (const part of parts) {
      const heading = part.title;
      const statusMatch = heading.match(/^(.+?)（状态：(.+?)）$/);
      const name = statusMatch ? statusMatch[1].trim() : heading.trim();
      const statusFromMd = statusMatch ? statusMatch[2].trim() : "";
      const body = part.body.join("\n");
      const supportMatch = body.match(/支撑的整体判断：([^\n]+)/);
      const metrics = parseDetailedMetrics(body);
      byName[name] = {
        department: name,
        statusFromMd,
        supportsFromMd: supportMatch
          ? supportMatch[1].split("、").map((s) => s.trim()).filter(Boolean)
          : [],
        metrics,
      };
    }
    return byName;
  }

  global.H5Parse = {
    parseOverallMarkdown,
    parseDepartmentMarkdown,
    parseDetailedMetrics,
  };
})(window);
