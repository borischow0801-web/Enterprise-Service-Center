"""管理员账号管理（sys_admin_user）——统一身份认证改造后，角色/区划/数据权限的
唯一正式维护入口。登录流程只读这张表，不写；只有这里的接口能写。

权限收紧到 ADMIN_USER_MANAGE，目前只有 PLATFORM_ADMIN / CITY_ADMIN 拥有
（见 app/constants/permission.py 的 ROLE_PERMISSIONS）——能在这里给别人分配角色，
本身就是一种可以提权到 PLATFORM_ADMIN 的能力，不能开放给 CENTER_ADMIN 及以下。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permission import require_permissions
from app.core.response import success, paginated
from app.core.exceptions import NotFoundException, ParamException
from app.constants.permission import Permission, AdminRole, VALID_DATA_SCOPES
from app.models.system import AdminUserStatus, SysOperationLog
from app.repositories.admin_user_repo import AdminUserRepository

router = APIRouter()

_VALID_ROLE_CODES = {v for k, v in vars(AdminRole).items() if not k.startswith("_") and isinstance(v, str)}
_VALID_STATUSES = {AdminUserStatus.ACTIVE, AdminUserStatus.DISABLED}


_require_manage = require_permissions(Permission.ADMIN_USER_MANAGE)


def _to_dict(item) -> dict:
    return {
        "id": item.id,
        "bspUserId": item.bsp_user_id,
        "username": item.username,
        "realName": item.real_name,
        "mobile": item.mobile,
        "status": item.status,
        "roleCodes": item.role_codes.split(",") if item.role_codes else [],
        "dataScope": item.data_scope,
        "regionCode": item.region_code,
        "regionName": item.region_name,
        "departmentId": item.department_id,
        "departmentName": item.department_name,
        "lastLoginAt": item.last_login_at.isoformat() if item.last_login_at else None,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "updatedAt": item.updated_at.isoformat() if item.updated_at else None,
    }


def _validate_role_codes(role_codes) -> str:
    if not role_codes or not isinstance(role_codes, list):
        raise ParamException("角色不能为空")
    invalid = [r for r in role_codes if r not in _VALID_ROLE_CODES]
    if invalid:
        raise ParamException(f"未知角色编码：{','.join(invalid)}")
    return ",".join(role_codes)


def _validate_data_scope(data_scope) -> str:
    if data_scope not in VALID_DATA_SCOPES:
        raise ParamException(f"未知数据权限范围：{data_scope}")
    return data_scope


def _write_log(db: Session, current: dict, op_type: str, target: "object", content: str):
    db.add(SysOperationLog(
        operator_type="ADMIN",
        operator_id=str(current.get("user_id", "")),
        operator_name=current.get("real_name", ""),
        business_type="ADMIN_USER",
        business_id=getattr(target, "id", None),
        operation_type=op_type,
        operation_content=content,
    ))


@router.get("/page", summary="管理员分页列表")
def list_admin_users(
    current: dict = Depends(_require_manage),
    db: Session = Depends(get_db),
    username: str | None = Query(None),
    status: str | None = Query(None),
    roleCode: str | None = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
):
    repo = AdminUserRepository(db)
    records, total = repo.list_page(pageNo, pageSize, username=username, status=status, role_code=roleCode)
    return paginated(records=[_to_dict(r) for r in records], total=total, page_no=pageNo, page_size=pageSize)


@router.get("/{admin_id}", summary="管理员详情")
def get_admin_user(admin_id: int, current: dict = Depends(_require_manage), db: Session = Depends(get_db)):
    repo = AdminUserRepository(db)
    item = repo.get_by_id(admin_id)
    if item is None:
        raise NotFoundException("管理员不存在")
    return success(data=_to_dict(item))


@router.post("", summary="新增管理员")
def create_admin_user(body: dict, current: dict = Depends(_require_manage), db: Session = Depends(get_db)):
    username = (body.get("username") or "").strip()
    real_name = (body.get("realName") or "").strip()
    if not username or not real_name:
        raise ParamException("账号、姓名不能为空")

    repo = AdminUserRepository(db)
    if repo.get_by_username(username) is not None:
        raise ParamException("该账号已存在")

    role_codes = _validate_role_codes(body.get("roleCodes"))
    data_scope = _validate_data_scope(body.get("dataScope"))
    status = body.get("status") or AdminUserStatus.ACTIVE
    if status not in _VALID_STATUSES:
        raise ParamException("无效的状态值")

    item = repo.create(
        username=username,
        real_name=real_name,
        mobile=body.get("mobile") or None,
        status=status,
        role_codes=role_codes,
        data_scope=data_scope,
        region_code=body.get("regionCode") or None,
        region_name=body.get("regionName") or None,
        department_id=body.get("departmentId") or None,
        department_name=body.get("departmentName") or None,
    )
    _write_log(db, current, "ADMIN_USER_CREATE", item, f"新增管理员 username={username}")
    db.commit()
    db.refresh(item)
    return success(data=_to_dict(item), message="新增成功")


@router.put("/{admin_id}", summary="修改管理员")
def update_admin_user(admin_id: int, body: dict, current: dict = Depends(_require_manage), db: Session = Depends(get_db)):
    repo = AdminUserRepository(db)
    item = repo.get_by_id(admin_id)
    if item is None:
        raise NotFoundException("管理员不存在")

    updates: dict = {}
    if "realName" in body:
        real_name = (body.get("realName") or "").strip()
        if not real_name:
            raise ParamException("姓名不能为空")
        updates["real_name"] = real_name
    if "mobile" in body:
        updates["mobile"] = body.get("mobile") or None
    if "roleCodes" in body:
        updates["role_codes"] = _validate_role_codes(body.get("roleCodes"))
    if "dataScope" in body:
        updates["data_scope"] = _validate_data_scope(body.get("dataScope"))
    if "regionCode" in body:
        updates["region_code"] = body.get("regionCode") or None
    if "regionName" in body:
        updates["region_name"] = body.get("regionName") or None
    if "departmentId" in body:
        updates["department_id"] = body.get("departmentId") or None
    if "departmentName" in body:
        updates["department_name"] = body.get("departmentName") or None

    repo.update_profile(item, **updates)
    item.updated_at = datetime.utcnow()
    _write_log(db, current, "ADMIN_USER_UPDATE", item, f"修改管理员 username={item.username}")
    db.commit()
    db.refresh(item)
    return success(data=_to_dict(item), message="修改成功")


@router.patch("/{admin_id}/status", summary="启用/禁用管理员")
def toggle_admin_user_status(admin_id: int, body: dict, current: dict = Depends(_require_manage), db: Session = Depends(get_db)):
    repo = AdminUserRepository(db)
    item = repo.get_by_id(admin_id)
    if item is None:
        raise NotFoundException("管理员不存在")
    status = body.get("status")
    if status not in _VALID_STATUSES:
        raise ParamException("无效的状态值")
    repo.update_profile(item, status=status)
    item.updated_at = datetime.utcnow()
    op_type = "ADMIN_USER_ENABLE" if status == AdminUserStatus.ACTIVE else "ADMIN_USER_DISABLE"
    _write_log(db, current, op_type, item, f"{op_type} username={item.username}")
    db.commit()
    db.refresh(item)
    return success(data=_to_dict(item), message="操作成功")
