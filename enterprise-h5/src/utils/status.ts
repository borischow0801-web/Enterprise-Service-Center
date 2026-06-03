/**
 * 企业端统一状态展示（诉求 / 会议室预约 / 政企约见 / 满意度）
 */

export type StatusModule = 'appeal' | 'booking' | 'govMeeting' | 'satisfaction'
export type StatusTagType = 'primary' | 'success' | 'warning' | 'danger' | 'default'

export interface StatusMeta {
  label: string
  type: StatusTagType
  color: string
  background: string
}

const APPEAL: Record<string, StatusMeta> = {
  PENDING_ACCEPT: { label: '待受理', type: 'warning', color: '#b45309', background: '#fef3c7' },
  NEED_SUPPLEMENT: { label: '退回补充', type: 'warning', color: '#b45309', background: '#fef3c7' },
  REJECTED: { label: '不予受理', type: 'danger', color: '#b91c1c', background: '#fee2e2' },
  ACCEPTED: { label: '已受理', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  CENTER_HANDLING: { label: '办理中', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  DEPT_HANDLING: { label: '部门办理中', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  DEPT_REPLIED: { label: '部门已反馈', type: 'success', color: '#15803d', background: '#dcfce7' },
  CENTER_REVIEWING: { label: '审核中', type: 'warning', color: '#b45309', background: '#fef3c7' },
  REVIEW_REJECTED: { label: '审核退回', type: 'danger', color: '#b91c1c', background: '#fee2e2' },
  REPLIED: { label: '已回复', type: 'success', color: '#15803d', background: '#dcfce7' },
  PENDING_EVALUATION: { label: '待评价', type: 'warning', color: '#b45309', background: '#fef3c7' },
  EVALUATED: { label: '已评价', type: 'success', color: '#15803d', background: '#dcfce7' },
  COMPLETED: { label: '已办结', type: 'success', color: '#15803d', background: '#dcfce7' },
}

const BOOKING: Record<string, StatusMeta> = {
  PENDING_AUDIT: { label: '待审核', type: 'warning', color: '#b45309', background: '#fef3c7' },
  NEED_SUPPLEMENT: { label: '退回补充', type: 'warning', color: '#b45309', background: '#fef3c7' },
  REJECTED: { label: '已驳回', type: 'danger', color: '#b91c1c', background: '#fee2e2' },
  APPROVED: { label: '审核通过', type: 'success', color: '#15803d', background: '#dcfce7' },
  WAIT_USE: { label: '待使用', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  IN_USE: { label: '使用中', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  COMPLETED: { label: '已完成', type: 'success', color: '#15803d', background: '#dcfce7' },
  CANCELLED: { label: '已取消', type: 'default', color: '#6b7280', background: '#f3f4f6' },
  CANCELED: { label: '已取消', type: 'default', color: '#6b7280', background: '#f3f4f6' },
  NO_SHOW: { label: '爽约', type: 'danger', color: '#b91c1c', background: '#fee2e2' },
}

const GOV_MEETING: Record<string, StatusMeta> = {
  PENDING_AUDIT: { label: '待审核', type: 'warning', color: '#b45309', background: '#fef3c7' },
  NEED_SUPPLEMENT: { label: '退回补正', type: 'warning', color: '#b45309', background: '#fef3c7' },
  REJECTED: { label: '不予受理', type: 'danger', color: '#b91c1c', background: '#fee2e2' },
  ACCEPTED: { label: '受理通过', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  PENDING_ARRANGE: { label: '待安排', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  ARRANGED: { label: '已安排', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  WAIT_MEETING: { label: '待约见', type: 'success', color: '#15803d', background: '#dcfce7' },
  MEETING_COMPLETED: { label: '约见完成', type: 'success', color: '#15803d', background: '#dcfce7' },
  PENDING_EVALUATION: { label: '待评价', type: 'warning', color: '#b45309', background: '#fef3c7' },
  EVALUATED: { label: '已评价', type: 'success', color: '#15803d', background: '#dcfce7' },
  COMPLETED: { label: '已办结', type: 'success', color: '#15803d', background: '#dcfce7' },
}

const SATISFACTION: Record<string, StatusMeta> = {
  SATISFIED: { label: '满意', type: 'success', color: '#15803d', background: '#dcfce7' },
  BASIC_SATISFIED: { label: '基本满意', type: 'primary', color: '#1d4ed8', background: '#dbeafe' },
  NORMAL: { label: '一般', type: 'default', color: '#6b7280', background: '#f3f4f6' },
  UNSATISFIED: { label: '不满意', type: 'danger', color: '#b91c1c', background: '#fee2e2' },
}

const MAPS: Record<StatusModule, Record<string, StatusMeta>> = {
  appeal: APPEAL,
  booking: BOOKING,
  govMeeting: GOV_MEETING,
  satisfaction: SATISFACTION,
}

const DEFAULT_META: StatusMeta = {
  label: '未知',
  type: 'default',
  color: '#6b7280',
  background: '#f3f4f6',
}

export function getStatusMeta(module: StatusModule, code?: string | null): StatusMeta {
  if (!code) return { ...DEFAULT_META, label: '--' }
  const meta = MAPS[module][code]
  if (meta) return meta
  return { ...DEFAULT_META, label: code }
}

export function statusLabel(module: StatusModule, code?: string | null): string {
  return getStatusMeta(module, code).label
}

export function statusColor(module: StatusModule, code?: string | null): string {
  return getStatusMeta(module, code).color
}

export function statusBannerBg(module: StatusModule, code?: string | null): string {
  return getStatusMeta(module, code).color
}

export function statusVantType(module: StatusModule, code?: string | null): StatusTagType {
  return getStatusMeta(module, code).type
}

/** 横幅背景色（比标签色更深，用于详情顶栏） */
export function statusBannerGradient(module: StatusModule, code?: string | null): string {
  const c = getStatusMeta(module, code).color
  return `linear-gradient(135deg, ${c} 0%, var(--esc-primary-dark) 100%)`
}

const BOOKING_HINT: Record<string, string> = {
  PENDING_AUDIT: '您的预约正在审核中，请耐心等待',
  NEED_SUPPLEMENT: '管理员要求补充材料，请尽快处理',
  REJECTED: '预约申请未通过审核',
  APPROVED: '预约已审核通过，请准时到场',
  WAIT_USE: '预约已确认，请准时到场使用',
  CANCELED: '预约已取消',
  CANCELLED: '预约已取消',
  COMPLETED: '会议室使用已完成，感谢您的使用',
  NO_SHOW: '您未按预约时间使用，已记录爽约',
}

export function bookingStatusHint(code?: string | null): string {
  if (!code) return ''
  return BOOKING_HINT[code] || ''
}
