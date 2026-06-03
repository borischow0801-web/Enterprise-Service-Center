import { get } from './request'
import type { PageResult } from './appeal'

export interface OperationLogItem {
  id: number
  operatorType: string
  operatorId: string
  operatorName: string
  businessType?: string
  businessId?: number
  operationType: string
  operationContent?: string
  beforeStatus?: string
  afterStatus?: string
  ipAddress?: string
  createdAt?: string
}

export interface OpLogQuery {
  operatorType?: string
  operatorName?: string
  businessType?: string
  operationType?: string
  startDate?: string
  endDate?: string
  pageNo?: number
  pageSize?: number
}

export function listOperationLogs(params: OpLogQuery) {
  return get<PageResult<OperationLogItem>>('/api/admin/operation-logs', params as Record<string, unknown>)
}
