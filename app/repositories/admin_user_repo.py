from datetime import datetime

from sqlalchemy.orm import Session

from app.models.system import SysAdminUser


class AdminUserRepository:
    """正式管理端账号（SysAdminUser）的数据访问层。

    登录流程只应调用 get_by_bsp_user_id / get_by_username / bind_bsp_user_id /
    touch_login —— 均不改写 role_codes/data_scope/region_code/department_id，
    这些字段只由管理员管理界面（app/api/admin/admin_users.py）写入。
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_bsp_user_id(self, bsp_user_id: str) -> SysAdminUser | None:
        return self.db.query(SysAdminUser).filter(
            SysAdminUser.bsp_user_id == bsp_user_id,
            SysAdminUser.deleted_flag == 0,
        ).first()

    def get_by_username(self, username: str) -> SysAdminUser | None:
        return self.db.query(SysAdminUser).filter(
            SysAdminUser.username == username,
            SysAdminUser.deleted_flag == 0,
        ).first()

    def get_by_id(self, admin_id: int) -> SysAdminUser | None:
        return self.db.query(SysAdminUser).filter(
            SysAdminUser.id == admin_id,
            SysAdminUser.deleted_flag == 0,
        ).first()

    def list_page(
        self,
        page_no: int,
        page_size: int,
        username: str | None = None,
        status: str | None = None,
        role_code: str | None = None,
    ) -> tuple[list[SysAdminUser], int]:
        q = self.db.query(SysAdminUser).filter(SysAdminUser.deleted_flag == 0)
        if username:
            q = q.filter(SysAdminUser.username.contains(username))
        if status:
            q = q.filter(SysAdminUser.status == status)
        if role_code:
            q = q.filter(SysAdminUser.role_codes.contains(role_code))
        total = q.count()
        records = (
            q.order_by(SysAdminUser.id.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return records, total

    def create(self, **kwargs) -> SysAdminUser:
        obj = SysAdminUser(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_profile(self, admin: SysAdminUser, **kwargs) -> SysAdminUser:
        """管理员管理界面用：更新角色/数据权限/区划/部门/状态等授权字段。"""
        for k, v in kwargs.items():
            setattr(admin, k, v)
        self.db.flush()
        return admin

    def bind_bsp_user_id(self, admin: SysAdminUser, bsp_user_id: str) -> SysAdminUser:
        """首次登录的安全绑定：仅在 admin.bsp_user_id 为空时调用（由调用方保证前置条件）。"""
        admin.bsp_user_id = bsp_user_id
        self.db.flush()
        return admin

    def touch_login(self, admin: SysAdminUser, real_name: str | None = None, mobile: str | None = None) -> SysAdminUser:
        """登录成功后的安全字段同步：仅描述性信息，绝不涉及角色/数据权限。"""
        if real_name:
            admin.real_name = real_name
        if mobile:
            admin.mobile = mobile
        admin.last_login_at = datetime.utcnow()
        self.db.flush()
        return admin
