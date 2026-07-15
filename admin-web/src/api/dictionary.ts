import { get, post, put, patch } from './request'
import type { PageResult } from './appeal'

export interface DictionaryItem {
  id: number
  dictType: string
  dictCode: string
  dictLabel: string
  dictValue?: string
  sortNo: number
  enabled: number
  parentCode?: string | null
  extraJson?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface DictQuery {
  dictType?: string
  dictCode?: string
  dictLabel?: string
  enabled?: number
  pageNo?: number
  pageSize?: number
}

export function listDictionaries(params: DictQuery) {
  return get<PageResult<DictionaryItem>>('/api/admin/dictionaries', params as Record<string, unknown>)
}

export function createDictionary(data: Partial<DictionaryItem>) {
  return post<DictionaryItem>('/api/admin/dictionaries', data)
}

export function updateDictionary(id: number, data: Partial<DictionaryItem>) {
  return put<DictionaryItem>(`/api/admin/dictionaries/${id}`, data)
}

export function toggleDictionaryStatus(id: number, enabled: number) {
  return patch<DictionaryItem>(`/api/admin/dictionaries/${id}/status`, { enabled })
}


export interface ServiceCenterItem {
  id: number
  centerName: string
  regionCode: string
  regionName: string
  address?: string | null
  contactName?: string | null
  contactPhone?: string | null
  status: 'ENABLED' | 'DISABLED'
  createdAt?: string
  updatedAt?: string
}

export interface ServiceCenterQuery {
  regionCode?: string
  centerName?: string
  status?: string
  pageNo?: number
  pageSize?: number
}

export function listServiceCenters(params: ServiceCenterQuery) {
  return get<PageResult<ServiceCenterItem>>('/api/admin/service-centers/page', params as Record<string, unknown>)
}

export function createServiceCenter(data: Partial<ServiceCenterItem>) {
  return post<ServiceCenterItem>('/api/admin/service-centers', data)
}

export function updateServiceCenter(id: number, data: Partial<ServiceCenterItem>) {
  return put<ServiceCenterItem>(`/api/admin/service-centers/${id}`, data)
}

export function toggleServiceCenterStatus(id: number, status: 'ENABLED' | 'DISABLED') {
  return patch<ServiceCenterItem>(`/api/admin/service-centers/${id}/status`, { status })
}
