import axios from 'axios'
import { get } from './request'
import { getToken } from '@/utils/token'
import { apiBaseUrl } from '@/utils/api'

export interface DictItem {
  id: number
  dictType: string
  dictCode: string
  dictLabel: string
  dictValue?: string
  sortNo: number
}

export async function getDictionary(dictType: string): Promise<DictItem[]> {
  try {
    return await get<DictItem[]>(`/api/common/dictionaries/${dictType}`)
  } catch {
    return []
  }
}

export interface AttachmentResult {
  id: number
  originalName: string
  fileExt: string
  fileSize: number
  storagePath: string
  downloadUrl: string
}

export async function uploadAttachment(file: File): Promise<AttachmentResult> {
  const formData = new FormData()
  formData.append('file', file)
  const token = getToken()
  const base = apiBaseUrl()
  const uploadPath = '/api/common/attachments/upload'
  const resp = await axios.post(base ? `${base}${uploadPath}` : uploadPath, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })
  const body = resp.data
  if (body.code !== 0) throw new Error(body.message || '上传失败')
  return body.data as AttachmentResult
}
