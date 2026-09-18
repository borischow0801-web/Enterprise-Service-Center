import { getToken } from './token'

/**
 * 打开/下载需要鉴权的业务附件（诉求/预约/政企约见材料）。
 *
 * 这些附件的下载接口现在要求 Authorization 头（见后端 A1 附件权限整改），
 * 而 <img>/window.open 直接访问 URL 时浏览器不会带上自定义请求头，
 * 因此这里改为先用 fetch 手动带上 token 取回文件内容，再以 Blob URL 的方式
 * 在新标签页打开——对用户来说和原来的 window.open 行为基本一致。
 *
 * 会议室封面图/图册/材料模板不受影响，后端对这类"公开展示"附件本就保持匿名可访问，
 * 继续使用原来的 <img src>/window.open 方式即可，不需要调用这个函数。
 */
export async function fetchSecureAttachmentBlobUrl(url: string): Promise<string> {
  const token = getToken()
  const base = import.meta.env.VITE_API_BASE_URL ?? ''
  const fullUrl = url.startsWith('http') ? url : `${base}${url}`

  const resp = await fetch(fullUrl, {
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
  return URL.createObjectURL(blob)
}

export async function openSecureAttachment(url: string): Promise<void> {
  const objectUrl = await fetchSecureAttachmentBlobUrl(url)
  window.open(objectUrl, '_blank')
}
