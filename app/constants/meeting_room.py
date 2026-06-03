class BookingStatus:
    PENDING_AUDIT = "PENDING_AUDIT"       # 待审核
    NEED_SUPPLEMENT = "NEED_SUPPLEMENT"   # 退回补充材料
    REJECTED = "REJECTED"                 # 审核驳回
    APPROVED = "APPROVED"                 # 审核通过
    WAIT_USE = "WAIT_USE"                 # 待使用
    CANCELED = "CANCELED"                 # 已取消
    COMPLETED = "COMPLETED"               # 已完成
    NO_SHOW = "NO_SHOW"                   # 爽约


class RoomStatus:
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class SpecialDateType:
    HOLIDAY = "HOLIDAY"
    TEMP_CLOSE = "TEMP_CLOSE"
    TEMP_OPEN = "TEMP_OPEN"


class AuditAction:
    SUBMIT = "SUBMIT"
    SUPPLEMENT = "SUPPLEMENT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN_SUPPLEMENT = "RETURN_SUPPLEMENT"
    CANCEL = "CANCEL"
    COMPLETE = "COMPLETE"
    NO_SHOW = "NO_SHOW"
    OCCUPY = "OCCUPY"


AUDIT_ACTION_NAMES = {
    AuditAction.SUBMIT: "企业提交预约",
    AuditAction.SUPPLEMENT: "企业补充材料",
    AuditAction.APPROVE: "审核通过",
    AuditAction.REJECT: "审核驳回",
    AuditAction.RETURN_SUPPLEMENT: "退回补充材料",
    AuditAction.CANCEL: "取消预约",
    AuditAction.COMPLETE: "确认使用完成",
    AuditAction.NO_SHOW: "标记爽约",
    AuditAction.OCCUPY: "手工占用",
}

ALLOWED_STATUS_FOR_ACTION = {
    AuditAction.APPROVE: [BookingStatus.PENDING_AUDIT, BookingStatus.NEED_SUPPLEMENT],
    AuditAction.REJECT: [BookingStatus.PENDING_AUDIT, BookingStatus.NEED_SUPPLEMENT],
    AuditAction.RETURN_SUPPLEMENT: [BookingStatus.PENDING_AUDIT],
    AuditAction.SUPPLEMENT: [BookingStatus.NEED_SUPPLEMENT],
    AuditAction.CANCEL: [BookingStatus.PENDING_AUDIT, BookingStatus.NEED_SUPPLEMENT, BookingStatus.APPROVED, BookingStatus.WAIT_USE],
    AuditAction.COMPLETE: [BookingStatus.APPROVED, BookingStatus.WAIT_USE],
    AuditAction.NO_SHOW: [BookingStatus.APPROVED, BookingStatus.WAIT_USE],
}

# Maximum爽约次数 before booking is disabled
NO_SHOW_DISABLE_THRESHOLD = 2
# Minimum advance booking days
MIN_ADVANCE_DAYS = 2
# Minimum booking duration in minutes
MIN_DURATION_MINUTES = 30
# Maximum booking duration in hours
MAX_DURATION_HOURS = 4
# Minimum hours before cancel (for APPROVED/WAIT_USE)
MIN_CANCEL_HOURS = 12
