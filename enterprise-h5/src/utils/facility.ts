import { getDictionary } from '@/api/common'

let facilityLabelCache: Record<string, string> | null = null

/** 加载设施字典（仅用于 code → 中文展示，不作为预约选项来源） */
export async function loadFacilityLabelMap(): Promise<Record<string, string>> {
  if (facilityLabelCache) return facilityLabelCache
  try {
    const items = await getDictionary('MEETING_ROOM_FACILITY')
    facilityLabelCache = Object.fromEntries(
      items.map(t => [t.dictCode, t.dictLabel]),
    )
  } catch {
    facilityLabelCache = {}
  }
  return facilityLabelCache
}

export function facilityDisplayLabel(code: string, map: Record<string, string>): string {
  return map[code] || code
}
