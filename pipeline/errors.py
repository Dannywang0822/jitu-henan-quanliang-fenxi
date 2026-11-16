"""流水线不变量错误。本模块不连接云，也不写正式层。"""


class PeriodMixError(ValueError):
    """日、周、月结果串期，或周期键与 as_of 不一致。"""


class NextMonthIsNotNextWeek(ValueError):
    """下个月测算被写成下个周。"""


class DictionaryNotExact(ValueError):
    """字段字典未完全一致，不得写入宽表。"""


class TableTooLarge(ValueError):
    """测试阶段宽表超过本地上限。"""


class AutoPromotionForbidden(PermissionError):
    """不得自动晋升正式层，也不得直接写正式宽表。"""


class FormalSurfaceUnavailable(PermissionError):
    """正式层为空时，周运营台、决策逻辑、历史对比不可用。"""


class OpenRegistrationForbidden(PermissionError):
    """账号不开放注册，只能指定开通。"""


class LaneRoleMismatch(PermissionError):
    """上传路与指定账号的角色或部门不一致。"""


class DocumentDatabaseWriteForbidden(PermissionError):
    """原始表和宽表不得写入 CloudBase 文档库。"""


class CloudResourceNotOpened(RuntimeError):
    """云资源尚未开通；骨架拒绝购买、开通和部署。"""


class DemandEntrySeparated(ValueError):
    """提需求入口不并进交数流水线。"""
