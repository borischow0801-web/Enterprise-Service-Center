import { get, post } from './request'

export interface AdminLoginParams {
  platformUserId: string
  username: string
  realName: string
  departmentId: string
  departmentName: string
  regionCode: string
  regionName: string
  roleCodes: string[]
  dataScope: string
}

export interface TokenResult {
  accessToken: string
  tokenType: string
  expiresIn: number
}

export interface AdminUser {
  id: number
  platformUserId: string
  username: string
  realName: string
  mobile?: string
  departmentId: string
  departmentName: string
  regionCode: string
  regionName: string
  roleCodes: string[]
  dataScope: string
  lastLoginTime?: string
}

export function adminMockLogin(params: AdminLoginParams): Promise<TokenResult> {
  return post<TokenResult>('/api/auth/admin/mock-login', params)
}

export function getAdminMe(): Promise<AdminUser> {
  return get<AdminUser>('/api/admin/me')
}
