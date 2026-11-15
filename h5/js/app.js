/**
 * 测试层 H5 入口：三个主界面、渲染测试层产出、本地上传校验。
 */
(function () {
  "use strict";

  const mainEl = document.getElementById("main");
  const disclaimerEl = document.getElementById("asof-disclaimer");
  const bannerEl = document.getElementById("informal-banner");
  const tabLinks = Array.from(document.querySelectorAll(".tabbar a"));

  const state = {
    report: null,
    overallMd: "",
    deptMd: "",
    overallMetrics: [],
    deptMetrics: {},
    error: "",
    lastPackage: null,
    uploadMsg: null,
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function route() {
    const hash = (location.hash || "#/overall").replace(/^#/, "");
    const parts = hash.split("/").filter(Boolean);
    const page = parts[0] || "overall";
    if (page === "departments" && parts[1]) {
      return { name: "department", dept: decodeURIComponent(parts[1]) };
    }
    if (page === "departments") return { name: "departments" };
    if (page === "upload") return { name: "upload" };
    return { name: "overall" };
  }

  function setActiveTab(name) {
    const key = name === "department" ? "departments" : name;
    tabLinks.forEach((a) => {
      a.classList.toggle("active", a.dataset.page === key);
    });
  }

  function statusClass(status) {
    if (status === "有分析") return "chip chip-ok";
    if (status === "缺数") return "chip chip-miss";
    return "chip chip-idle";
  }

  function renderDisclaimer() {
    const report = state.report;
    if (!report) {
      disclaimerEl.innerHTML = "<strong>不同 as_of 说明：</strong>正在载入。不同日期报表不得视为同一天。";
      return;
    }
    if (bannerEl && report.informal_mark) {
      bannerEl.textContent = report.informal_mark;
    }
    const chips = (report.used_as_of || [])
      .map((d) => '<span class="chip chip-asof">as_of ' + esc(d) + "</span>")
      .join("");
    disclaimerEl.innerHTML =
      "<strong>不同 as_of 说明：</strong>" +
      esc(report.as_of_disclaimer) +
      (chips ? '<div class="asof-chips">' + chips + "</div>" : "");
  }

  function metricCard(m) {
    const title = esc(m.title || "");
    const result = esc(m["结果"] || "");
    const source = esc(m["来源类型"] || "");
    const asof = esc(m.as_of || "");
    const rows = ["说明", "公式", "输入", "口径"]
      .filter((k) => m[k])
      .map((k) => '<div class="kv"><span class="kv-k">' + esc(k) + '</span><span class="kv-v">' + esc(m[k]) + "</span></div>")
      .join("");
    return (
      '<details class="metric">' +
      "<summary><div class=\"metric-head\">" +
      '<div class="metric-title">' +
      title +
      "</div>" +
      (result ? '<div class="metric-result">' + result + "</div>" : "") +
      '<div class="metric-meta">' +
      (source ? '<span class="chip chip-source">来源类型：' + source + "</span>" : "") +
      (asof ? '<span class="chip chip-asof">as_of：' + asof + "</span>" : "") +
      "</div></div></summary>" +
      '<div class="metric-body">' +
      rows +
      "</div></details>"
    );
  }

  function renderOverall() {
    const r = state.report;
    const findings = (r.findings || [])
      .map((f) => '<span class="finding">' + esc(f) + "</span>")
      .join("");
    const missing = (r.overall_missing || [])
      .map((x) => "<li>" + esc(x) + "</li>")
      .join("");
    const metrics = state.overallMetrics.map(metricCard).join("");
    mainEl.innerHTML =
      '<h1 class="page-title">整体结论</h1>' +
      '<div class="section-title">发现</div>' +
      '<div class="card"><div class="findings">' +
      findings +
      "</div></div>" +
      '<div class="section-title">方案</div>' +
      '<div class="card"><div class="plan-text">' +
      esc(r.overall_plan) +
      "</div></div>" +
      '<div class="section-title">缺数与不确定项</div>' +
      '<div class="card"><ul class="missing-list">' +
      missing +
      "</ul></div>" +
      '<div class="section-title">详细测算（点击展开）</div>' +
      (metrics || '<p class="muted">本篇没有可展开的详细测算。</p>');
  }

  function renderDepartments() {
    const r = state.report;
    const order = globalThis.H5Const.DEPT_ORDER;
    const byName = {};
    (r.departments || []).forEach((d) => {
      byName[d.department] = d;
    });
    const rows = order
      .map((name) => {
        const d = byName[name];
        if (!d) return "";
        const extra =
          name === "营运"
            ? '<div class="dept-note">运力归本部门，不单列运力部</div>'
            : "";
        return (
          '<a class="dept-row" href="#/departments/' +
          encodeURIComponent(name) +
          '"><div><div class="dept-name">' +
          esc(name) +
          "</div>" +
          extra +
          '</div><div class="dept-right"><span class="' +
          statusClass(d.status) +
          '">' +
          esc(d.status) +
          '</span><span class="chevron">›</span></div></a>'
        );
      })
      .join("");
    mainEl.innerHTML =
      '<h1 class="page-title">各部门重点关注目标</h1>' +
      '<p class="muted" style="margin-top:0">九个部门同一套拆分。点进查看该部门方案、缺数和详细测算。</p>' +
      '<div class="dept-list">' +
      rows +
      "</div>";
  }

  function renderDepartment(name) {
    const r = state.report;
    const d = (r.departments || []).find((x) => x.department === name);
    if (!d) {
      mainEl.innerHTML =
        '<a class="back-link" href="#/departments">← 返回各部门</a>' +
        '<h1 class="page-title">未找到该部门</h1>';
      return;
    }
    const supports = (d.supports_overall || [])
      .map((s) => '<span class="chip chip-source">' + esc(s) + "</span>")
      .join("");
    const missing = (d.missing || []).map((x) => "<li>" + esc(x) + "</li>").join("");
    const md = state.deptMetrics[name] || { metrics: [] };
    const metrics = (md.metrics || []).map(metricCard).join("");
    mainEl.innerHTML =
      '<a class="back-link" href="#/departments">← 返回各部门</a>' +
      '<h1 class="page-title">' +
      esc(d.department) +
      "</h1>" +
      '<div style="margin-bottom:10px"><span class="' +
      statusClass(d.status) +
      '">' +
      esc(d.status) +
      "</span></div>" +
      (supports ? '<div class="section-title">支撑的整体判断</div><div class="supports">' + supports + "</div>" : "") +
      (d.department === "营运" ? '<p class="muted">运力归营运部，不单列运力部。</p>' : "") +
      '<div class="section-title">方案</div>' +
      '<div class="card"><div class="plan-text">' +
      esc(d.plan) +
      "</div></div>" +
      '<div class="section-title">缺数与不确定项</div>' +
      '<div class="card">' +
      (missing ? '<ul class="missing-list">' + missing + "</ul>" : '<p class="muted">本部门本轮无另列缺数项。</p>') +
      "</div>" +
      '<div class="section-title">详细测算（点击展开）</div>' +
      (metrics || '<p class="muted">本部门没有可展开的详细测算。</p>');
  }

  function renderUpload() {
    const sources = globalThis.H5Const.SOURCE_TYPES.map((s) => {
      return (
        '<label><input type="radio" name="sourceType" value="' +
        esc(s) +
        '" /> ' +
        esc(s) +
        "</label>"
      );
    }).join("");
    const msg = state.uploadMsg
      ? '<div class="msg ' +
        (state.uploadMsg.ok ? "msg-ok" : "msg-error") +
        '">' +
        esc(state.uploadMsg.text) +
        "</div>"
      : "";
    const pack = state.lastPackage
      ? '<div class="actions" style="margin-top:8px">' +
        '<button class="btn btn-primary" type="button" id="btn-download">下载测试层待处理包</button>' +
        "</div>" +
        '<p class="muted">可将该 JSON 手工放到仓库的 test_layer/inbox/，供后续测试层处理。不要写入 formal_layer/。</p>'
      : "";
    mainEl.innerHTML =
      '<h1 class="page-title">上传录入</h1>' +
      '<div class="card"><p>只收汇总。电脑可选文件，手机可拍照。必须先选来源类型，否则整份拒绝且不保留内容。</p>' +
      "<p>命中明细列名（如运单号、客户名单、薪酬明细、车辆轨迹等）将整份拒绝。「轨迹断更」是汇总票数，允许上传。</p>" +
      "<p>照片和 PDF 第一版不能自动识别成正式数字，通过后仍是待测上传，并标明「非正式，尚未演算」。</p></div>" +
      '<form id="upload-form" autocomplete="off">' +
      '<div class="form-block"><span class="form-label">来源类型<span class="required">必选</span></span>' +
      '<div class="source-picks">' +
      sources +
      "</div></div>" +
      '<div class="form-block"><span class="form-label">选择文件或拍照</span>' +
      '<div class="file-row">' +
      '<label class="file-btn">选择文件<input type="file" id="file-input" accept=".json,.csv,.tsv,.xlsx,.xls,.pdf,image/*,.png,.jpg,.jpeg,.webp,.gif,.bmp,.heic" /></label>' +
      '<label class="file-btn">拍照<input type="file" id="camera-input" accept="image/*" capture="camera" /></label>' +
      '<div class="file-name" id="file-name">尚未选择文件</div>' +
      "</div></div>" +
      '<div class="form-block"><span class="form-label">或粘贴 JSON / 字段名</span>' +
      '<textarea class="paste" id="paste-input" placeholder=\'例如 {"来源类型":"Danny提供的汇总","轨迹断更":100} 或字段名：轨迹断更,件量\'></textarea>' +
      "</div>" +
      '<div class="actions"><button class="btn btn-primary" type="submit">生成测试层待处理包</button>' +
      '<button class="btn btn-ghost" type="reset" id="btn-reset">清空</button></div>' +
      "</form>" +
      msg +
      pack;
    bindUpload();
  }

  function clearUploadMemory() {
    state.lastPackage = null;
    const fileInput = document.getElementById("file-input");
    const cameraInput = document.getElementById("camera-input");
    const pasteInput = document.getElementById("paste-input");
    const fileName = document.getElementById("file-name");
    if (fileInput) fileInput.value = "";
    if (cameraInput) cameraInput.value = "";
    if (pasteInput) pasteInput.value = "";
    if (fileName) fileName.textContent = "尚未选择文件";
  }

  function chosenFile() {
    const a = document.getElementById("file-input");
    const b = document.getElementById("camera-input");
    if (a && a.files && a.files[0]) return a.files[0];
    if (b && b.files && b.files[0]) return b.files[0];
    return null;
  }

  function bindUpload() {
    const form = document.getElementById("upload-form");
    const fileInput = document.getElementById("file-input");
    const cameraInput = document.getElementById("camera-input");
    const fileName = document.getElementById("file-name");
    const resetBtn = document.getElementById("btn-reset");
    const dlBtn = document.getElementById("btn-download");

    function showName() {
      const f = chosenFile();
      fileName.textContent = f ? f.name + "（" + f.size + " 字节）" : "尚未选择文件";
    }
    if (fileInput) {
      fileInput.addEventListener("change", () => {
        if (cameraInput) cameraInput.value = "";
        showName();
      });
    }
    if (cameraInput) {
      cameraInput.addEventListener("change", () => {
        if (fileInput) fileInput.value = "";
        showName();
      });
    }
    if (resetBtn) {
      resetBtn.addEventListener("click", (ev) => {
        ev.preventDefault();
        state.uploadMsg = null;
        clearUploadMemory();
        renderUpload();
      });
    }
    if (dlBtn && state.lastPackage) {
      dlBtn.addEventListener("click", () => downloadPackage(state.lastPackage));
    }
    if (form) {
      form.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const sourceEl = form.querySelector('input[name="sourceType"]:checked');
        const sourceType = sourceEl ? sourceEl.value : "";
        const file = chosenFile();
        const pastedText = (document.getElementById("paste-input") || {}).value || "";
        try {
          const pkg = await globalThis.H5Upload.validateUpload({ sourceType, file, pastedText });
          state.lastPackage = pkg;
          state.uploadMsg = {
            ok: true,
            text:
              "已通过前端校验，生成测试层待处理包。\n状态：待测上传。\n非正式，尚未演算。\n来源类型：" +
              pkg.source_type +
              "。" +
              (pkg.file_kind === "image" || pkg.file_kind === "pdf"
                ? "\n照片/PDF 未做识别，不会把影像当作已演算数字。"
                : "") +
              "\n请下载 JSON，需要时手工放入 test_layer/inbox/。不要写入 formal_layer/。",
          };
          renderUpload();
        } catch (err) {
          state.lastPackage = null;
          if (fileInput) fileInput.value = "";
          if (cameraInput) cameraInput.value = "";
          if (fileName) fileName.textContent = "尚未选择文件";
          const pasteEl = document.getElementById("paste-input");
          if (pasteEl) pasteEl.value = "";
          state.uploadMsg = {
            ok: false,
            text: (err && err.message) || "已拒绝，未保留内容。",
          };
          renderUpload();
        }
      });
    }
  }

  function downloadPackage(pkg) {
    const text = JSON.stringify(pkg, null, 2);
    const blob = new Blob([text], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = globalThis.H5Upload.packageFilename(pkg);
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function render() {
    if (state.error) {
      renderDisclaimer();
      mainEl.innerHTML =
        '<div class="error-load">无法读取测试层产出副本。请在 h5/ 目录用本地服务打开，例如：python3 -m http.server 8765。' +
        (state.error ? "（" + esc(state.error) + "）" : "") +
        "</div>";
      return;
    }
    if (!state.report) {
      renderDisclaimer();
      mainEl.innerHTML = '<div class="loading">正在载入测试层产出…</div>';
      return;
    }
    renderDisclaimer();
    const r = route();
    setActiveTab(r.name);
    window.scrollTo(0, 0);
    if (r.name === "overall") renderOverall();
    else if (r.name === "departments") renderDepartments();
    else if (r.name === "department") renderDepartment(r.dept);
    else renderUpload();
  }

  async function load() {
    try {
      const [reportRes, overallRes, deptRes] = await Promise.all([
        fetch("data/test_report.json", { cache: "no-store" }),
        fetch("data/整体结论.md", { cache: "no-store" }),
        fetch("data/各部门重点关注目标.md", { cache: "no-store" }),
      ]);
      if (!reportRes.ok || !overallRes.ok || !deptRes.ok) {
        throw new Error("读取 data/ 失败");
      }
      state.report = await reportRes.json();
      state.overallMd = await overallRes.text();
      state.deptMd = await deptRes.text();
      state.overallMetrics = globalThis.H5Parse.parseOverallMarkdown(state.overallMd).metrics;
      state.deptMetrics = globalThis.H5Parse.parseDepartmentMarkdown(state.deptMd);
      state.error = "";
    } catch (err) {
      state.error = err && err.message ? err.message : "载入失败";
    }
    render();
  }

  window.addEventListener("hashchange", render);
  if (!location.hash) location.hash = "#/overall";
  load();
})();
