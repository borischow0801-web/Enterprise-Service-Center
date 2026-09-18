from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.enterprise import EnterpriseIdentity, EnterpriseIdentityType


class EnterpriseIdentityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_type_and_identifier(self, identity_type: str, identifier: str) -> Optional[EnterpriseIdentity]:
        return self.db.query(EnterpriseIdentity).filter(
            EnterpriseIdentity.identity_type == identity_type,
            EnterpriseIdentity.identifier == identifier,
            EnterpriseIdentity.deleted_flag == 0,
        ).first()

    def get_by_enterprise_and_type(self, enterprise_id: int, identity_type: str) -> Optional[EnterpriseIdentity]:
        return self.db.query(EnterpriseIdentity).filter(
            EnterpriseIdentity.enterprise_id == enterprise_id,
            EnterpriseIdentity.identity_type == identity_type,
            EnterpriseIdentity.deleted_flag == 0,
        ).first()

    def create_local_identity(
        self,
        enterprise_id: int,
        credit_code: str,
        credential_hash: str,
        contact_name: Optional[str],
        contact_mobile: Optional[str],
    ) -> EnterpriseIdentity:
        identity = EnterpriseIdentity(
            enterprise_id=enterprise_id,
            identity_type=EnterpriseIdentityType.LOCAL,
            identifier=credit_code,
            credential_hash=credential_hash,
            contact_name=contact_name,
            contact_mobile=contact_mobile,
        )
        self.db.add(identity)
        self.db.flush()
        return identity

    def update_login(self, identity: EnterpriseIdentity) -> EnterpriseIdentity:
        identity.last_login_time = datetime.utcnow()
        self.db.flush()
        return identity
