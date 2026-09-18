from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.deps import CurrentAdmin
from app.constants.permission import Permission
from app.core.permission import require_permissions
from app.core.response import success, paginated
from app.schemas.meeting_room import (
    BookingApproveRequest, BookingRejectRequest, BookingReturnSupplementRequest,
    BookingCompleteRequest, BookingNoShowRequest,
)
from app.services.meeting_room_service import MeetingRoomService

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


@router.get("", summary="预约审核列表（管理端）")
def list_bookings(
    current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)),
    db: Session = Depends(get_db),
    roomId: Optional[int] = Query(None),
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
    svc = MeetingRoomService(db)
    total, records = svc.list_bookings_admin(
        {"roomId": roomId, "enterpriseName": enterpriseName, "creditCode": creditCode,
         "status": status, "startDate": startDate, "endDate": endDate,
         "regionCode": regionCode, "serviceCenterId": serviceCenterId,
         "pageNo": pageNo, "pageSize": pageSize},
        data_scope=current.get("data_scope", "ALL"),
        current_region_code=current.get("region_code", ""),
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/ledger", summary="预约台账查询")
def get_ledger(
    current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)),
    db: Session = Depends(get_db),
    regionCode: Optional[str] = Query(None),
    serviceCenterId: Optional[int] = Query(None),
    roomId: Optional[int] = Query(None),
    enterpriseName: Optional[str] = Query(None),
    creditCode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(50, ge=1, le=200),
):
    svc = MeetingRoomService(db)
    total, records = svc.list_bookings_admin(
        {"roomId": roomId, "enterpriseName": enterpriseName, "creditCode": creditCode,
         "status": status, "startDate": startDate, "endDate": endDate,
         "regionCode": regionCode, "serviceCenterId": serviceCenterId,
         "pageNo": pageNo, "pageSize": pageSize},
        data_scope=current.get("data_scope", "ALL"),
        current_region_code=current.get("region_code", ""),
    )
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/export", summary="预约台账导出（TODO：改为真实Excel）")
def export_ledger(
    current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)),
    db: Session = Depends(get_db),
    regionCode: Optional[str] = Query(None),
    serviceCenterId: Optional[int] = Query(None),
    roomId: Optional[int] = Query(None),
    enterpriseName: Optional[str] = Query(None),
    creditCode: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None),
):
    # TODO: 后续改为生成真实 Excel 文件并返回 FileResponse
    svc = MeetingRoomService(db)
    _, records = svc.list_bookings_admin(
        {"roomId": roomId, "enterpriseName": enterpriseName, "creditCode": creditCode,
         "status": status, "startDate": startDate, "endDate": endDate,
         "regionCode": regionCode, "serviceCenterId": serviceCenterId,
         "pageNo": 1, "pageSize": 10000},
        data_scope=current.get("data_scope", "ALL"),
        current_region_code=current.get("region_code", ""),
    )
    return success(data={"records": records, "total": len(records), "note": "TODO: 后续改为Excel文件导出"})


@router.get("/{booking_id}", summary="预约详情（管理端）")
def get_booking_detail(booking_id: int, current: dict = Depends(require_permissions(Permission.MEETING_ROOM_VIEW)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    return success(data=svc.get_booking_detail_admin(booking_id, _op(current)))


@router.post("/{booking_id}/approve", summary="审核通过")
def approve_booking(booking_id: int, body: BookingApproveRequest, current: dict = Depends(require_permissions(Permission.MEETING_BOOKING_HANDLE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.approve_booking(booking_id, body.model_dump(), _op(current))
    return success(data=result, message="审核通过")


@router.post("/{booking_id}/reject", summary="审核驳回")
def reject_booking(booking_id: int, body: BookingRejectRequest, current: dict = Depends(require_permissions(Permission.MEETING_BOOKING_HANDLE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.reject_booking(booking_id, body.model_dump(), _op(current))
    return success(data=result, message="已驳回")


@router.post("/{booking_id}/return-supplement", summary="退回补充材料")
def return_supplement(booking_id: int, body: BookingReturnSupplementRequest, current: dict = Depends(require_permissions(Permission.MEETING_BOOKING_HANDLE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.return_supplement(booking_id, body.model_dump(), _op(current))
    return success(data=result, message="已退回")


@router.post("/{booking_id}/complete", summary="确认使用完成")
def complete_booking(booking_id: int, body: BookingCompleteRequest, current: dict = Depends(require_permissions(Permission.MEETING_BOOKING_HANDLE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.complete_booking(booking_id, body.model_dump(), _op(current))
    return success(data=result, message="已确认完成")


@router.post("/{booking_id}/no-show", summary="标记爽约")
def no_show_booking(booking_id: int, body: BookingNoShowRequest, current: dict = Depends(require_permissions(Permission.MEETING_BOOKING_HANDLE)), db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.no_show_booking(booking_id, body.model_dump(), _op(current))
    return success(data=result, message="已标记爽约")
