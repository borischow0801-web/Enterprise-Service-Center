from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EnterpriseInfo(BaseModel):
    id: int
    enterpriseName: str
    creditCode: str
    legalPersonName: str
    legalPersonMobile: str
    industryCode: Optional[str] = None
    industryName: Optional[str] = None
    regionCode: Optional[str] = None
    regionName: Optional[str] = None
    authSource: str
    meetingNoShowCount: int
    meetingBookingDisabled: int
    lastLoginTime: Optional[datetime] = None

    model_config = {"from_attributes": True}
