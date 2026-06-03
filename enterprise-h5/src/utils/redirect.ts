/** 登录后默认落地页（无 redirect 时） */
export const DEFAULT_AFTER_LOGIN = '/home'

/**
 * 解析登录后跳转路径（decodeURIComponent + 防开放重定向）
 * 正式环境省级统一身份认证回调后同样使用此逻辑跳回菜单页。
 */
export function resolveRedirectPath(raw: string | null | undefined): string {
  if (!raw || typeof raw !== 'string') return DEFAULT_AFTER_LOGIN
  let path: string
  try {
    path = decodeURIComponent(raw.trim())
  } catch {
    return DEFAULT_AFTER_LOGIN
  }
  if (!path.startsWith('/') || path.startsWith('//')) return DEFAULT_AFTER_LOGIN
  if (path.startsWith('/login')) return DEFAULT_AFTER_LOGIN
  return path
}

/** 未登录时构造登录页地址，保留原始目标 fullPath（含 query） */
export function buildLoginRedirect(targetFullPath: string): string {
  return `/login?redirect=${encodeURIComponent(targetFullPath)}`
}
