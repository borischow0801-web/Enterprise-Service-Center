import { get, post, put, patch } from './request'
import type { PageResult } from './appeal'

export interface AdminUserItem {
  id: number
  bspUserId?: string | null
  username: string
  realName: string
  mobile?: string | null
  status: 'ACTIVE' | 'DISABLED'
  roleCodes: string[]
  dataScope: string
  regionCode?: string | null
  regionName?: string | null
  departmentId?: string | null
  departmentName?: string | null
  lastLoginAt?: string | null
  createdAt?: string
  updatedAt?: string
}

export interface AdminUserQuery {
  username?: string
  status?: string
  roleCode?: string
  pageNo?: number
  pageSize?: number
}

export interface AdminUserSaveInput {
  username?: string
  realName?: string
  mobile?: string | null
  roleCodes: string[]
  dataScope: string
  regionCode?: string | null
  regionName?: string | null
  departmentId?: string | null
  departmentName?: string | null
  status?: 'ACTIVE' | 'DISABLED'
}

export function listAdminUsers(params: AdminUserQuery) {
  return get<PageResult<AdminUserItem>>('/api/admin/admin-users/page', params as Record<string, unknown>)
}

export function getAdminUser(id: number) {
  return get<AdminUserItem>(`/api/admin/admin-users/${id}`)
}

export function createAdminUser(data: AdminUserSaveInput) {
  return post<AdminUserItem>('/api/admin/admin-users', data)
}

export function updateAdminUser(id: number, data: Partial<AdminUserSaveInput>) {
  return put<AdminUserItem>(`/api/admin/admin-users/${id}`, data)
}

export function toggleAdminUserStatus(id: number, status: 'ACTIVE' | 'DISABLED') {
  return patch<AdminUserItem>(`/api/admin/admin-users/${id}/status`, { status })
}
