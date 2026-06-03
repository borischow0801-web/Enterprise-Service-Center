// ── 企业诉求状态 ──────────────────────────────────────────────────────────────
const APPEAL_STATUS_MAP: Record<string, string> = {
  PENDING_ACCEPT: '待受理',
  NEED_SUPPLEMENT: '退回补充',
  REJECTED: '不予受理',
  ACCEPTED: '已受理',
  CENTER_HANDLING: '企服中心办理中',
  DEPT_HANDLING: '部门办理中',
  DEPT_REPLIED: '部门已反馈',
  CENTER_REVIEWING: '企服中心审核',
  REVIEW_REJECTED: '审核退回',
  REPLIED: '已回复',
  PENDING_EVALUATION: '待评价',
  EVALUATED: '已评价',
  COMPLETED: '已办结',
}

// ── 会议室预约状态 ────────────────────────────────────────────────────────────
const BOOKING_STATUS_MAP: Record<string, string> = {
  PENDING_AUDIT: '待审核',
  NEED_SUPPLEMENT: '退回补充材料',
  REJECTED: '审核驳回',
  APPROVED: '审核通过',
  WAIT_USE: '待使用',
  CANCELED: '已取消',
  COMPLETED: '已完成',
  NO_SHOW: '爽约',
}

// ── 政企约见状态 ──────────────────────────────────────────────────────────────
const GOV_MEETING_STATUS_MAP: Record<string, string> = {
  PENDING_AUDIT: '待审核',
  NEED_SUPPLEMENT: '退回补正',
  REJECTED: '不予受理',
  ACCEPTED: '受理通过',
  PENDING_ARRANGE: '待安排',
  ARRANGED: '已安排',
  WAIT_MEETING: '待约见',
  MEETING_COMPLETED: '约见完成',
  PENDING_EVALUATION: '待评价',
  EVALUATED: '已评价',
  COMPLETED: '已办结',
}

// ── 会议室状态 ────────────────────────────────────────────────────────────────
const ROOM_STATUS_MAP: Record<string, string> = {
  ENABLED: '启用',
  DISABLED: '停用',
}

export type StatusType = 'appeal' | 'booking' | 'govMeeting' | 'room'

const STATUS_MAPS: Record<StatusType, Record<string, string>> = {
  appeal: APPEAL_STATUS_MAP,
  booking: BOOKING_STATUS_MAP,
  govMeeting: GOV_MEETING_STATUS_MAP,
  room: ROOM_STATUS_MAP,
}

export function statusText(type: StatusType, code: string): string {
  return STATUS_MAPS[type]?.[code] ?? code
}

// ── Element Plus Tag 类型 ─────────────────────────────────────────────────────
export function statusTagType(
  type: StatusType,
  code: string,
): 'success' | 'warning' | 'danger' | 'info' | '' {
  const successCodes = ['COMPLETED', 'EVALUATED', 'APPROVED', 'ACCEPTED', 'ENABLED', 'WAIT_USE', 'MEETING_COMPLETED']
  const warningCodes = ['PENDING_ACCEPT', 'PENDING_AUDIT', 'NEED_SUPPLEMENT', 'CENTER_HANDLING', 'DEPT_HANDLING', 'CENTER_REVIEWING', 'PENDING_ARRANGE', 'ARRANGED', 'WAIT_MEETING', 'PENDING_EVALUATION', 'DEPT_REPLIED']
  const dangerCodes = ['REJECTED', 'REVIEW_REJECTED', 'NO_SHOW', 'DISABLED']
  const infoCodes = ['CANCELED', 'REPLIED', 'REVIEW_REJECTED']

  if (successCodes.includes(code)) return 'success'
  if (dangerCodes.includes(code)) return 'danger'
  if (infoCodes.includes(code)) return 'info'
  if (warningCodes.includes(code)) return 'warning'
  return ''
}

// ── 日期格式化 ────────────────────────────────────────────────────────────────
export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function formatDateOnly(dateStr: string | null | undefined): string {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}
