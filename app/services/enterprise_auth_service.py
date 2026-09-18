"""
Enterprise LOCAL authentication (self-registration + password login).

Design intent
-------------
`Enterprise` (business profile) and `EnterpriseIdentity` (login identity) are
kept deliberately separate:

  Enterprise 1 : N EnterpriseIdentity

An Enterprise may end up with zero, one, or several identities over time
(LOCAL today, PROVINCIAL_SSO later — an enterprise could even hold both at
once once SSO is wired up). This service only ever touches LOCAL identities.
It authenticates the caller and then hands back a plain enterprise_id, using
the exact same JWT payload shape and `create_enterprise_token()` call that
`app/api/auth/router.py`'s existing mock-login already uses — so
`app/core/deps.py::get_current_enterprise` and all three business modules
(appeal / meeting_room / gov_meeting) need zero changes.
"""

from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AlreadyRegisteredException, LoginFailedException
from app.core.password import hash_password, verify_password
from app.core.security import create_enterprise_token
from app.models.enterprise import EnterpriseIdentityType
from app.repositories.enterprise_identity_repo import EnterpriseIdentityRepository
from app.repositories.enterprise_repo import EnterpriseRepository


def _issue_token(enterprise) -> dict[str, Any]:
    payload = {
        "sub": str(enterprise.id),
        "subject_type": "ENTERPRISE",
        "enterprise_id": enterprise.id,
        "enterprise_name": enterprise.enterprise_name,
        "credit_code": enterprise.credit_code,
    }
    return {"accessToken": create_enterprise_token(payload)}


class EnterpriseAuthService:
    def __init__(self, db: Session):
        self.db = db
        self.ent_repo = EnterpriseRepository(db)
        self.identity_repo = EnterpriseIdentityRepository(db)

    def register_local(self, data: dict) -> dict:
        credit_code = data["creditCode"]

        try:
            enterprise = self.ent_repo.get_by_credit_code(credit_code)

            if enterprise is not None:
                existing_local = self.identity_repo.get_by_enterprise_and_type(
                    enterprise.id, EnterpriseIdentityType.LOCAL
                )
                if existing_local is not None:
                    # 情况3：该信用代码已注册过本地账号，禁止重复注册。
                    raise AlreadyRegisteredException()
                # 情况2：Enterprise 已存在（例如此前通过 mock-login/其他方式产生），
                # 但尚未绑定 LOCAL 身份——不重复建企业，只绑定新的登录身份。
            else:
                # 情况1：信用代码从未出现过，新建企业档案。
                # 法人三要素留空，等待权威来源（省认证/管理端核实）补齐。
                enterprise = self.ent_repo.create(
                    enterprise_name=data["enterpriseName"],
                    credit_code=credit_code,
                    legal_person_name=None,
                    legal_person_id_no=None,
                    legal_person_mobile=None,
                    auth_source="LOCAL",
                )

            self.identity_repo.create_local_identity(
                enterprise_id=enterprise.id,
                credit_code=credit_code,
                credential_hash=hash_password(data["password"]),
                contact_name=data.get("contactName"),
                contact_mobile=data.get("contactMobile"),
            )

            enterprise.last_login_time = datetime.utcnow()
            self.db.flush()
            self.db.commit()
        except IntegrityError:
            # 并发重复提交：两个请求同时通过了上面的存在性检查，
            # 数据库唯一约束（enterprise.credit_code 或
            # uq_enterprise_identity_type_identifier）兜底拦截其中一个。
            self.db.rollback()
            raise AlreadyRegisteredException()

        self.db.refresh(enterprise)
        return _issue_token(enterprise)

    def login_local(self, credit_code: str, password: str) -> dict:
        identity = self.identity_repo.get_by_type_and_identifier(
            EnterpriseIdentityType.LOCAL, credit_code
        )
        # 账号不存在 / 密码错误 必须返回完全相同的错误，不能让调用方区分两者，
        # 否则可以被用来枚举已注册的统一社会信用代码。
        if identity is None or not verify_password(password, identity.credential_hash):
            raise LoginFailedException()

        if identity.status != "ACTIVE":
            raise LoginFailedException()

        enterprise = self.ent_repo.get_by_id(identity.enterprise_id)
        if enterprise is None:
            raise LoginFailedException()

        self.identity_repo.update_login(identity)
        enterprise.last_login_time = datetime.utcnow()
        self.db.commit()

        return _issue_token(enterprise)
