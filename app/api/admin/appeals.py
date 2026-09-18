from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.constants.permission import Permission
from app.core.permission import require_permissions
from app.core.response import success, paginated
from app.schemas.appeal import (
    AppealAcceptRequest,
    AppealReturnSupplementRequest,
    AppealRejectRequest,
    AppealCenterHandleRequest,
    AppealAssignRequest,
    AppealDeptReplyRequest,
    AppealReviewReplyRequest,
    AppealFollowupRequest,
    AppealCompleteRequest,
)
from app.services.appeal_service import AppealService

router = APIRouter()


def _build_admin_operator(current: dict) -> dict:
    return {
        "operator_type": "USER",
        "operator_id": str(current.get("user_id", current.get("platform_user_id", ""))),
        "operator_name": current.get("real_name", ""),
        "department_id": current.get("department_id"),
        "department_name": current.get("department_name"),
        "user_id_str": str(current.get("user_id", "")),
        "real_name": current.get("real_name", ""),
        # 供 DataPermissionService 做数据权限校验用（见 A2 整改）
        "data_scope": current.get("data_scope"),
        "region_code": current.get("region_code"),
        "role_codes": current.get("role_codes"),
    }


@router.get("", summary="诉求列表（管理端）")
def list_appeals(
    current: dict = Depends(require_permissions(Permission.APPEAL_VIEW)),
    db: Session = Depends(get_db),
    enterpriseName: Optional[str] = Query(None),
    creditCode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    appealTypeCode: Optional[str] = Query(None),
    regionCode: Optional[str] = Query(None),
    responsibleDeptId: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = AppealService(db)
    query = {
        "enterpriseName": enterpriseName,
        "creditCode": creditCode,
        "status": status,
        "appealTypeCode": appealTypeCode,
        "regionCode": regionCode,
        "responsibleDeptId": responsibleDeptId,
        "startDate": startDate,
        "endDate": endDate,
        "pageNo": pageNo,
        "pageSize": pageSize,
    }
    total, records = svc.list_admin_appeals(
        query=query,
        data_scope=current.get("data_scope", "ALL"),
        current_region_code=current.get("region_code", ""),
        current_dept_id=current.get("department_id", ""),
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/{appeal_id}", summary="诉求详情（管理端）")
def get_appeal_detail(
    appeal_id: int,
    current: dict = Depends(require_permissions(Permission.APPEAL_VIEW)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    result = svc.get_appeal_detail_for_admin(appeal_id, _build_admin_operator(current))
    return success(data=result)


@router.post("/{appeal_id}/accept", summary="受理诉求")
def accept_appeal(
    appeal_id: int,
    body: AppealAcceptRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.accept_appeal(appeal_id, body.model_dump(), operator)
    return success(data=result, message="受理成功")


@router.post("/{appeal_id}/return-supplement", summary="退回补充")
def return_supplement(
    appeal_id: int,
    body: AppealReturnSupplementRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.return_supplement(appeal_id, body.model_dump(), operator)
    return success(data=result, message="已退回")


@router.post("/{appeal_id}/reject", summary="不予受理")
def reject_appeal(
    appeal_id: int,
    body: AppealRejectRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.reject_appeal(appeal_id, body.model_dump(), operator)
    return success(data=result, message="已不予受理")


@router.post("/{appeal_id}/center-handle", summary="企服中心自行办理")
def center_handle(
    appeal_id: int,
    body: AppealCenterHandleRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.center_handle(appeal_id, body.model_dump(), operator)
    return success(data=result, message="办理完成")


@router.post("/{appeal_id}/assign", summary="分派责任部门")
def assign_dept(
    appeal_id: int,
    body: AppealAssignRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.assign_dept(appeal_id, body.model_dump(), operator)
    return success(data=result, message="分派成功")


@router.post("/{appeal_id}/department-reply", summary="部门反馈")
def dept_reply(
    appeal_id: int,
    body: AppealDeptReplyRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE, Permission.APPEAL_DEPT_REPLY)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.dept_reply(appeal_id, body.model_dump(), operator)
    return success(data=result, message="反馈成功")


@router.post("/{appeal_id}/review-reply", summary="审核部门反馈")
def review_reply(
    appeal_id: int,
    body: AppealReviewReplyRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.review_reply(appeal_id, body.model_dump(by_alias=False), operator)
    return success(data=result, message="审核完成")


@router.post("/{appeal_id}/followup", summary="不满意回访记录")
def add_followup(
    appeal_id: int,
    body: AppealFollowupRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.add_followup(appeal_id, body.model_dump(), operator)
    return success(data=result, message="回访记录已保存")


@router.post("/{appeal_id}/complete", summary="办结")
def complete_appeal(
    appeal_id: int,
    body: AppealCompleteRequest,
    current: dict = Depends(require_permissions(Permission.APPEAL_HANDLE)),
    db: Session = Depends(get_db),
):
    svc = AppealService(db)
    operator = _build_admin_operator(current)
    result = svc.complete_appeal(appeal_id, body.model_dump(), operator)
    return success(data=result, message="已办结")
