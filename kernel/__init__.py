"""同一物理模型内核。部门只挂视角，不另起模型。"""

from kernel.source import SourceType, SourcedDecimal, MissingSourceError, InvalidSourceError
from kernel.fields import FieldId, PersonNameAsPrimaryKeyError, parse_field_id
from kernel.dates import AsOf, DifferentAsOfCannotBeSameDay, as_same_day, CrossDateContrast
from kernel.departments import Department, UnknownDepartmentError, CapacityIsNotDepartmentError
from kernel.ratios import (
    MomType,
    CumulativeKind,
    achievement_rate,
    InvertedAchievementRateError,
    MissingMomTypeError,
    WrongCumulativeCaliberError,
)
from kernel.metrics import FieldMergeForbidden, forbid_merge, LABOR_COST_ASSESSMENT, LABOR_COST_OPS, CAPACITY_PER_KG_CORE, CAPACITY_PER_KG_PNL
from kernel.pnl import PnlIdentityError, assert_pnl_identity
from kernel.output import IncompleteReportError, InformalMark, TwoLayerReport
from kernel.connectors import InternalSystemConnectorForbidden, connect_jitu_internal
from kernel.detail import DetailColumnRejected, reject_detail_column
from kernel.promotion import (
    PromotionDenied,
    IncompletePackageError,
    FormalStore,
    PromotionPackage,
    DannyApproval,
)

__all__ = [
    "SourceType",
    "SourcedDecimal",
    "MissingSourceError",
    "InvalidSourceError",
    "FieldId",
    "PersonNameAsPrimaryKeyError",
    "parse_field_id",
    "AsOf",
    "DifferentAsOfCannotBeSameDay",
    "as_same_day",
    "CrossDateContrast",
    "Department",
    "UnknownDepartmentError",
    "CapacityIsNotDepartmentError",
    "MomType",
    "CumulativeKind",
    "achievement_rate",
    "InvertedAchievementRateError",
    "MissingMomTypeError",
    "WrongCumulativeCaliberError",
    "FieldMergeForbidden",
    "forbid_merge",
    "LABOR_COST_ASSESSMENT",
    "LABOR_COST_OPS",
    "CAPACITY_PER_KG_CORE",
    "CAPACITY_PER_KG_PNL",
    "PnlIdentityError",
    "assert_pnl_identity",
    "IncompleteReportError",
    "InformalMark",
    "TwoLayerReport",
    "InternalSystemConnectorForbidden",
    "connect_jitu_internal",
    "DetailColumnRejected",
    "reject_detail_column",
    "PromotionDenied",
    "IncompletePackageError",
    "FormalStore",
    "PromotionPackage",
    "DannyApproval",
]
