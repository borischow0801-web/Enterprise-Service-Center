import { statusBannerBg, statusLabel } from './status'

/** @deprecated 请使用 utils/status.ts */
export function appealStatusText(code: string) {
  return statusLabel('appeal', code)
}

/** 详情顶栏背景色 */
export function appealStatusColor(code: string): string {
  return statusBannerBg('appeal', code)
}

/** 手机号脱敏：138****0000 */
export function maskMobile(mobile?: string | null): string {
  if (!mobile) return '--'
  if (mobile.length < 7) return mobile
  return `${mobile.slice(0, 3)}****${mobile.slice(-4)}`
}

/** 兼容 camelCase / snake_case 字段读取 */
export function getField<T = unknown>(
  obj: object | null | undefined,
  ...keys: string[]
): T | undefined {
  if (!obj) return undefined
  const record = obj as Record<string, unknown>
  for (const k of keys) {
    const v = record[k]
    if (v !== undefined && v !== null && v !== '') return v as T
  }
  return undefined
}

/** 规范化会议室 facilities：兼容数组、逗号/JSON 字符串等 */
export function normalizeFacilities(raw: unknown): string[] {
  if (raw == null || raw === '') return []
  if (Array.isArray(raw)) {
    const parts: string[] = []
    for (const item of raw) {
      if (typeof item === 'string') {
        normalizeFacilities(item).forEach(c => {
          if (c && !parts.includes(c)) parts.push(c)
        })
      }
    }
    return parts
  }
  if (typeof raw === 'string') {
    const s = raw.trim()
    if (!s) return []
    if (s.startsWith('[')) {
      try {
        const parsed = JSON.parse(s)
        if (Array.isArray(parsed)) return normalizeFacilities(parsed)
      } catch {
        /* 非 JSON，按分隔符拆分 */
      }
    }
    const parts: string[] = []
    s.split(/[,，、;；\n\r]+/).forEach(part => {
      const t = part.trim()
      if (t && !parts.includes(t)) parts.push(t)
    })
    return parts
  }
  return []
}

/** 解析使用物品：支持数组、逗号/顿号/分号/换行分隔字符串，去重去空 */
export function parseSupportItems(raw: string[] | string | null | undefined): string[] {
  if (!raw) return []
  const parts: string[] = []
  const add = (s: string) => {
    const t = s.trim()
    if (t && !parts.includes(t)) parts.push(t)
  }
  if (Array.isArray(raw)) {
    for (const item of raw) {
      if (typeof item === 'string') {
        item.split(/[,，、;；\n\r]+/).forEach(add)
      }
    }
    return parts
  }
  if (typeof raw === 'string' && raw) {
    raw.split(/[,，、;；\n\r]+/).forEach(add)
  }
  return parts
}

/** 合并选择项、已添加标签与输入框中的手动内容 */
export function buildSupportItems(
  selected: string[],
  customTags: string[],
  customInput?: string
): string[] {
  const merged: string[] = [...selected, ...customTags]
  if (customInput?.trim()) merged.push(customInput.trim())
  return parseSupportItems(merged)
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}
