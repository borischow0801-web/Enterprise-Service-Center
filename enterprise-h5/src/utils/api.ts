/** 后端 API 根地址（.env.development 中 VITE_API_BASE_URL） */
export function apiBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? ''
  return base.replace(/\/$/, '')
}

/** 将相对路径转为可访问的完整 URL（封面图、附件下载等） */
export function apiAssetUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const base = apiBaseUrl()
  if (!base) return path
  return `${base}${path.startsWith('/') ? path : `/${path}`}`
}
