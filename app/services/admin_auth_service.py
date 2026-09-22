"""管理端正式登录编排：BSP 认证 → 本地管理员匹配/绑定 → 签发本系统 JWT。

认证与授权分离（改造背景第四节）：
  - "这个人是谁、账号密码是否合法" 完全由 BspClient / BSP 判断，本模块不重新验证密码。
  - "这个人在企业服务中心是什么角色、能看什么数据" 完全来自 SysAdminUser 这张本地表，
    绝不读取、也绝不接受 BSP 返回的 role/roleValue 作为本系统角色。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, LoginFailedException, ThirdPartyAuthException
from app.core.security import create_admin_token
from app.models.system import AdminUserStatus, SysAdminUser, SysOperationLog
from app.repositories.admin_user_repo import AdminUserRepository
from app.services.bsp_client import BspAuthFailedException, BspClient, BspServiceException, BspUser

# 未绑定/已禁用两种情况对外统一提示成同一句话，避免向调用方泄露
# "这个用户名在本系统里到底是不存在、还是存在但被禁用" 这类账号状态信息。
_NOT_PROVISIONED_MESSAGE = "当前账号未开通企业服务中心管理权限，请联系管理员"


class AdminAuthService:
    def __init__(self, db: Session, bsp_client: BspClient | None = None):
        self.db = db
        self.repo = AdminUserRepository(db)
        self.bsp_client = bsp_client or BspClient()

    def login(self, username: str, password: str) -> dict[str, Any]:
        try:
            bsp_user = self.bsp_client.login(username, password)
        except BspAuthFailedException:
            raise LoginFailedException("账号或密码错误")
        except BspServiceException as exc:
            raise ThirdPartyAuthException(str(exc))

        admin = self._match_local_admin(bsp_user)

        if admin.status != AdminUserStatus.ACTIVE:
            raise ForbiddenException("账号已被禁用，请联系管理员")

        self.repo.touch_login(admin, real_name=bsp_user.name, mobile=bsp_user.mobile)
        self.db.commit()
        self.db.refresh(admin)

        return self._issue_token(admin)

    def _match_local_admin(self, bsp_user: BspUser) -> SysAdminUser:
        admin = self.repo.get_by_bsp_user_id(bsp_user.id)
        if admin is not None:
            return admin

        # 尚未按 bsp_user_id 绑定过——尝试按 username 做一次性安全绑定。
        candidate = self.repo.get_by_username(bsp_user.username)
        if (
            candidate is not None
            and candidate.status == AdminUserStatus.ACTIVE
            and candidate.bsp_user_id is None
        ):
            self.repo.bind_bsp_user_id(candidate, bsp_user.id)
            self.db.add(SysOperationLog(
                operator_type="ADMIN",
                operator_id=str(candidate.id),
                operator_name=candidate.real_name,
                business_type="ADMIN_USER",
                business_id=candidate.id,
                operation_type="BSP_BIND",
                operation_content=f"首次登录安全绑定 BSP 账号：username={bsp_user.username}, bsp_user_id={bsp_user.id}",
            ))
            self.db.commit()
            self.db.refresh(candidate)
            return candidate

        raise ForbiddenException(_NOT_PROVISIONED_MESSAGE)

    def _issue_token(self, admin: SysAdminUser) -> dict[str, Any]:
        role_codes = [c for c in (admin.role_codes or "").split(",") if c]
        payload = {
            "sub": str(admin.id),
            "subject_type": "ADMIN",
            "admin_source": "BSP",
            "user_id": admin.id,
            "platform_user_id": admin.bsp_user_id,
            "username": admin.username,
            "real_name": admin.real_name,
            "department_id": admin.department_id,
            "department_name": admin.department_name,
            "region_code": admin.region_code,
            "region_name": admin.region_name,
            "role_codes": role_codes,
            "data_scope": admin.data_scope,
        }
        return {"accessToken": create_admin_token(payload)}
