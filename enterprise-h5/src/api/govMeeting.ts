import { get, post } from './request'

// ── snake_case compat helpers ─────────────────────────────────────────────

function s(obj: any, ...keys: string[]): any {
  for (const k of keys) {
    if (obj[k] !== undefined && obj[k] !== null) return obj[k]
  }
  return undefined
}

// ── Interfaces ────────────────────────────────────────────────────────────

export interface GovMeetingApply {
  id: number
  applyNo: string
  apply_no?: string
  enterpriseName: string
  enterprise_name?: string
  creditCode: string
  credit_code?: string
  contactName: string
  contact_name?: string
  contactPhone: string
  contact_phone?: string
  topicCode?: string
  topic_code?: string
  topicName?: string
  topic_name?: string
  meetingLevel?: string
  meeting_level?: string
  expectedLevelCode?: string
  expected_level_code?: string
  expectedLevelName?: string
  expected_level_name?: string
  finalLevelCode?: string
  final_level_code?: string
  finalLevelName?: string
  final_level_name?: string
  title?: string
  content?: string
  meeting_content?: string
  discussionItem?: string
  discussion_item?: string
  urgencyLevel?: string
  urgency_level?: string
  industryCode?: string
  industry_code?: string
  industryName?: string
  industry_name?: string
  registeredAddress?: string
  registered_address?: string
  description?: string
  commitmentChecked?: number
  commitment_checked?: number
  regionCode: string
  region_code?: string
  regionName: string
  region_name?: string
  serviceCenterId?: number
  service_center_id?: number
  serviceCenterName?: string
  service_center_name?: string
  status: string
  rejectReasonCode?: string
  reject_reason_code?: string
  rejectReasonName?: string
  reject_reason_name?: string
  rejectOpinion?: string
  reject_opinion?: string
  submittedAt?: string
  submitted_at?: string
  acceptedAt?: string
  accepted_at?: string
  arrangedAt?: string
  arranged_at?: string
  completedAt?: string
  completed_at?: string
  evaluatedAt?: string
  evaluated_at?: string
  finishedAt?: string
  finished_at?: string
  createdAt?: string
  created_at?: string
}

export interface GovMeetingParticipant {
  id?: number
  participantType: string
  participant_type?: string
  participantName: string
  participant_name?: string
  participantTitle?: string
  participant_title?: string
  participantDeptId?: string
  participant_dept_id?: string
  participantDeptName?: string
  participant_dept_name?: string
  contactPhone?: string
  contact_phone?: string
  roleName?: string
  role_name?: string
  sortNo?: number
  sort_no?: number
}

export interface GovMeetingArrangement {
  id: number
  applyId?: number
  apply_id?: number
  meetingDate?: string
  meeting_date?: string
  startTime?: string
  start_time?: string
  endTime?: string
  end_time?: string
  meetingPlace?: string
  meeting_place?: string
  meetingMethod?: string
  meeting_method?: string
  hostDeptName?: string
  host_dept_name?: string
  govContactName?: string
  gov_contact_name?: string
  govContactPhone?: string
  gov_contact_phone?: string
  notes?: string
  remark?: string
  confirmedFlag?: number
  confirmed_flag?: number
  participants: GovMeetingParticipant[]
}

export interface GovMeetingAudit {
  id: number
  actionType: string
  action_type?: string
  actionName: string
  action_name?: string
  beforeStatus?: string
  before_status?: string
  afterStatus?: string
  after_status?: string
  opinion?: string
  operatorName?: string
  operator_name?: string
  operatorDeptName?: string
  operator_dept_name?: string
  createdAt?: string
  created_at?: string
}

export interface GovMeetingRecord {
  id: number
  content: string
  conclusions?: string
  followUpItems?: string
  follow_up_items?: string
  recorderName?: string
  recorder_name?: string
  recordTime?: string
  record_time?: string
  createdAt?: string
  created_at?: string
}

export interface GovMeetingEvaluation {
  id: number
  satisfaction: string
  score: number
  resolvedFlag?: number
  resolved_flag?: number
  comment?: string
  createdAt?: string
  created_at?: string
}

export interface GovMeetingDetail extends GovMeetingApply {
  arrangement?: GovMeetingArrangement | null
  auditTrail?: GovMeetingAudit[]
  audit_trail?: GovMeetingAudit[]
  records?: GovMeetingRecord[]
  attachments?: any[]
  evaluation?: GovMeetingEvaluation | null
}

export interface PageResult<T> {
  records: T[]
  total: number
  pageNo: number
  pageSize: number
}

// ── Compat getters ─────────────────────────────────────────────────────────

export function applyNo(a: GovMeetingApply) { return s(a, 'applyNo', 'apply_no') || '' }
export function expectedLevelName(a: GovMeetingApply) { return s(a, 'expectedLevelName', 'expected_level_name') || s(a, 'meetingLevel', 'meeting_level') || '' }
export function finalLevelName(a: GovMeetingApply) { return s(a, 'finalLevelName', 'final_level_name') || '' }
export function applyTitle(a: GovMeetingApply) { return s(a, 'title') || s(a, 'topicName', 'topic_name') || '' }
export function applyContent(a: GovMeetingApply) { return s(a, 'content', 'meeting_content') || s(a, 'description') || '' }
export function applyDiscussion(a: GovMeetingApply) { return s(a, 'discussionItem', 'discussion_item') || '' }
export function urgencyLevel(a: GovMeetingApply) { return s(a, 'urgencyLevel', 'urgency_level') || '' }
export function submittedAt(a: GovMeetingApply) { return s(a, 'submittedAt', 'submitted_at') || '' }
export function acceptedAt(a: GovMeetingApply) { return s(a, 'acceptedAt', 'accepted_at') || '' }

export function arrMeetingDate(arr: GovMeetingArrangement) { return s(arr, 'meetingDate', 'meeting_date') || '' }
export function arrStartTime(arr: GovMeetingArrangement) { return s(arr, 'startTime', 'start_time') || '' }
export function arrEndTime(arr: GovMeetingArrangement) { return s(arr, 'endTime', 'end_time') || '' }
export function arrPlace(arr: GovMeetingArrangement) { return s(arr, 'meetingPlace', 'meeting_place') || '' }
export function arrMethod(arr: GovMeetingArrangement) { return s(arr, 'meetingMethod', 'meeting_method') || '' }
export function arrHostDept(arr: GovMeetingArrangement) { return s(arr, 'hostDeptName', 'host_dept_name') || '' }
export function arrNotes(arr: GovMeetingArrangement) { return s(arr, 'notes') || s(arr, 'remark') || '' }
export function arrParticipants(arr: GovMeetingArrangement): GovMeetingParticipant[] { return arr.participants || [] }

export function pType(p: GovMeetingParticipant) { return s(p, 'participantType', 'participant_type') || '' }
export function pName(p: GovMeetingParticipant) { return s(p, 'participantName', 'participant_name') || '' }
export function pTitle(p: GovMeetingParticipant) { return s(p, 'participantTitle', 'participant_title') || '' }
export function pDept(p: GovMeetingParticipant) { return s(p, 'participantDeptName', 'participant_dept_name') || '' }
export function pPhone(p: GovMeetingParticipant) { return s(p, 'contactPhone', 'contact_phone') || '' }
export function pRole(p: GovMeetingParticipant) { return s(p, 'roleName', 'role_name') || '' }

export function auditActionName(a: GovMeetingAudit) { return s(a, 'actionName', 'action_name') || '' }
export function auditOpinion(a: GovMeetingAudit) { return s(a, 'opinion') || '' }
export function auditOperator(a: GovMeetingAudit) { return s(a, 'operatorName', 'operator_name') || '' }
export function auditCreatedAt(a: GovMeetingAudit) { return s(a, 'createdAt', 'created_at') || '' }
export function detailAuditTrail(d: GovMeetingDetail): GovMeetingAudit[] { return d.auditTrail || d.audit_trail || [] }
export function detailRecords(d: GovMeetingDetail): GovMeetingRecord[] { return d.records || [] }

// ── API functions ─────────────────────────────────────────────────────────

/** 政企约见须知（后端暂无此接口，前端使用兜底文本） */
export async function getGovMeetingNotice(): Promise<string | null> {
  try {
    const res = await get<{ content?: string; html?: string }>('/api/enterprise/gov-meetings/notice')
    return res?.content || res?.html || null
  } catch {
    return null
  }
}

export function createGovMeeting(data: {
  contactName: string
  contactPhone: string
  topicCode?: string
  topicName?: string
  expectedLevelCode?: string
  expectedLevelName?: string
  title?: string
  content?: string
  discussionItem?: string
  urgencyLevel?: string
  industryCode?: string
  industryName?: string
  registeredAddress?: string
  regionCode: string
  regionName: string
  serviceCenterId?: number
  serviceCenterName?: string
  commitmentChecked: number
  attachmentIds?: number[]
}): Promise<GovMeetingApply> {
  return post<GovMeetingApply>('/api/enterprise/gov-meetings', data)
}

export function getMyGovMeetings(params: {
  status?: string
  pageNo?: number
  pageSize?: number
}): Promise<PageResult<GovMeetingApply>> {
  return get<PageResult<GovMeetingApply>>('/api/enterprise/gov-meetings', params as Record<string, unknown>)
}

export function getGovMeetingDetail(id: number): Promise<GovMeetingDetail> {
  return get<GovMeetingDetail>(`/api/enterprise/gov-meetings/${id}`)
}

export function supplementGovMeeting(id: number, data: {
  content?: string
  attachmentIds?: number[]
}): Promise<GovMeetingApply> {
  return post<GovMeetingApply>(`/api/enterprise/gov-meetings/${id}/supplement`, data)
}

/**
 * 企业评价政企约见
 * 后端实际路径：POST /api/enterprise/gov-meetings/{id}/evaluate（非 /evaluation）
 */
export function evaluateGovMeeting(id: number, data: {
  satisfaction: string
  score: number
  resolvedFlag?: number
  comment?: string
}): Promise<GovMeetingApply> {
  return post<GovMeetingApply>(`/api/enterprise/gov-meetings/${id}/evaluate`, data)
}
