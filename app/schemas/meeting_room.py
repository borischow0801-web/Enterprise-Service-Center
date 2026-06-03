from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List


# ── Admin room management ─────────────────────────────────────────────────────

class RoomCreateRequest(BaseModel):
    roomName: str = Field(..., max_length=200)
    roomType: Optional[str] = None
    regionCode: str
    regionName: str
    serviceCenterId: Optional[int] = None
    serviceCenterName: Optional[str] = None
    address: Optional[str] = None
    capacity: int = Field(..., ge=1)
    facilities: Optional[List[str]] = None
    description: Optional[str] = None
    coverAttachmentId: Optional[int] = None
    imageAttachmentIds: Optional[List[int]] = None
    bookingNotice: Optional[str] = None


class RoomUpdateRequest(BaseModel):
    roomName: Optional[str] = Field(None, max_length=200)
    roomType: Optional[str] = None
    address: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    facilities: Optional[List[str]] = None
    description: Optional[str] = None
    coverAttachmentId: Optional[int] = None
    imageAttachmentIds: Optional[List[int]] = None
    bookingNotice: Optional[str] = None


class RoomStatusRequest(BaseModel):
    status: str  # ENABLED or DISABLED


class OpenRuleItem(BaseModel):
    weekday: int = Field(..., ge=1, le=7)
    openFlag: int = Field(..., ge=0, le=1)
    startTime: Optional[str] = None
    endTime: Optional[str] = None


class OpenRulesRequest(BaseModel):
    rules: List[OpenRuleItem]


class SpecialDateRequest(BaseModel):
    regionCode: str
    serviceCenterId: Optional[int] = None
    specialDate: str  # YYYY-MM-DD
    dateType: str
    openFlag: int = Field(..., ge=0, le=1)
    reason: Optional[str] = None


class OccupyRequest(BaseModel):
    roomId: int
    occupyTitle: str = Field(..., max_length=200)
    occupyReason: Optional[str] = None
    startTime: datetime
    endTime: datetime


class MaterialRuleCreateRequest(BaseModel):
    roomId: Optional[int] = None           # deprecated; region-based config preferred
    regionCode: str = Field(..., max_length=32)
    regionName: Optional[str] = Field(None, max_length=100)
    serviceCenterId: Optional[int] = None
    serviceCenterName: Optional[str] = Field(None, max_length=100)
    enterpriseType: Optional[str] = None
    materialName: str = Field(..., max_length=200)
    materialCode: str = Field(..., max_length=100)
    requiredFlag: int = Field(1, ge=0, le=1)
    templateAttachmentId: Optional[int] = None
    description: Optional[str] = None
    sortNo: int = 0


class MaterialRuleUpdateRequest(BaseModel):
    regionCode: Optional[str] = Field(None, max_length=32)
    regionName: Optional[str] = Field(None, max_length=100)
    serviceCenterId: Optional[int] = None
    serviceCenterName: Optional[str] = Field(None, max_length=100)
    materialName: Optional[str] = Field(None, max_length=200)
    requiredFlag: Optional[int] = Field(None, ge=0, le=1)
    templateAttachmentId: Optional[int] = None
    description: Optional[str] = None
    enabled: Optional[int] = Field(None, ge=0, le=1)
    sortNo: Optional[int] = None


# ── Booking ───────────────────────────────────────────────────────────────────

class BookingMaterialItem(BaseModel):
    materialCode: str
    materialName: Optional[str] = None
    attachmentIds: List[int] = Field(default_factory=list)


class BookingCreateRequest(BaseModel):
    roomId: int
    meetingSubject: str = Field(..., max_length=200)
    participantCount: int = Field(..., ge=1)
    contactName: str = Field(..., max_length=100)
    contactPhone: str = Field(..., max_length=64)
    startTime: datetime
    endTime: datetime
    enterpriseType: Optional[str] = None
    supportItems: Optional[List[str]] = None
    materials: Optional[List[BookingMaterialItem]] = None
    attachmentIds: Optional[List[int]] = None


class BookingCancelRequest(BaseModel):
    cancelReason: str


class BookingSupplementRequest(BaseModel):
    materials: Optional[List[BookingMaterialItem]] = None
    attachmentIds: Optional[List[int]] = None
    remark: Optional[str] = None


class BookingApproveRequest(BaseModel):
    auditOpinion: Optional[str] = None


class BookingRejectRequest(BaseModel):
    auditOpinion: str


class BookingReturnSupplementRequest(BaseModel):
    auditOpinion: str


class BookingCompleteRequest(BaseModel):
    actualStartTime: Optional[datetime] = None
    actualEndTime: Optional[datetime] = None
    remark: Optional[str] = None


class BookingNoShowRequest(BaseModel):
    reason: Optional[str] = None


# ── Query params ──────────────────────────────────────────────────────────────

class EnterpriseBookingListQuery(BaseModel):
    status: Optional[str] = None
    pageNo: int = 1
    pageSize: int = 10


class AdminBookingListQuery(BaseModel):
    roomId: Optional[int] = None
    enterpriseName: Optional[str] = None
    creditCode: Optional[str] = None
    status: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    regionCode: Optional[str] = None
    serviceCenterId: Optional[int] = None
    pageNo: int = 1
    pageSize: int = 10
