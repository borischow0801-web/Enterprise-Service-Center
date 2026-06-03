import { get, post } from './request'

export interface AppealListParams {
  enterpriseName?: string
  creditCode?: string
  status?: string
  appealTypeCode?: string
  regionCode?: string
  responsibleDeptId?: string
  startDate?: string
  endDate?: string
  pageNo?: number
  pageSize?: number
}

export interface AppealItem {
  id: number
  appealNo: string
  enterpriseId: number
  enterpriseName: string
  creditCode: string
  title: string
  content: string
  contactName: string
  contactPhone: string
  industryCode?: string
  industryName?: string
  regionCode: string
  regionName: string
  appealTypeCode?: string
  appealTypeName?: string
  urgencyLevel?: string
  status: string
  handleMode?: string
  responsibleDeptId?: string
  responsibleDeptName?: string
  replyDeadline?: string
  submittedAt?: string
  acceptedAt?: string
  repliedAt?: string
  completedAt?: string
  evaluatedAt?: string
  createdAt?: string
  updatedAt?: string
}

export interface AppealRecord {
  id: number
  actionType: string
  actionName: string
  beforeStatus: string | null
  afterStatus: string
  opinion: string | null
  operatorType: string
  operatorName: string
  operatorDeptName: string | null
  createdAt: string
}

export interface AppealAssignment {
  id: number
  assignedDeptId: string
  assignedDeptName: string
  assignOpinion: string | null
  assignedAt: string
  deadline: string | null
  status: string
  replyContent: string | null
  repliedAt: string | null
}

export interface AppealEvaluation {
  id: number
  satisfaction: string
  score: number
  resolvedFlag: number
  comment: string | null
  evaluateTime: string
}

export interface AppealFollowup {
  id: number
  followupStatus: string
  followupMethod: string | null
  followupContent: string | null
  followupResult: string | null
  followupUserName: string | null
  followupTime: string | null
}

export interface AppealAttachment {
  id: number
  originalName: string
  fileExt: string
  fileSize: number
  storagePath: string
}

export interface AppealDetail extends AppealItem {
  attachments: AppealAttachment[]
  records: AppealRecord[]
  assignments: AppealAssignment[]
  evaluation: AppealEvaluation | null
  followups: AppealFollowup[]
}

export interface PageResult<T> {
  records: T[]
  total: number
  pageNo: number
  pageSize: number
}

export function getAppealList(params: AppealListParams): Promise<PageResult<AppealItem>> {
  return get<PageResult<AppealItem>>('/api/admin/appeals', params as Record<string, unknown>)
}

export function getAppealDetail(id: number): Promise<AppealDetail> {
  return get<AppealDetail>(`/api/admin/appeals/${id}`)
}

export function acceptAppeal(id: number, body: {
  appealTypeCode?: string
  appealTypeName?: string
  replyDeadline?: string
  opinion?: string
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/accept`, body)
}

export function returnSupplementAppeal(id: number, body: { opinion: string }): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/return-supplement`, body)
}

export function rejectAppeal(id: number, body: {
  reasonCode?: string
  reasonName?: string
  opinion?: string
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/reject`, body)
}

export function centerHandleAppeal(id: number, body: {
  replyContent: string
  attachmentIds?: number[]
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/center-handle`, body)
}

export function assignAppeal(id: number, body: {
  assignedDeptId: string
  assignedDeptName: string
  deadline?: string
  assignOpinion?: string
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/assign`, body)
}

export function departmentReplyAppeal(id: number, body: {
  replyContent: string
  attachmentIds?: number[]
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/department-reply`, body)
}

export function reviewReplyAppeal(id: number, body: {
  pass: boolean
  opinion?: string
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/admin/appeals/${id}/review-reply`, body)
}

export function addAppealFollowup(id: number, body: {
  responsibleDeptId?: string
  responsibleDeptName?: string
  followupMethod?: string
  followupContent?: string
  followupResult?: string
}): Promise<unknown> {
  return post(`/api/admin/appeals/${id}/followup`, body)
}
