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
