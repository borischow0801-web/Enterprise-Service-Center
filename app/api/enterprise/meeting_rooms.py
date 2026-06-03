from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.deps import CurrentEnterprise
from app.core.response import success, paginated
from app.services.meeting_room_service import MeetingRoomService

router = APIRouter()


@router.get("", summary="会议室列表（企业端）")
def list_rooms(
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
    regionCode: Optional[str] = Query(None),
    capacityMin: Optional[int] = Query(None),
    facility: Optional[str] = Query(None),
    roomType: Optional[str] = Query(None),
    pageNo: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    svc = MeetingRoomService(db)
    total, records = svc.list_rooms_enterprise(regionCode, capacityMin, facility, roomType, pageNo, pageSize)
    return paginated(records=records, total=total, page_no=pageNo, page_size=pageSize)


@router.get("/{room_id}/calendar", summary="查询会议室可预约时间")
def get_room_calendar(
    room_id: int,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
    startDate: str = Query(...),
    endDate: str = Query(...),
):
    svc = MeetingRoomService(db)
    return success(data=svc.get_room_calendar(room_id, startDate, endDate))


@router.get("/{room_id}/material-rules", summary="查询材料要求")
def get_material_rules(
    room_id: int,
    current: CurrentEnterprise,
    db: Session = Depends(get_db),
    enterpriseType: Optional[str] = Query(None),
):
    svc = MeetingRoomService(db)
    return success(data=svc.get_material_rules_enterprise(room_id, enterpriseType))


@router.get("/{room_id}", summary="会议室详情（企业端）")
def get_room_detail(room_id: int, current: CurrentEnterprise, db: Session = Depends(get_db)):
    svc = MeetingRoomService(db)
    return success(data=svc.get_room_detail_enterprise(room_id))
