/**
 * 与 kernel/detail.py 对齐的校验常量，以及允许的来源类型。
 * 不要在此改内核口径；仅复制前端校验所需名单。
 */
(function (global) {
  "use strict";

  const DETAIL_NAME_HINTS = [
    "薪酬明细",
    "工资明细",
    "个人工资",
    "银行账户",
    "银行卡",
    "证件号",
    "身份证",
    "工号清单",
    "员工名单",
    "运单明细",
    "运单号",
    "客户明细",
    "客户名单",
    "客户电话",
    "车辆轨迹",
    "轨迹明细",
    "逐车",
    "趟次明细",
    "加盟合同",
    "合同原文",
    "单商户结算",
    "结算明细",
  ];

  const ALLOWED_SUMMARY_EXCEPTIONS = new Set(["轨迹断更"]);

  const SOURCE_TYPES = ["假设", "公开来源", "合规授权汇总", "Danny提供的汇总"];

  const DEPT_ORDER = [
    "客服",
    "人资行政",
    "总经办",
    "市场",
    "质控",
    "网络管理",
    "财务",
    "营运",
    "云仓",
  ];

  function isDetailColumn(columnName) {
    const text = String(columnName == null ? "" : columnName).trim();
    if (!text) return false;
    if (ALLOWED_SUMMARY_EXCEPTIONS.has(text)) return false;
    return DETAIL_NAME_HINTS.some((hint) => text.includes(hint));
  }

  function findDetailHint(columnName) {
    const text = String(columnName == null ? "" : columnName).trim();
    if (!text) return null;
    if (ALLOWED_SUMMARY_EXCEPTIONS.has(text)) return null;
    return DETAIL_NAME_HINTS.find((hint) => text.includes(hint)) || null;
  }

  global.H5Const = {
    DETAIL_NAME_HINTS,
    ALLOWED_SUMMARY_EXCEPTIONS,
    SOURCE_TYPES,
    DEPT_ORDER,
    isDetailColumn,
    findDetailHint,
  };
})(window);
