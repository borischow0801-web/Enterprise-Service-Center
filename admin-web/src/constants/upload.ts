/** 与后端 MAX_UPLOAD_SIZE 默认 10MB 一致 */
export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024
export const MAX_UPLOAD_TIP = '支持图片、PDF 等常见文件，单个文件大小不超过 10MB'

export function validateFileSize(file: File): string | null {
  if (file.size > MAX_UPLOAD_BYTES) {
    return '单个文件不能超过 10MB'
  }
  return null
}
