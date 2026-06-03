from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.deps import CurrentEnterprise
from app.core.response import success, paginated
from app.schemas.meeting_room import BookingCreateRequest, BookingCancelRequest, BookingSupplementRequest
from app.services.meeting_room_service import MeetingRoomService

router = APIRouter()


@router.post("", summary="提交预约")
def submit_booking(body: BookingCreateRequest, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.submit_booking(current["enterprise_id"], body.model_dump(by_alias=False))
    return success(data=result, message="预约提交成功，请等待审核")


@router.get("", summary="我的预约列表")
def list_bookings(
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = MeetingRoomService(db)
    total, records = svc.list_bookings_enterprise(current["enterprise_id"], status, pageNo, pageSize)
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/{booking_id}", summary="预约详情")
def get_booking_detail(booking_id: int, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    return success(data=svc.get_booking_detail_enterprise(booking_id, current["enterprise_id"]))


@router.post("/{booking_id}/cancel", summary="取消预约")
def cancel_booking(booking_id: int, body: BookingCancelRequest, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    result = svc.cancel_booking_enterprise(booking_id, current["enterprise_id"], body.model_dump())
    return success(data=result, message="预约已取消")


@router.post("/{booking_id}/supplement", summary="补充材料")
def supplement_booking(
    booking_id: int,
    body: BookingSupplementRequest,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
):
    svc = MeetingRoomService(db)
    result = svc.supplement_booking_enterprise(
        booking_id, current["enterprise_id"], body.model_dump(exclude_none=True),
    )
    return success(data=result, message="材料已补充，等待后台重新审核")
