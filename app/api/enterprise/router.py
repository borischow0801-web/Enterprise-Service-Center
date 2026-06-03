from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentEnterprise
from app.core.response import success
from app.core.exceptions import NotFoundException
from app.repositories.enterprise_repo import EnterpriseRepository
from app.api.enterprise.appeals import router as appeals_router
from app.api.enterprise.meeting_rooms import router as meeting_rooms_router
from app.api.enterprise.meeting_bookings import router as meeting_bookings_router
from app.api.enterprise.gov_meetings import router as gov_meetings_router

router = APIRouter()

router.include_router(appeals_router, prefix="/appeals", tags=["企业端-诉求"])
router.include_router(meeting_rooms_router, prefix="/meeting-rooms", tags=["企业端-会议室"])
router.include_router(meeting_bookings_router, prefix="/meeting-bookings", tags=["企业端-预约"])
router.include_router(gov_meetings_router, prefix="/gov-meetings", tags=["企业端-政企约见"])


@router.get("/me", summary="获取当前企业信息")
def get_enterprise_me(current: CurrentEnterprise, db: Session = Depends(get_db)):
    enterprise_id = current.get("enterprise_id")
    if not enterprise_id:
        raise NotFoundException("企业信息不存在")

    repo = EnterpriseRepository(db)
    enterprise = repo.get_by_id(enterprise_id)
    if enterprise is None:
        raise NotFoundException("企业信息不存在")

    return success(data={
        "id": enterprise.id,
        "enterpriseName": enterprise.enterprise_name,
        "creditCode": enterprise.credit_code,
        "legalPersonName": enterprise.legal_person_name,
        "legalPersonMobile": enterprise.legal_person_mobile,
        "industryCode": enterprise.industry_code,
        "industryName": enterprise.industry_name,
        "regionCode": enterprise.region_code,
        "regionName": enterprise.region_name,
        "authSource": enterprise.auth_source,
        "meetingNoShowCount": enterprise.meeting_no_show_count,
        "meetingBookingDisabled": enterprise.meeting_booking_disabled,
        "lastLoginTime": enterprise.last_login_time.isoformat() if enterprise.last_login_time else None,
    })
