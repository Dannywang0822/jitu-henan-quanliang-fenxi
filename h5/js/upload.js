/**
 * 上传校验（前端第一版，无后端）。
 * 与 kernel/detail.py 对齐：明细列名整份拒绝、不落存；无来源类型拒绝。
 * 照片/PDF 不做识别，不把影像当成已演算数字。
 */
(function (global) {
  "use strict";

  const SOURCE_TYPES = global.H5Const.SOURCE_TYPES;
  const findDetailHint = global.H5Const.findDetailHint;

  class UploadRejected extends Error {
    constructor(message) {
      super(message);
      this.name = "UploadRejected";
    }
  }

  function reject(message) {
    throw new UploadRejected(message);
  }

  function checkFieldName(name, where) {
    const hint = findDetailHint(name);
    if (hint) {
      reject(
        "已拒绝：在" +
          where +
          "中发现明细列名「" +
          String(name).trim() +
          "」（命中「" +
          hint +
          "」）。按内核规则，明细列整份拒绝，不保存任何取值。请只上传汇总。"
      );
    }
  }

  function checkFilename(filename) {
    if (!filename) return;
    checkFieldName(filename, "文件名");
  }

  function collectJsonKeys(value, keys) {
    if (value == null) return;
    if (Array.isArray(value)) {
      value.forEach((item) => collectJsonKeys(item, keys));
      return;
    }
    if (typeof value === "object") {
      Object.keys(value).forEach((k) => {
        keys.push(k);
        collectJsonKeys(value[k], keys);
      });
    }
  }

  function inspectJsonObject(obj) {
    const keys = [];
    collectJsonKeys(obj, keys);
    keys.forEach((k) => checkFieldName(k, "JSON 字段名"));
    return obj;
  }

  function parseCsvText(text) {
    let src = String(text || "");
    if (src.charCodeAt(0) === 0xfeff) src = src.slice(1);
    const rows = [];
    let row = [];
    let cell = "";
    let i = 0;
    let inQuotes = false;
    while (i < src.length) {
      const ch = src[i];
      if (inQuotes) {
        if (ch === '"') {
          if (src[i + 1] === '"') {
            cell += '"';
            i += 2;
            continue;
          }
          inQuotes = false;
          i += 1;
          continue;
        }
        cell += ch;
        i += 1;
        continue;
      }
      if (ch === '"') {
        inQuotes = true;
        i += 1;
        continue;
      }
      if (ch === "," || ch === "\t" || ch === ";") {
        row.push(cell);
        cell = "";
        i += 1;
        continue;
      }
      if (ch === "\n") {
        row.push(cell);
        rows.push(row);
        row = [];
        cell = "";
        i += 1;
        continue;
      }
      if (ch === "\r") {
        i += 1;
        continue;
      }
      cell += ch;
      i += 1;
    }
    if (cell.length || row.length) {
      row.push(cell);
      rows.push(row);
    }
    return rows.filter((r) => r.some((c) => String(c).trim() !== ""));
  }

  function inspectCsv(text) {
    const rows = parseCsvText(text);
    if (!rows.length) {
      reject("已拒绝：表格是空的，没有可校验的字段名。");
    }
    const headers = rows[0].map((h) => String(h).trim()).filter(Boolean);
    if (!headers.length) {
      reject("已拒绝：无法读取表格表头。请确认第一行是字段名。");
    }
    headers.forEach((h) => checkFieldName(h, "表格表头"));
    const records = [];
    for (let r = 1; r < rows.length; r += 1) {
      const rec = {};
      headers.forEach((h, idx) => {
        rec[h] = rows[r][idx] == null ? "" : rows[r][idx];
      });
      records.push(rec);
    }
    return { headers, records };
  }

  function decodeUtf8(bytes) {
    return new TextDecoder("utf-8").decode(bytes);
  }

  async function inflateRaw(bytes) {
    if (typeof DecompressionStream !== "function") {
      reject("当前浏览器无法读取 xlsx（缺少解压能力）。请改为上传 CSV 或 JSON。");
    }
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    const buf = await new Response(stream).arrayBuffer();
    return new Uint8Array(buf);
  }

  async function unzipXlsx(arrayBuffer) {
    const bytes = new Uint8Array(arrayBuffer);
    const view = new DataView(arrayBuffer);
    let eocd = bytes.length - 22;
    while (eocd >= 0 && view.getUint32(eocd, true) !== 0x06054b50) {
      eocd -= 1;
    }
    if (eocd < 0) {
      reject("已拒绝：无法将文件作为 xlsx 读取。请改为 CSV 或 JSON，或确认文件未损坏。");
    }
    const cdEntries = view.getUint16(eocd + 10, true);
    const cdOffset = view.getUint32(eocd + 16, true);
    const files = {};
    let p = cdOffset;
    for (let i = 0; i < cdEntries; i += 1) {
      if (view.getUint32(p, true) !== 0x02014b50) {
        reject("已拒绝：xlsx 内部目录无法解析。请改为上传 CSV 或 JSON。");
      }
      const method = view.getUint16(p + 10, true);
      const compSize = view.getUint32(p + 20, true);
      const nameLen = view.getUint16(p + 28, true);
      const extraLen = view.getUint16(p + 30, true);
      const commentLen = view.getUint16(p + 32, true);
      const localOff = view.getUint32(p + 42, true);
      const name = decodeUtf8(bytes.slice(p + 46, p + 46 + nameLen));
      const localNameLen = view.getUint16(localOff + 26, true);
      const localExtraLen = view.getUint16(localOff + 28, true);
      const dataStart = localOff + 30 + localNameLen + localExtraLen;
      const compressed = bytes.slice(dataStart, dataStart + compSize);
      let raw;
      if (method === 0) raw = compressed;
      else if (method === 8) raw = await inflateRaw(compressed);
      else reject("已拒绝：xlsx 压缩方式不受支持。请改为上传 CSV 或 JSON。");
      files[name] = raw;
      p += 46 + nameLen + extraLen + commentLen;
    }
    return files;
  }

  function xmlDoc(bytes) {
    const text = decodeUtf8(bytes);
    return new DOMParser().parseFromString(text, "application/xml");
  }

  function sharedStrings(files) {
    const entry = Object.keys(files).find((k) => k.toLowerCase() === "xl/sharedstrings.xml");
    if (!entry) return [];
    const doc = xmlDoc(files[entry]);
    const sis = Array.from(doc.getElementsByTagName("si"));
    return sis.map((si) => Array.from(si.getElementsByTagName("t")).map((t) => t.textContent || "").join(""));
  }

  function headerCellsFromSheet(doc, strings) {
    const rows = Array.from(doc.getElementsByTagName("row")).slice(0, 5);
    const names = [];
    rows.forEach((row, rowIdx) => {
      const cells = Array.from(row.getElementsByTagName("c"));
      cells.forEach((c) => {
        const type = c.getAttribute("t") || "";
        let value = "";
        if (type === "s") {
          const v = c.getElementsByTagName("v")[0];
          const idx = v ? parseInt(v.textContent || "", 10) : NaN;
          value = Number.isFinite(idx) ? strings[idx] || "" : "";
        } else if (type === "inlineStr" || type === "str") {
          value = Array.from(c.getElementsByTagName("t")).map((t) => t.textContent || "").join("");
          if (!value) {
            const v = c.getElementsByTagName("v")[0];
            value = v ? v.textContent || "" : "";
          }
        } else if (rowIdx === 0) {
          const v = c.getElementsByTagName("v")[0];
          value = v ? v.textContent || "" : "";
        }
        const trimmed = String(value).trim();
        if (trimmed) names.push(trimmed);
      });
    });
    return names;
  }

  async function inspectXlsx(arrayBuffer) {
    const files = await unzipXlsx(arrayBuffer);
    const strings = sharedStrings(files);
    const sheetKeys = Object.keys(files).filter((k) => /xl\/worksheets\/sheet\d+\.xml$/i.test(k));
    if (!sheetKeys.length) {
      reject("已拒绝：xlsx 中没有找到工作表，无法校验表头。请改为 CSV 或 JSON。");
    }
    const headers = [];
    sheetKeys.forEach((key) => {
      const doc = xmlDoc(files[key]);
      headerCellsFromSheet(doc, strings).forEach((name) => headers.push(name));
    });
    if (!headers.length) {
      reject("已拒绝：无法读取 Excel 表头。请改为 CSV 或 JSON。");
    }
    headers.forEach((h) => checkFieldName(h, "Excel 表头"));
    return { headers: unique(headers) };
  }

  function unique(arr) {
    const seen = new Set();
    const out = [];
    arr.forEach((x) => {
      if (!seen.has(x)) {
        seen.add(x);
        out.push(x);
      }
    });
    return out;
  }

  function kindFromFile(file) {
    const name = (file && file.name) || "";
    const lower = name.toLowerCase();
    const type = (file && file.type) || "";
    if (type === "application/json" || lower.endsWith(".json")) return "json";
    if (type === "text/csv" || lower.endsWith(".csv") || lower.endsWith(".tsv")) return "csv";
    if (
      type === "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
      lower.endsWith(".xlsx")
    ) {
      return "xlsx";
    }
    if (type === "application/vnd.ms-excel" || lower.endsWith(".xls")) return "xls";
    if (type === "application/pdf" || lower.endsWith(".pdf")) return "pdf";
    if (type.startsWith("image/") || /\.(png|jpe?g|gif|webp|bmp|heic|heif)$/i.test(lower)) return "image";
    return "unknown";
  }

  function parsePasted(text) {
    const raw = String(text || "").trim();
    if (!raw) return null;
    if (raw.startsWith("{") || raw.startsWith("[")) {
      let obj;
      try {
        obj = JSON.parse(raw);
      } catch (err) {
        reject("已拒绝：粘贴内容不是合法 JSON。请检查格式后再提交。");
      }
      inspectJsonObject(obj);
      return { mode: "json", data: obj };
    }
    const names = raw
      .split(/[\n,，、\t;；]+/)
      .map((s) => s.trim())
      .filter(Boolean);
    names.forEach((n) => checkFieldName(n, "粘贴的字段名"));
    return { mode: "fields", fields: names };
  }

  function nowIsoShanghai() {
    const now = new Date();
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
    }).formatToParts(now);
    const get = (t) => (parts.find((p) => p.type === t) || {}).value;
    return (
      get("year") +
      "-" +
      get("month") +
      "-" +
      get("day") +
      "T" +
      get("hour") +
      ":" +
      get("minute") +
      ":" +
      get("second") +
      "+08:00"
    );
  }

  async function readText(file) {
    return await file.text();
  }

  async function validateUpload({ sourceType, file, pastedText }) {
    const picked = String(sourceType || "").trim();
    if (!SOURCE_TYPES.includes(picked)) {
      reject("已拒绝：必须先选择来源类型（假设 / 公开来源 / 合规授权汇总 / Danny提供的汇总）。未选择来源的内容不会被保留。");
    }
    const pasted = String(pastedText || "").trim();
    if (!file && !pasted) {
      reject("已拒绝：请选择文件、拍照，或粘贴汇总 JSON / 字段名。");
    }

    const pkg = {
      informal_mark: "测试，非正式",
      layer: "test_layer",
      status: "待测上传",
      notice: "非正式，尚未演算",
      source_type: picked,
      created_at: nowIsoShanghai(),
      drop_in: "test_layer/inbox/",
      not_for: "formal_layer",
      ocr_or_calc: false,
    };

    if (file) {
      checkFilename(file.name);
      const kind = kindFromFile(file);
      pkg.filename = file.name;
      pkg.file_kind = kind;
      pkg.file_size_bytes = file.size;

      if (kind === "json") {
        let obj;
        try {
          obj = JSON.parse(await readText(file));
        } catch (err) {
          reject("已拒绝：JSON 无法解析。未保存文件内容。");
        }
        inspectJsonObject(obj);
        if (obj && typeof obj === "object" && !Array.isArray(obj) && obj["来源类型"]) {
          const inner = String(obj["来源类型"]).trim();
          if (!SOURCE_TYPES.includes(inner)) {
            reject("已拒绝：文件中的来源类型不在允许名单内。未保存文件内容。");
          }
          pkg.file_declared_source_type = inner;
        }
        pkg.fields = obj;
      } else if (kind === "csv") {
        const parsed = inspectCsv(await readText(file));
        pkg.fields = { headers: parsed.headers, records: parsed.records };
      } else if (kind === "xlsx") {
        const parsed = await inspectXlsx(await file.arrayBuffer());
        pkg.fields = { headers: parsed.headers };
        pkg.note = "第一版只校验 Excel 表头是否为明细列，不把单元格演算为正式数字。";
      } else if (kind === "xls") {
        reject("已拒绝：第一版不能可靠读取旧版 .xls 表头。请另存为 .xlsx 或导出为 CSV / JSON。未保存文件内容。");
      } else if (kind === "image" || kind === "pdf") {
        pkg.pending_media = {
          filename: file.name,
          mime: file.type || "",
          size_bytes: file.size,
        };
        pkg.note =
          "第一版不能把照片或 PDF 自动识别成正式数字。本包仅为待测上传，非正式，尚未演算。请将原文件与本 JSON 一并手工放入 test_layer/inbox/，不要写入 formal_layer/。";
      } else {
        reject("已拒绝：不支持的文件类型。请上传 JSON、CSV、xlsx、图片或 PDF。未保存文件内容。");
      }
    }

    if (pasted) {
      const parsedPaste = parsePasted(pasted);
      pkg.pasted = parsedPaste;
    }

    return pkg;
  }

  function packageFilename(pkg) {
    const stamp = String(pkg.created_at || "").replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
    return "test-layer-pending-" + (stamp || "pack") + ".json";
  }

  global.H5Upload = {
    UploadRejected,
    validateUpload,
    packageFilename,
    kindFromFile,
    inspectJsonObject,
    inspectCsv,
    parsePasted,
  };
})(window);
