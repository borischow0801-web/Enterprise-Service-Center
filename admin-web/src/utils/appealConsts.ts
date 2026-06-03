// 诉求状态映射
export const APPEAL_STATUS_MAP: Record<string, string> = {
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

export const APPEAL_STATUS_OPTIONS = Object.entries(APPEAL_STATUS_MAP).map(([value, label]) => ({ value, label }))

export function appealStatusText(code: string) {
  return APPEAL_STATUS_MAP[code] ?? code
}

export function appealTagType(code: string): 'success' | 'warning' | 'danger' | 'info' | '' {
  const success = ['REPLIED', 'PENDING_EVALUATION', 'EVALUATED', 'COMPLETED', 'DEPT_REPLIED']
  const warning = ['PENDING_ACCEPT', 'ACCEPTED', 'CENTER_HANDLING', 'DEPT_HANDLING', 'CENTER_REVIEWING']
  const danger = ['REJECTED', 'REVIEW_REJECTED']
  const info = ['NEED_SUPPLEMENT']
  if (success.includes(code)) return 'success'
  if (danger.includes(code)) return 'danger'
  if (info.includes(code)) return 'info'
  if (warning.includes(code)) return 'warning'
  return ''
}

// 诉求类型 (TODO: 从 /api/admin/dictionaries?dictType=APPEAL_TYPE 获取，暂用本地枚举)
export const APPEAL_TYPE_MAP: Record<string, string> = {
  POLICY_CONSULT: '政策咨询',
  POLICY_ADVICE: '政策诉求',
  BIZ_CONSULT: '业务咨询',
  COMPLAINT: '投诉举报',
  SUGGESTION: '意见建议',
  HELP: '帮办代办',
  OTHER: '其他',
}

export const APPEAL_TYPE_OPTIONS = Object.entries(APPEAL_TYPE_MAP).map(([value, label]) => ({ value, label }))

// 不予受理原因 (TODO: 从 APPEAL_REJECT_REASON 字典获取)
export const REJECT_REASON_OPTIONS = [
  { value: 'NOT_IN_SCOPE', label: '不在受理范围' },
  { value: 'LACK_MATERIAL', label: '材料不齐全' },
  { value: 'DUPLICATE', label: '重复诉求' },
  { value: 'INVALID', label: '内容无效' },
  { value: 'OTHER', label: '其他原因' },
]

// 紧急程度
export const URGENCY_MAP: Record<string, string> = {
  NORMAL: '普通',
  URGENT: '紧急',
  VERY_URGENT: '非常紧急',
}

export function urgencyText(code: string) {
  return URGENCY_MAP[code] ?? code
}

export function urgencyTagType(code: string): 'success' | 'warning' | 'danger' | 'info' | '' {
  if (code === 'VERY_URGENT') return 'danger'
  if (code === 'URGENT') return 'warning'
  return ''
}

// 操作记录类型
export const ACTION_TYPE_MAP: Record<string, string> = {
  SUBMIT: '企业提交',
  ACCEPT: '受理',
  RETURN_SUPPLEMENT: '退回补充',
  REJECT: '不予受理',
  CENTER_HANDLE: '企服中心办理',
  ASSIGN_DEPT: '分派部门',
  DEPT_REPLY: '部门反馈',
  REVIEW_PASS: '审核通过',
  REVIEW_REJECT: '审核退回',
  SUPPLEMENT: '企业补充',
  EVALUATE: '企业评价',
  FOLLOW_UP: '线下回访',
  WITHDRAW: '企业撤回',
}

// 回访方式
export const FOLLOWUP_METHOD_OPTIONS = [
  { value: 'PHONE', label: '电话回访' },
  { value: 'VISIT', label: '上门回访' },
  { value: 'ONLINE', label: '线上回访' },
  { value: 'OTHER', label: '其他方式' },
]

// 满意度
export const SATISFACTION_MAP: Record<string, string> = {
  SATISFIED: '满意',
  BASIC_SATISFIED: '基本满意',
  NORMAL: '一般',
  UNSATISFIED: '不满意',
}

export function formatSatisfaction(code?: string | null): string {
  if (!code) return '--'
  return SATISFACTION_MAP[code] ?? code
}

export function formatResolvedFlag(flag?: number | null): string {
  if (flag === 1) return '是'
  if (flag === 0) return '否'
  return '--'
}

// 分派状态
export const ASSIGNMENT_STATUS_MAP: Record<string, string> = {
  PENDING: '待办理',
  HANDLING: '办理中',
  REPLIED: '已反馈',
  CLOSED: '已关闭',
}

// 回访状态
export const FOLLOWUP_STATUS_MAP: Record<string, string> = {
  PENDING: '待回访',
  COMPLETED: '已回访',
  FAILED: '回访失败',
}

// 按当前状态决定可用操作
export type AppealAction = 'accept' | 'returnSupplement' | 'reject' | 'centerHandle' | 'assign' | 'deptReply' | 'reviewReply' | 'followup'

export function availableActions(status: string): AppealAction[] {
  const map: Record<string, AppealAction[]> = {
    PENDING_ACCEPT: ['accept', 'returnSupplement', 'reject'],
    ACCEPTED: ['centerHandle', 'assign'],
    NEED_SUPPLEMENT: [],
    REJECTED: [],
    CENTER_HANDLING: ['centerHandle'],
    DEPT_HANDLING: ['deptReply'],
    DEPT_REPLIED: ['deptReply'],
    CENTER_REVIEWING: ['reviewReply'],
    REVIEW_REJECTED: ['assign', 'deptReply'],
    EVALUATED: ['followup'],
    PENDING_EVALUATION: ['followup'],
  }
  return map[status] ?? []
}
