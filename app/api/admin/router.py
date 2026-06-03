from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.core.response import success
from app.core.exceptions import NotFoundException
from app.repositories.sys_user_repo import SysUserSnapshotRepository
from app.api.admin.appeals import router as admin_appeals_router
from app.api.admin.meeting_rooms import router as admin_meeting_rooms_router
from app.api.admin.meeting_bookings import router as admin_meeting_bookings_router
from app.api.admin.gov_meetings import router as admin_gov_meetings_router
from app.api.admin.dictionaries import router as admin_dict_router
from app.api.admin.operation_logs import router as admin_op_log_router
from app.api.admin.dashboard import router as admin_dashboard_router

router = APIRouter()

router.include_router(admin_appeals_router, prefix="/appeals", tags=["管理端-诉求"])
router.include_router(admin_meeting_rooms_router, prefix="/meeting-rooms", tags=["管理端-会议室"])
router.include_router(admin_meeting_bookings_router, prefix="/meeting-bookings", tags=["管理端-预约"])
router.include_router(admin_gov_meetings_router, prefix="/gov-meetings", tags=["管理端-政企约见"])
router.include_router(admin_dict_router, prefix="/dictionaries", tags=["管理端-字典"])
router.include_router(admin_op_log_router, prefix="/operation-logs", tags=["管理端-操作日志"])
router.include_router(admin_dashboard_router, prefix="/dashboard", tags=["管理端-工作台"])


@router.get("/me", summary="获取当前管理端用户信息")
def get_admin_me(current: CurrentAdmin, db: Session = Depends(get_db)):
    user_id = current.get("user_id")
    if not user_id:
        raise NotFoundException("用户信息不存在")

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
