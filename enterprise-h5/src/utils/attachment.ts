import { getToken } from './token'
import { apiAssetUrl } from './api'

/**
 * 打开需要鉴权的业务附件（诉求/预约/政企约见材料）。
 *
 * 这些附件的下载接口现在要求 Authorization 头（见后端 A1 附件权限整改），
 * window.open 直接访问 URL 时浏览器不会带上自定义请求头，因此改为先用 fetch
 * 手动带上 token 取回文件内容，再以 Blob URL 的方式在新标签页打开。
 *
 * 会议室封面图/材料模板不受影响，后端对这类"公开展示"附件保持匿名可访问，
 * 继续用 apiAssetUrl() + window.open/<img> 即可，不需要调用这个函数。
 */
export async function openSecureAttachment(path: string): Promise<void> {
  const token = getToken()
  const resp = await fetch(apiAssetUrl(path), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (!resp.ok) {
    let message = '附件下载失败'
    try {
      const body = await resp.json()
      message = body?.message || message
    } catch {
      // 响应体不是 JSON，忽略
    }
    throw new Error(message)
  }

  const blob = await resp.blob()
  const objectUrl = URL.createObjectURL(blob)
  window.open(objectUrl, '_blank')
}
