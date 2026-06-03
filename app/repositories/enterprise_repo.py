from datetime import datetime
from sqlalchemy.orm import Session
from app.models.enterprise import Enterprise


class EnterpriseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_credit_code(self, credit_code: str) -> Enterprise | None:
        return self.db.query(Enterprise).filter(
            Enterprise.credit_code == credit_code,
            Enterprise.deleted_flag == 0
        ).first()

    def get_by_id(self, enterprise_id: int) -> Enterprise | None:
        return self.db.query(Enterprise).filter(
            Enterprise.id == enterprise_id,
            Enterprise.deleted_flag == 0
        ).first()

    def create(self, **kwargs) -> Enterprise:
        obj = Enterprise(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_login(self, enterprise: Enterprise, **kwargs) -> Enterprise:
        for k, v in kwargs.items():
            setattr(enterprise, k, v)
        enterprise.last_login_time = datetime.utcnow()
        self.db.flush()
        return enterprise
