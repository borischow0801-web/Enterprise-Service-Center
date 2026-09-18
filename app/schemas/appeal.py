from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ── Enterprise-side requests ──────────────────────────────────────────────────

class AppealSubmitRequest(BaseModel):
    title: str = Field(..., max_length=200)
    content: str
    contactName: str = Field(..., max_length=100)
    contactPhone: str = Field(..., max_length=64)
    industryCode: Optional[str] = None
    industryName: Optional[str] = None
    regionCode: str
    regionName: str
    urgencyLevel: Optional[str] = None
    attachmentIds: Optional[List[int]] = None


class AppealModifyRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    contactName: Optional[str] = Field(None, max_length=100)
    contactPhone: Optional[str] = Field(None, max_length=64)
    industryCode: Optional[str] = None
    industryName: Optional[str] = None
    regionCode: Optional[str] = None
    regionName: Optional[str] = None
    urgencyLevel: Optional[str] = None


class AppealSupplementRequest(BaseModel):
    content: str
    attachmentIds: Optional[List[int]] = None


class AppealEvaluationRequest(BaseModel):
    satisfaction: str
    score: int = Field(..., ge=1, le=5)
    resolvedFlag: Optional[int] = None
    comment: Optional[str] = Field(None, max_length=1000)


# ── Admin-side requests ───────────────────────────────────────────────────────

class AppealAcceptRequest(BaseModel):
    appealTypeCode: str
    appealTypeName: str
    replyDeadline: Optional[datetime] = None
    opinion: Optional[str] = None


class AppealReturnSupplementRequest(BaseModel):
    opinion: str


class AppealRejectRequest(BaseModel):
    reasonCode: Optional[str] = None
    reasonName: Optional[str] = None
    opinion: str


class AppealCenterHandleRequest(BaseModel):
    replyContent: str
    attachmentIds: Optional[List[int]] = None


class AppealAssignRequest(BaseModel):
    assignedDeptId: str
    assignedDeptName: str
    deadline: Optional[datetime] = None
    assignOpinion: Optional[str] = None


class AppealDeptReplyRequest(BaseModel):
    replyContent: str
    attachmentIds: Optional[List[int]] = None


class AppealReviewReplyRequest(BaseModel):
    passed: bool = Field(..., alias="pass")
    opinion: Optional[str] = None
    model_config = {"populate_by_name": True}


class AppealFollowupRequest(BaseModel):
    responsibleDeptId: Optional[str] = None
    responsibleDeptName: Optional[str] = None
    followupMethod: Optional[str] = None
    followupContent: Optional[str] = None
    followupResult: Optional[str] = None


class AppealCompleteRequest(BaseModel):
    remark: Optional[str] = None


# ── Query params ──────────────────────────────────────────────────────────────

class EnterpriseAppealListQuery(BaseModel):
    status: Optional[str] = None
    pageNo: int = 1
    pageSize: int = 10


class AdminAppealListQuery(BaseModel):
    enterpriseName: Optional[str] = None
    creditCode: Optional[str] = None
    status: Optional[str] = None
    appealTypeCode: Optional[str] = None
    regionCode: Optional[str] = None
    responsibleDeptId: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    pageNo: int = 1
    pageSize: int = 10
