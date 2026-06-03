import { get, post, put } from './request'
import type { PageResult } from './appeal'

// ── Interfaces ────────────────────────────────────────────────────────────────

export interface GovMeetingApply {
  id: number
  applyNo: string
  enterpriseId: number
  enterpriseName: string
  creditCode: string
  contactName: string
  contactPhone: string
  topicCode?: string
  topicName?: string
  meetingLevel?: string
  expectedLevelCode?: string
  expectedLevelName?: string
  finalLevelCode?: string
  finalLevelName?: string
  description: string
  commitmentChecked?: number
  regionCode: string
  regionName: string
  serviceCenterId?: number
  serviceCenterName?: string
  status: string
  rejectReasonCode?: string
  rejectReasonName?: string
  rejectOpinion?: string
  submittedAt?: string
  acceptedAt?: string
  arrangedAt?: string
  meetingAt?: string
  completedAt?: string
  evaluatedAt?: string
  finishedAt?: string
  createdAt?: string
}

export interface GovMeetingParticipant {
  id?: number
  participantType: string   // GOV / ENTERPRISE
  participantName: string
  participantTitle?: string
  participantDeptId?: string
  participantDeptName?: string
  contactPhone?: string
  roleName?: string
  sortNo?: number
}

export interface GovMeetingArrangement {
  id: number
  applyId: number
  meetingDate?: string
  meetingPlace?: string
  meetingMethod?: string
  startTime?: string
  endTime?: string
  hostDeptId?: string
  hostDeptName?: string
  notes?: string
  govContactName?: string
  govContactPhone?: string
  remark?: string
  confirmedFlag: number
  participants: GovMeetingParticipant[]
}

export interface GovMeetingRecord {
  id: number
  applyId: number
  arrangementId?: number
  content: string
  conclusions?: string
  followUpItems?: string
  recorderName?: string
  recordTime?: string
  createdAt?: string
}

export interface GovMeetingAudit {
  id: number
  applyId: number
  actionType: string
  actionName: string
  beforeStatus?: string
  afterStatus?: string
  opinion?: string
  operatorType?: string
  operatorId?: string
  operatorName?: string
  operatorDeptId?: string
  operatorDeptName?: string
  createdAt: string
}

export interface GovMeetingAttachment {
  id: number
  originalName: string
  fileExt?: string
  fileSize?: number
  storagePath?: string
}

export interface GovMeetingEvaluation {
  id: number
  satisfaction: string
  score: number
  resolvedFlag?: number
  comment?: string
  createdAt?: string
}

export interface GovMeetingDetail extends GovMeetingApply {
  arrangement?: GovMeetingArrangement | null
  auditTrail: GovMeetingAudit[]
  records: GovMeetingRecord[]
  attachments: GovMeetingAttachment[]
  evaluation?: GovMeetingEvaluation | null
}

export interface GovMeetingListParams {
  enterpriseName?: string
  creditCode?: string
  status?: string
  topicCode?: string
  regionCode?: string
  serviceCenterId?: number
  startDate?: string
  endDate?: string
  pageNo?: number
  pageSize?: number
}

// ── API functions ─────────────────────────────────────────────────────────────

export function getGovMeetingList(params: GovMeetingListParams): Promise<PageResult<GovMeetingApply>> {
  return get<PageResult<GovMeetingApply>>('/api/admin/gov-meetings', params as Record<string, unknown>)
}

export function getGovMeetingDetail(id: number): Promise<GovMeetingDetail> {
  return get<GovMeetingDetail>(`/api/admin/gov-meetings/${id}`)
}

/** 审核：auditType = ACCEPT | RETURN_SUPPLEMENT | REJECT */
export function auditGovMeeting(id: number, data: {
  auditType: 'ACCEPT' | 'RETURN_SUPPLEMENT' | 'REJECT'
  opinion?: string
  rejectReasonCode?: string
  rejectReasonName?: string
  finalLevelCode?: string
  finalLevelName?: string
}): Promise<GovMeetingApply> {
  return post<GovMeetingApply>(`/api/admin/gov-meetings/${id}/audit`, data)
}

/** 安排约见（PENDING_ARRANGE → ARRANGED） */
export function arrangeGovMeeting(id: number, data: {
  meetingDate?: string
  meetingPlace?: string
  meetingMethod?: string
  startTime?: string
  endTime?: string
  hostDeptId?: string
  hostDeptName?: string
  notes?: string
  govContactName?: string
  govContactPhone?: string
  remark?: string
  participants?: GovMeetingParticipant[]
}): Promise<GovMeetingArrangement> {
  return post<GovMeetingArrangement>(`/api/admin/gov-meetings/${id}/arrange`, data)
}

/** 修改约见安排（ARRANGED / WAIT_MEETING，不变状态） */
export function updateGovMeetingArrangement(id: number, arrId: number, data: {
  meetingDate?: string
  meetingPlace?: string
  meetingMethod?: string
  startTime?: string
  endTime?: string
  hostDeptId?: string
  hostDeptName?: string
  notes?: string
  govContactName?: string
  govContactPhone?: string
  remark?: string
  participants?: GovMeetingParticipant[]
}): Promise<GovMeetingArrangement> {
  return put<GovMeetingArrangement>(`/api/admin/gov-meetings/${id}/arrangements/${arrId}`, data)
}

/** 确认并通知企业（ARRANGED → WAIT_MEETING） */
export function confirmGovMeeting(id: number, data: { opinion?: string }): Promise<GovMeetingApply> {
  return post<GovMeetingApply>(`/api/admin/gov-meetings/${id}/confirm`, data)
}

/** 标记约见完成（WAIT_MEETING → MEETING_COMPLETED） */
export function completeGovMeeting(id: number, data: { meetingAt?: string; opinion?: string }): Promise<GovMeetingApply> {
  return post<GovMeetingApply>(`/api/admin/gov-meetings/${id}/complete`, data)
}

/** 填写约见纪要（不改变状态） */
export function recordGovMeeting(id: number, data: {
  arrangementId?: number
  content: string
  conclusions?: string
  followUpItems?: string
  recordTime?: string
}): Promise<GovMeetingRecord> {
  return post<GovMeetingRecord>(`/api/admin/gov-meetings/${id}/record`, data)
}

/** 办结：sendEvaluation=1 → PENDING_EVALUATION；sendEvaluation=0 → COMPLETED */
export function finishGovMeeting(id: number, data: { sendEvaluation?: number; opinion?: string }): Promise<GovMeetingApply> {
  return post<GovMeetingApply>(`/api/admin/gov-meetings/${id}/finish`, data)
}
