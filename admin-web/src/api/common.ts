import { get } from './request'
import { getToken } from '@/utils/token'
import axios from 'axios'
import { ElMessage } from 'element-plus'

export interface DictItem {
  id: number
  dictType: string
  dictCode: string
  dictLabel: string
  dictValue?: string
  sortNo: number
  parentCode?: string | null
}

/**
 * 通用字典查询，无需登录。
 * GET /api/common/dictionaries/{dictType}
 * 返回 enabled=1 的字典项，按 sortNo 升序。
 */
export async function getDictionary(dictType: string): Promise<DictItem[]> {
  try {
    return await get<DictItem[]>(`/api/common/dictionaries/${dictType}`)
  } catch {
    return []
  }
}

/** 将字典列表转为 {code: label} 映射，方便直接查文本 */
export function dictToMap(items: DictItem[]): Record<string, string> {
  return Object.fromEntries(items.map(i => [i.dictCode, i.dictLabel]))
}

export interface AttachmentResult {
  id: number
  originalName: string
  fileExt: string
  fileSize: number
  storagePath: string
  downloadUrl: string
}

/**
 * 上传附件（支持企业端和管理端 token）
 * POST /api/common/attachments/upload
 */
export async function uploadAttachment(file: File): Promise<AttachmentResult> {
  const formData = new FormData()
  formData.append('file', file)
  const token = getToken()
  const resp = await axios.post('/api/common/attachments/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  const body = resp.data
  if (body.code !== 0) {
    ElMessage.error(body.message || '上传失败')
    throw new Error(body.message)
  }
  return body.data as AttachmentResult
}
