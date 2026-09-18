import { get, post } from './request'

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

export interface AppealItem {
  id: number
  appealNo: string
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
  replyDeadline?: string
  submittedAt?: string
  acceptedAt?: string
  repliedAt?: string
  evaluatedAt?: string
}

export interface AppealDetail extends AppealItem {
  attachments: { id: number; originalName: string; fileExt: string; fileSize: number }[]
  records: AppealRecord[]
  evaluation: {
    id: number
    satisfaction: string
    score: number
    resolvedFlag: number
    comment: string | null
    evaluateTime: string
  } | null
}

export interface PageResult<T> {
  records: T[]
  total: number
  pageNo: number
  pageSize: number
}

export function createAppeal(data: {
  title: string
  content: string
  contactName: string
  contactPhone: string
  industryCode?: string
  industryName?: string
  regionCode: string
  regionName: string
  urgencyLevel?: string
  attachmentIds?: number[]
}): Promise<AppealItem> {
  return post<AppealItem>('/api/enterprise/appeals', data)
}

export function getMyAppeals(params: {
  status?: string
  pageNo?: number
  pageSize?: number
}): Promise<PageResult<AppealItem>> {
  return get<PageResult<AppealItem>>('/api/enterprise/appeals', params as Record<string, unknown>)
}

export function getAppealDetail(id: number): Promise<AppealDetail> {
  return get<AppealDetail>(`/api/enterprise/appeals/${id}`)
}

/**
 * 企业评价诉求
 * 后端实际路径：POST /api/enterprise/appeals/{id}/evaluation（非 /evaluate）
 */
export function evaluateAppeal(id: number, data: {
  satisfaction: string
  score: number
  resolvedFlag: number
  comment?: string
}): Promise<unknown> {
  return post(`/api/enterprise/appeals/${id}/evaluation`, data)
}

/**
 * 企业补充材料（诉求处于"退回补充"状态时使用）。
 * 后端：POST /api/enterprise/appeals/{id}/supplement
 */
export function supplementAppeal(id: number, data: {
  content: string
  attachmentIds?: number[]
}): Promise<AppealItem> {
  return post<AppealItem>(`/api/enterprise/appeals/${id}/supplement`, data)
}
