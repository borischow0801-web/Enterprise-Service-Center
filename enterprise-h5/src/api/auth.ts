import { get, post } from './request'

export interface EnterpriseMockLoginParams {
  enterpriseName: string
  creditCode: string
  legalPersonName: string
  legalPersonIdNo: string
  legalPersonMobile: string
}

export interface EnterpriseUser {
  id?: number
  enterpriseName: string
  creditCode: string
  legalPersonName?: string
  legalPersonMobile?: string
  regionCode?: string
  regionName?: string
}

export type LoginResponseData = Record<string, unknown>

/** 从登录 data 中解析 token（兼容多种字段名） */
export function resolveAuthToken(data: LoginResponseData): string {
  const t =
    data.accessToken ??
    data.token ??
    data.access_token
  return typeof t === 'string' ? t : ''
}

/** 从登录 data 中解析企业信息（兼容 enterprise / user / 平铺字段） */
export function resolveEnterpriseUser(data: LoginResponseData): EnterpriseUser | null {
  const nested = data.enterprise ?? data.user
  if (nested && typeof nested === 'object') {
    return nested as EnterpriseUser
  }
  if (typeof data.enterpriseName === 'string' && typeof data.creditCode === 'string') {
    return data as unknown as EnterpriseUser
  }
  return null
}

/**
 * 正式环境：省级统一身份认证回调占位（未实现）。
 *
 * 微信公众号菜单直链 + 省认证流程应为：
 * 1. 用户从公众号菜单访问 /appeals、/meeting-rooms、/gov-meetings/notice 等；
 * 2. 未登录时路由守卫记录 redirect（见 router/index.ts、utils/redirect.ts）并跳转省认证；
 * 3. 认证回调到 /auth/callback（或约定页），调用后端 /api/auth/enterprise/callback 换取 token；
 * 4. 前端保存 enterprise_token / enterprise_user；
 * 5. 使用 resolveRedirectPath(redirect) 跳回原始菜单页，不要强制 /home。
 */
export async function handleProvincialAuthCallback(_params: { authCode: string }): Promise<never> {
  throw new Error('省级统一身份认证尚未对接，请使用开发调试登录页')
}

export function enterpriseMockLogin(params: EnterpriseMockLoginParams): Promise<LoginResponseData> {
  return post<LoginResponseData>('/api/auth/enterprise/mock-login', params)
}

export function getEnterpriseMe(): Promise<EnterpriseUser> {
  return get<EnterpriseUser>('/api/enterprise/me')
}
