"""
Admin role / data-scope / functional-permission constants.

Role codes come from 第一阶段数据库与后端接口设计说明.md §13.2 ("建议第一阶段预设以下角色编码") —
this is the only place in the project's own materials that defines a role list; we do not invent
roles beyond what's there. Where that document doesn't specify fine-grained action permissions,
role → permission mapping below is a conservative, least-privilege inference from the business
flows already implemented in app/services/*.py; ambiguous mappings are called out in
docs/ADMIN_PERMISSION_MATRIX.md as "需要业务确认" rather than guessed silently.
"""

from typing import Iterable, Optional


class DataScope:
    ALL = "ALL"
    REGION = "REGION"
    DEPARTMENT = "DEPARTMENT"
    SELF = "SELF"


VALID_DATA_SCOPES = {DataScope.ALL, DataScope.REGION, DataScope.DEPARTMENT, DataScope.SELF}


class ScopeBranch:
    """Which filtering branch a list query should take for a given data_scope value."""

    ALL = "ALL"                # 不加区域/部门过滤，返回全量
    REGION = "REGION"          # 必须按 region_code 过滤
    DEPARTMENT = "DEPARTMENT"  # 必须按部门维度过滤（含 SELF）
    DENY = "DENY"              # 未知/不支持的 data_scope —— Fail Closed，不返回任何数据


def resolve_scope_branch(data_scope: Optional[str]) -> str:
    scope = (data_scope or "").strip().upper()
    if scope == DataScope.ALL:
        return ScopeBranch.ALL
    if scope == DataScope.REGION:
        return ScopeBranch.REGION
    if scope in (DataScope.DEPARTMENT, DataScope.SELF):
        return ScopeBranch.DEPARTMENT
    return ScopeBranch.DENY


class AdminRole:
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    CITY_ADMIN = "CITY_ADMIN"
    CENTER_ADMIN = "CENTER_ADMIN"
    CENTER_STAFF = "CENTER_STAFF"
    DEPT_USER = "DEPT_USER"
    ROOM_ADMIN = "ROOM_ADMIN"


class Permission:
    APPEAL_VIEW = "APPEAL_VIEW"
    APPEAL_HANDLE = "APPEAL_HANDLE"                 # 受理/退回/不予受理/企服中心办理/分派/审核回复/办结/回访
    APPEAL_DEPT_REPLY = "APPEAL_DEPT_REPLY"         # 部门反馈
    MEETING_ROOM_VIEW = "MEETING_ROOM_VIEW"         # 会议室/预约 列表&详情&台账
    MEETING_ROOM_MANAGE = "MEETING_ROOM_MANAGE"     # 会议室资源/开放规则/材料清单/手工占用 维护
    MEETING_BOOKING_HANDLE = "MEETING_BOOKING_HANDLE"  # 预约审核/驳回/完成/爽约/退回补充
    GOV_MEETING_VIEW = "GOV_MEETING_VIEW"
    GOV_MEETING_HANDLE = "GOV_MEETING_HANDLE"       # 审核/安排/确认/完成/纪要/办结
    DICT_MANAGE = "DICT_MANAGE"                     # 字典维护（含服务中心维护）
    OPERATION_LOG_VIEW = "OPERATION_LOG_VIEW"
    DASHBOARD_VIEW = "DASHBOARD_VIEW"
    ADMIN_USER_MANAGE = "ADMIN_USER_MANAGE"         # 管理员账号/角色/数据权限维护（sys_admin_user）


_ALL_PERMISSIONS = {
    v for k, v in vars(Permission).items() if not k.startswith("_") and isinstance(v, str)
}

# 角色 -> 权限集合。PLATFORM_ADMIN/CITY_ADMIN 数据范围为"全部"（设计文档原文），
# 采用层级 RBAC 的通常假设：数据范围更大的角色至少拥有下级角色的全部操作能力。
ROLE_PERMISSIONS: dict[str, set[str]] = {
    AdminRole.PLATFORM_ADMIN: set(_ALL_PERMISSIONS),
    AdminRole.CITY_ADMIN: set(_ALL_PERMISSIONS),
    AdminRole.CENTER_ADMIN: {
        Permission.APPEAL_VIEW,
        Permission.APPEAL_HANDLE,
        Permission.MEETING_ROOM_VIEW,
        Permission.MEETING_ROOM_MANAGE,
        Permission.MEETING_BOOKING_HANDLE,
        Permission.GOV_MEETING_VIEW,
        Permission.GOV_MEETING_HANDLE,
        Permission.DICT_MANAGE,
        Permission.OPERATION_LOG_VIEW,
        Permission.DASHBOARD_VIEW,
    },
    AdminRole.CENTER_STAFF: {
        Permission.APPEAL_VIEW,
        Permission.APPEAL_HANDLE,
        Permission.MEETING_ROOM_VIEW,
        Permission.MEETING_BOOKING_HANDLE,
        Permission.GOV_MEETING_VIEW,
        Permission.GOV_MEETING_HANDLE,
        Permission.DASHBOARD_VIEW,
    },
    AdminRole.DEPT_USER: {
        Permission.APPEAL_VIEW,
        Permission.APPEAL_DEPT_REPLY,
    },
    AdminRole.ROOM_ADMIN: {
        Permission.MEETING_ROOM_VIEW,
        Permission.MEETING_ROOM_MANAGE,
        Permission.MEETING_BOOKING_HANDLE,
    },
}


def get_permissions_for_roles(role_codes: Optional[Iterable[str]]) -> set[str]:
    result: set[str] = set()
    for role in role_codes or []:
        result |= ROLE_PERMISSIONS.get(role, set())
    return result


def has_permission(role_codes: Optional[Iterable[str]], permission_code: str) -> bool:
    return permission_code in get_permissions_for_roles(role_codes)


def has_any_permission(role_codes: Optional[Iterable[str]], permission_codes: Iterable[str]) -> bool:
    granted = get_permissions_for_roles(role_codes)
    return any(code in granted for code in permission_codes)
