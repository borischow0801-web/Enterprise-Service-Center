from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.constants.permission import Permission
from app.core.permission import require_permissions
from app.core.response import success, paginated
from app.schemas.gov_meeting import (
    GovMeetingAuditRequest, GovMeetingArrangeRequest,
    GovMeetingRecordRequest, GovMeetingConfirmRequest,
    GovMeetingCompleteRequest, GovMeetingFinishRequest,
)
from app.services.gov_meeting_service import GovMeetingService

router = APIRouter()


def _op(current: dict) -> dict:
    return {
        "operator_type": "USER",
        "operator_id": str(current.get("user_id", current.get("platform_user_id", ""))),
        "operator_name": current.get("real_name", ""),
        "department_id": current.get("department_id"),
        "department_name": current.get("department_name"),
        "data_scope": current.get("data_scope"),
        "region_code": current.get("region_code"),
        "role_codes": current.get("role_codes"),
    }


# ── 静态路由（必须在 /{apply_id} 之前）────────────────────────────────────────

@router.get("", summary="政企约见列表（管理端）")
def list_applies(
    current: dict = Depends(require_permissions(Permission.GOV_MEETING_VIEW)),
    db: Session = Depends(get_db),
    enterpriseName: Optional[str] = Query(None),
    creditCode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    regionCode: Optional[str] = Query(None),
    serviceCenterId: Optional[int] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = GovMeetingService(db)
    total, records = svc.list_applies_admin(
        {
            "enterpriseName": enterpriseName, "creditCode": creditCode,
            "status": status, "startDate": startDate, "endDate": endDate,
            "regionCode": regionCode, "serviceCenterId": serviceCenterId,
            "pageNo": pageNo, "pageSize": pageSize,
        },
        data_scope=current.get("data_scope", "ALL"),
        current_region_code=current.get("region_code", ""),
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


# ── 动态路由 ─────────────────────────────────────────────────────────────────

@router.get("/{apply_id}", summary="政企约见详情（管理端）")
def get_apply_detail(apply_id: int, current: dict = Depends(require_permissions(Permission.GOV_MEETING_VIEW)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    return success(data=svc.get_apply_detail_admin(apply_id, _op(current)))


@router.post("/{apply_id}/audit", summary="审核政企约见（受理/驳回/退回补正）")
def audit_apply(apply_id: int, body: GovMeetingAuditRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.audit_apply(apply_id, body.model_dump(), _op(current))
    return success(data=result, message="操作成功")


@router.post("/{apply_id}/arrange", summary="安排约见")
def arrange_apply(apply_id: int, body: GovMeetingArrangeRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.arrange_apply(apply_id, body.model_dump(exclude_none=True), _op(current))
    return success(data=result, message="约见安排成功")


@router.put("/{apply_id}/arrangements/{arr_id}", summary="修改约见安排")
def update_arrangement(apply_id: int, arr_id: int, body: GovMeetingArrangeRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.update_arrangement(apply_id, arr_id, body.model_dump(exclude_none=True), _op(current))
    return success(data=result, message="修改成功")


@router.post("/{apply_id}/confirm", summary="确认并通知企业（ARRANGED→WAIT_MEETING）")
def confirm_apply(apply_id: int, body: GovMeetingConfirmRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.confirm_apply(apply_id, body.model_dump(exclude_none=True), _op(current))
    return success(data=result, message="已确认通知企业")


@router.post("/{apply_id}/complete", summary="标记约见完成（WAIT_MEETING→MEETING_COMPLETED）")
def complete_apply(apply_id: int, body: GovMeetingCompleteRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.complete_apply(apply_id, body.model_dump(exclude_none=True), _op(current))
    return success(data=result, message="约见已完成")


@router.post("/{apply_id}/record", summary="填写约见纪要")
def add_record(apply_id: int, body: GovMeetingRecordRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.add_record(apply_id, body.model_dump(exclude_none=True), _op(current))
    return success(data=result, message="纪要保存成功")


@router.post("/{apply_id}/finish", summary="办结（触发评价或直接办结）")
def finish_apply(apply_id: int, body: GovMeetingFinishRequest, current: dict = Depends(require_permissions(Permission.GOV_MEETING_HANDLE)), db: Session = Depends(get_db)):
    svc = GovMeetingService(db)
    result = svc.finish_apply(apply_id, body.model_dump(), _op(current))
    return success(data=result, message="操作成功")
