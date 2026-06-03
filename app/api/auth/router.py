from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_enterprise_token, create_admin_token
from app.core.config import settings
from app.core.response import success
from app.schemas.auth import EnterpriseMockLoginRequest, AdminMockLoginRequest
from app.repositories.enterprise_repo import EnterpriseRepository
from app.repositories.sys_user_repo import SysUserSnapshotRepository

router = APIRouter()


@router.post("/enterprise/mock-login", summary="企业端模拟登录")
def enterprise_mock_login(body: EnterpriseMockLoginRequest, db: Session = Depends(get_db)):
    repo = EnterpriseRepository(db)
    enterprise = repo.get_by_credit_code(body.creditCode)

    if enterprise is None:
        enterprise = repo.create(
            enterprise_name=body.enterpriseName,
            credit_code=body.creditCode,
            legal_person_name=body.legalPersonName,
            legal_person_id_no=body.legalPersonIdNo,
            legal_person_mobile=body.legalPersonMobile,
            auth_source="MOCK",
            last_login_time=datetime.utcnow(),
        )
    else:
        repo.update_login(
            enterprise,
            enterprise_name=body.enterpriseName,
            legal_person_name=body.legalPersonName,
            legal_person_id_no=body.legalPersonIdNo,
            legal_person_mobile=body.legalPersonMobile,
        )

    db.commit()
    db.refresh(enterprise)

    token_payload = {
        "sub": str(enterprise.id),
        "subject_type": "ENTERPRISE",
        "enterprise_id": enterprise.id,
        "enterprise_name": enterprise.enterprise_name,
        "credit_code": enterprise.credit_code,
    }
    access_token = create_enterprise_token(token_payload)

    return success(
        data={
            "accessToken": access_token,
            "tokenType": "Bearer",
            "expiresIn": settings.jwt_enterprise_expire_minutes * 60,
        },
        message="登录成功",
    )


@router.post("/admin/mock-login", summary="管理端模拟登录")
def admin_mock_login(body: AdminMockLoginRequest, db: Session = Depends(get_db)):
    repo = SysUserSnapshotRepository(db)
    user = repo.get_by_platform_user_id(body.platformUserId)

    role_codes_str = ",".join(body.roleCodes)

    if user is None:
        user = repo.create(
            platform_user_id=body.platformUserId,
            username=body.username,
            real_name=body.realName,
            department_id=body.departmentId,
            department_name=body.departmentName,
            region_code=body.regionCode,
            region_name=body.regionName,
            role_codes=role_codes_str,
            data_scope=body.dataScope,
            last_login_time=datetime.utcnow(),
        )
    else:
        repo.update_login(
            user,
            username=body.username,
            real_name=body.realName,
            department_id=body.departmentId,
            department_name=body.departmentName,
            region_code=body.regionCode,
            region_name=body.regionName,
            role_codes=role_codes_str,
            data_scope=body.dataScope,
        )

    db.commit()
    db.refresh(user)

    token_payload = {
        "sub": str(user.id),
        "subject_type": "ADMIN",
        "user_id": user.id,
        "platform_user_id": user.platform_user_id,
        "real_name": user.real_name,
        "department_id": user.department_id,
        "department_name": user.department_name,
        "region_code": user.region_code,
        "region_name": user.region_name,
        "role_codes": body.roleCodes,
        "data_scope": user.data_scope,
    }
    access_token = create_admin_token(token_payload)

    return success(
        data={
            "accessToken": access_token,
            "tokenType": "Bearer",
            "expiresIn": settings.jwt_admin_expire_minutes * 60,
        },
        message="登录成功",
    )
