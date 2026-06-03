from datetime import datetime
from sqlalchemy.orm import Session
from app.models.system import SysUserSnapshot


class SysUserSnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_platform_user_id(self, platform_user_id: str) -> SysUserSnapshot | None:
        return self.db.query(SysUserSnapshot).filter(
            SysUserSnapshot.platform_user_id == platform_user_id,
            SysUserSnapshot.deleted_flag == 0
        ).first()

    def get_by_id(self, user_id: int) -> SysUserSnapshot | None:
        return self.db.query(SysUserSnapshot).filter(
            SysUserSnapshot.id == user_id,
            SysUserSnapshot.deleted_flag == 0
        ).first()

    def create(self, **kwargs) -> SysUserSnapshot:
        obj = SysUserSnapshot(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_login(self, user: SysUserSnapshot, **kwargs) -> SysUserSnapshot:
        for k, v in kwargs.items():
            setattr(user, k, v)
        user.last_login_time = datetime.utcnow()
        self.db.flush()
        return user
