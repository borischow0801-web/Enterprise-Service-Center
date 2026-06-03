from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ── Enterprise-side requests ──────────────────────────────────────────────────

class GovMeetingSubmitRequest(BaseModel):
    contactName: str = Field(..., max_length=100)
    contactPhone: str = Field(..., max_length=64)
    topicCode: Optional[str] = None
    topicName: Optional[str] = None
    meetingLevel: Optional[str] = None
    expectedLevelCode: Optional[str] = None
    expectedLevelName: Optional[str] = None
    title: Optional[str] = Field(None, max_length=300)
    content: Optional[str] = None          # 映射到 meeting_content
    discussionItem: Optional[str] = None
    urgencyLevel: Optional[str] = None
    industryCode: Optional[str] = None
    industryName: Optional[str] = None
    registeredAddress: Optional[str] = None
    description: Optional[str] = None     # 兼容旧字段（申请说明）
    commitmentChecked: int = Field(..., ge=1, le=1, description="必须为1")
    regionCode: str
    regionName: str
    serviceCenterId: Optional[int] = None
    serviceCenterName: Optional[str] = None
    attachmentIds: Optional[List[int]] = None


class GovMeetingModifyRequest(BaseModel):
    contactName: Optional[str] = Field(None, max_length=100)
    contactPhone: Optional[str] = Field(None, max_length=64)
    topicCode: Optional[str] = None
    topicName: Optional[str] = None
    meetingLevel: Optional[str] = None
    expectedLevelCode: Optional[str] = None
    expectedLevelName: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    discussionItem: Optional[str] = None
    urgencyLevel: Optional[str] = None
    description: Optional[str] = None
    attachmentIds: Optional[List[int]] = None


class GovMeetingSupplementRequest(BaseModel):
    content: Optional[str] = None          # 补充说明内容
    description: Optional[str] = None      # 兼容旧字段
    attachmentIds: Optional[List[int]] = None


class GovMeetingEvaluationRequest(BaseModel):
    satisfaction: str
    score: int = Field(..., ge=1, le=5)
    resolvedFlag: Optional[int] = None
    comment: Optional[str] = Field(None, max_length=1000)


# ── Admin-side requests ───────────────────────────────────────────────────────

class GovMeetingAuditRequest(BaseModel):
    auditType: str  # ACCEPT / REJECT / RETURN_SUPPLEMENT
    rejectReasonCode: Optional[str] = None
    rejectReasonName: Optional[str] = None
    finalLevelCode: Optional[str] = None   # 后台研判约见层级（ACCEPT 时填写）
    finalLevelName: Optional[str] = None
    opinion: Optional[str] = None


class ParticipantItem(BaseModel):
    participantType: str   # GOV / ENTERPRISE
    participantName: str
    participantTitle: Optional[str] = None
    participantDeptId: Optional[str] = None
    participantDeptName: Optional[str] = None
    contactPhone: Optional[str] = None
    roleName: Optional[str] = None
    sortNo: Optional[int] = 0


class GovMeetingArrangeRequest(BaseModel):
    meetingDate: Optional[datetime] = None
    meetingPlace: Optional[str] = None
    meetingMethod: Optional[str] = None
    startTime: Optional[datetime] = None
    endTime: Optional[datetime] = None
    hostDeptId: Optional[str] = None
    hostDeptName: Optional[str] = None
    notes: Optional[str] = None
    govContactName: Optional[str] = None
    govContactPhone: Optional[str] = None
    remark: Optional[str] = None
    participants: Optional[List[ParticipantItem]] = None


class GovMeetingRecordRequest(BaseModel):
    arrangementId: Optional[int] = None
    content: str
    conclusions: Optional[str] = None
    followUpItems: Optional[str] = None
    recordTime: Optional[datetime] = None


class GovMeetingConfirmRequest(BaseModel):
    opinion: Optional[str] = None


class GovMeetingCompleteRequest(BaseModel):
    meetingAt: Optional[datetime] = None
    opinion: Optional[str] = None


class GovMeetingFinishRequest(BaseModel):
    sendEvaluation: Optional[int] = Field(1, description="1=发送评价通知 0=直接办结")
    opinion: Optional[str] = None
