from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.constants.permission import Permission
from app.core.permission import require_permissions
from app.core.response import success, paginated
from app.core.exceptions import NotFoundException, ParamException
from app.constants.permission import resolve_scope_branch, ScopeBranch
from app.models.system import ServiceCenter, SysOperationLog
from app.repositories.sys_user_repo import SysUserSnapshotRepository
from app.repositories.admin_user_repo import AdminUserRepository
from app.api.admin.appeals import router as admin_appeals_router
from app.api.admin.meeting_rooms import router as admin_meeting_rooms_router
from app.api.admin.meeting_bookings import router as admin_meeting_bookings_router
from app.api.admin.gov_meetings import router as admin_gov_meetings_router
from app.api.admin.dictionaries import router as admin_dict_router
from app.api.admin.operation_logs import router as admin_op_log_router
from app.api.admin.dashboard import router as admin_dashboard_router
from app.api.admin.admin_users import router as admin_admin_users_router

router = APIRouter()

router.include_router(admin_appeals_router, prefix="/appeals", tags=["管理端-诉求"])
router.include_router(admin_meeting_rooms_router, prefix="/meeting-rooms", tags=["管理端-会议室"])
router.include_router(admin_meeting_bookings_router, prefix="/meeting-bookings", tags=["管理端-预约"])
router.include_router(admin_gov_meetings_router, prefix="/gov-meetings", tags=["管理端-政企约见"])
router.include_router(admin_dict_router, prefix="/dictionaries", tags=["管理端-字典"])
router.include_router(admin_op_log_router, prefix="/operation-logs", tags=["管理端-操作日志"])
router.include_router(admin_dashboard_router, prefix="/dashboard", tags=["管理端-工作台"])
router.include_router(admin_admin_users_router, prefix="/admin-users", tags=["管理端-管理员管理"])


def _service_center_to_dict(item: ServiceCenter) -> dict:
    return {
        "id": item.id,
        "centerName": item.center_name,
        "regionCode": item.region_code,
        "regionName": item.region_name,
        "address": item.address,
        "contactName": item.contact_name,
        "contactPhone": item.contact_phone,
        "status": item.status,
        "createdAt": item.created_at.isoformat() if item.created_at else None,
        "updatedAt": item.updated_at.isoformat() if item.updated_at else None,
    }


def _write_service_center_log(db: Session, current: dict, op_type: str, center_name: str):
    db.add(SysOperationLog(
        operator_type="USER",
        operator_id=str(current.get("user_id", "")),
        operator_name=current.get("real_name", ""),
        business_type="SERVICE_CENTER",
        operation_type=op_type,
        operation_content=f"服务中心={center_name}，操作={op_type}",
    ))


@router.get("/service-centers", summary="服务中心列表")
def list_service_centers(
    current: CurrentAdmin,
    db: Session = Depends(get_db),
    regionCode: str | None = Query(None),
):
    q = db.query(ServiceCenter).filter(
        ServiceCenter.deleted_flag == 0,
        ServiceCenter.status == "ENABLED",
    )
    current_region_code = current.get("region_code")
    branch = resolve_scope_branch(current.get("data_scope"))
    if branch == ScopeBranch.DENY:
        return success(data=[])
    if branch in (ScopeBranch.REGION, ScopeBranch.DEPARTMENT):
        if not current_region_code:
            return success(data=[])
        q = q.filter(ServiceCenter.region_code == current_region_code)
    if regionCode:
        q = q.filter(ServiceCenter.region_code == regionCode)
    centers = q.order_by(ServiceCenter.region_code, ServiceCenter.id).all()
    return success(data=[_service_center_to_dict(item) for item in centers])


@router.get("/service-centers/page", summary="服务中心分页列表")
def list_service_centers_page(
    current: CurrentAdmin,
    db: Session = Depends(get_db),
    regionCode: str | None = Query(None),
    centerName: str | None = Query(None),
    status: str | None = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=200),
):
    q = db.query(ServiceCenter).filter(ServiceCenter.deleted_flag == 0)
    current_region_code = current.get("region_code")
    branch = resolve_scope_branch(current.get("data_scope"))
    if branch == ScopeBranch.DENY:
        return paginated(records=[], total=0, page_no=pageNo, page_size=pageSize)
    if branch in (ScopeBranch.REGION, ScopeBranch.DEPARTMENT):
        if not current_region_code:
            return paginated(records=[], total=0, page_no=pageNo, page_size=pageSize)
        q = q.filter(ServiceCenter.region_code == current_region_code)
    if regionCode:
        q = q.filter(ServiceCenter.region_code == regionCode)
    if centerName:
        q = q.filter(ServiceCenter.center_name.contains(centerName))
    if status:
        q = q.filter(ServiceCenter.status == status)
    total = q.count()
    records = q.order_by(ServiceCenter.region_code, ServiceCenter.id)\
        .offset((pageNo - 1) * pageSize).limit(pageSize).all()
    return paginated(
        records=[_service_center_to_dict(item) for item in records],
        total=total,
        page_no=pageNo,
        page_size=pageSize,
    )


@router.post("/service-centers", summary="新增服务中心")
def create_service_center(body: dict, current: dict = Depends(require_permissions(Permission.DICT_MANAGE)), db: Session = Depends(get_db)):
    center_name = (body.get("centerName") or "").strip()
    region_code = (body.get("regionCode") or "").strip()
    region_name = (body.get("regionName") or "").strip()
    if not center_name or not region_code or not region_name:
        raise ParamException("中心名称、所属区划不能为空")
    exists = db.query(ServiceCenter).filter(
        ServiceCenter.center_name == center_name,
        ServiceCenter.region_code == region_code,
        ServiceCenter.deleted_flag == 0,
    ).first()
    if exists:
        raise ParamException("该区划下已存在同名服务中心")
    item = ServiceCenter(
        center_name=center_name,
        region_code=region_code,
        region_name=region_name,
        address=body.get("address") or None,
        contact_name=body.get("contactName") or None,
        contact_phone=body.get("contactPhone") or None,
        status=body.get("status") or "ENABLED",
    )
    db.add(item)
    _write_service_center_log(db, current, "SERVICE_CENTER_CREATE", center_name)
    db.commit()
    db.refresh(item)
    return success(data=_service_center_to_dict(item), message="新增成功")


@router.patch("/service-centers/{center_id}/status", summary="启用/停用服务中心")
def toggle_service_center_status(center_id: int, body: dict, current: dict = Depends(require_permissions(Permission.DICT_MANAGE)), db: Session = Depends(get_db)):
    item = db.query(ServiceCenter).filter(
        ServiceCenter.id == center_id,
        ServiceCenter.deleted_flag == 0,
    ).first()
    if not item:
        raise NotFoundException("服务中心不存在")
    status = body.get("status")
    if status not in ["ENABLED", "DISABLED"]:
        raise ParamException("无效的状态值")
    item.status = status
    item.updated_at = datetime.utcnow()
    op_type = "SERVICE_CENTER_ENABLE" if status == "ENABLED" else "SERVICE_CENTER_DISABLE"
    _write_service_center_log(db, current, op_type, item.center_name)
    db.commit()
    db.refresh(item)
    return success(data=_service_center_to_dict(item), message="操作成功")


@router.put("/service-centers/{center_id}", summary="修改服务中心")
def update_service_center(center_id: int, body: dict, current: dict = Depends(require_permissions(Permission.DICT_MANAGE)), db: Session = Depends(get_db)):
    item = db.query(ServiceCenter).filter(
        ServiceCenter.id == center_id,
        ServiceCenter.deleted_flag == 0,
    ).first()
    if not item:
        raise NotFoundException("服务中心不存在")
    center_name = (body.get("centerName", item.center_name) or "").strip()
    region_code = (body.get("regionCode", item.region_code) or "").strip()
    region_name = (body.get("regionName", item.region_name) or "").strip()
    if not center_name or not region_code or not region_name:
        raise ParamException("中心名称、所属区划不能为空")
    exists = db.query(ServiceCenter).filter(
        ServiceCenter.center_name == center_name,
        ServiceCenter.region_code == region_code,
        ServiceCenter.deleted_flag == 0,
        ServiceCenter.id != center_id,
    ).first()
    if exists:
        raise ParamException("该区划下已存在同名服务中心")
    item.center_name = center_name
    item.region_code = region_code
    item.region_name = region_name
    item.address = body.get("address") or None
    item.contact_name = body.get("contactName") or None
    item.contact_phone = body.get("contactPhone") or None
    if "status" in body:
        item.status = body.get("status") or "ENABLED"
    item.updated_at = datetime.utcnow()
    _write_service_center_log(db, current, "SERVICE_CENTER_UPDATE", center_name)
    db.commit()
    db.refresh(item)
    return success(data=_service_center_to_dict(item), message="修改成功")


@router.get("/me", summary="获取当前管理端用户信息")
def get_admin_me(current: CurrentAdmin, db: Session = Depends(get_db)):
    user_id = current.get("user_id")
    if not user_id:
        raise NotFoundException("用户信息不存在")

    # admin_source 缺失（历史 token）或非 "BSP" 一律按 mock-login 的 sys_user_snapshot
    # 处理，保持旧行为不变；正式统一身份认证登录签发的 token 带 admin_source="BSP"，
    # 查 sys_admin_user。两张表主键空间独立，必须按来源分流，不能混查。
    if current.get("admin_source") == "BSP":
        admin_repo = AdminUserRepository(db)
        admin = admin_repo.get_by_id(user_id)
        if admin is None:
            raise NotFoundException("用户信息不存在")
        return success(data={
            "id": admin.id,
            "platformUserId": admin.bsp_user_id,
            "username": admin.username,
            "realName": admin.real_name,
            "mobile": admin.mobile,
            "departmentId": admin.department_id,
            "departmentName": admin.department_name,
            "regionCode": admin.region_code,
            "regionName": admin.region_name,
            "roleCodes": admin.role_codes.split(",") if admin.role_codes else [],
            "dataScope": admin.data_scope,
            "lastLoginTime": admin.last_login_at.isoformat() if admin.last_login_at else None,
        })

    repo = SysUserSnapshotRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise NotFoundException("用户信息不存在")

    return success(data={
        "id": user.id,
        "platformUserId": user.platform_user_id,
        "username": user.username,
        "realName": user.real_name,
        "mobile": user.mobile,
        "departmentId": user.department_id,
        "departmentName": user.department_name,
        "regionCode": user.region_code,
        "regionName": user.region_name,
        "roleCodes": user.role_codes.split(",") if user.role_codes else [],
        "dataScope": user.data_scope,
        "lastLoginTime": user.last_login_time.isoformat() if user.last_login_time else None,
    })
