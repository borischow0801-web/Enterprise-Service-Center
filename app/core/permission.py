"""
Authorization = Role Permission AND Data Scope Permission.

- require_permissions(...): FastAPI dependency — "is this role allowed to perform this
  action at all". Plugs in wherever a route currently declares `current: CurrentAdmin`.
- DataPermissionService: "is this specific record within this operator's data scope".
  Called explicitly inside service methods once a record has been fetched, because the
  scope check needs the record's region/department, which isn't known before the fetch.

Both are intentionally simple, table-driven, and centralized here so no endpoint ever
hand-rolls `if "XXX" not in current["role_codes"]` or `if region_code != ...` again.
"""

from typing import Iterable, Optional

from fastapi import Depends

from app.core.deps import CurrentAdmin
from app.core.exceptions import ForbiddenException
from app.constants.permission import DataScope, has_any_permission


def require_permissions(*permission_codes: str):
    """Usage: current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE))
    Passing multiple codes means "any one of these is sufficient" (OR semantics)."""

    def _checker(current: CurrentAdmin) -> dict:
        role_codes = current.get("role_codes") or []
        if not has_any_permission(role_codes, permission_codes):
            raise ForbiddenException("当前角色无权执行该操作")
        return current

    return _checker


class DataPermissionService:
    """Fail-closed data-scope enforcement.

    An operator's JWT carries `data_scope` (+ `region_code` / `department_id`) exactly as
    self-declared at login (see app/api/auth/router.py::admin_mock_login) — this module does
    not change how that value is obtained, only how strictly it's enforced afterwards.
    """

    @staticmethod
    def assert_can_access(
        operator: dict,
        region_code: Optional[str] = None,
        dept_ids: Optional[Iterable[Optional[str]]] = None,
    ) -> None:
        """
        region_code: the business record's own region_code (appeal/booking/apply all have one).
        dept_ids: for modules with a real department-of-record concept (currently only Appeal:
            responsible_dept_id + historical assigned_dept_id). Leave None for modules that have
            no department concept (meeting room / gov meeting) — DEPARTMENT/SELF scope then falls
            back to the region-equivalent check, matching the approximation the existing list
            endpoints already use for those two modules (see meeting_room_repo.py / gov_meeting_repo.py
            comments: "DEPARTMENT/SELF: TODO — treated as REGION").
        """
        scope = (operator.get("data_scope") or "").strip().upper()

        if scope == DataScope.ALL:
            return

        if scope == DataScope.REGION:
            if region_code and region_code == operator.get("region_code"):
                return
            raise ForbiddenException("无权访问其他区域的数据")

        if scope in (DataScope.DEPARTMENT, DataScope.SELF):
            if dept_ids is not None:
                current_dept = str(operator.get("department_id") or "")
                dept_id_strs = {str(d) for d in dept_ids if d}
                if current_dept and current_dept in dept_id_strs:
                    return
                raise ForbiddenException("无权访问其他部门的数据")
            if region_code and region_code == operator.get("region_code"):
                return
            raise ForbiddenException("无权访问其他区域/部门的数据")

        # 未知/缺失 data_scope：Fail Closed，一律拒绝，绝不默认放行为 ALL。
        raise ForbiddenException("数据权限范围未知，拒绝访问")
