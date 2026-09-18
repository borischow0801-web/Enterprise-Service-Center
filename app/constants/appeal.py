class AppealStatus:
    PENDING_ACCEPT = "PENDING_ACCEPT"       # 待受理
    NEED_SUPPLEMENT = "NEED_SUPPLEMENT"     # 退回补充
    REJECTED = "REJECTED"                   # 不予受理
    ACCEPTED = "ACCEPTED"                   # 已受理
    CENTER_HANDLING = "CENTER_HANDLING"     # 企服中心办理中
    DEPT_HANDLING = "DEPT_HANDLING"         # 部门办理中
    DEPT_REPLIED = "DEPT_REPLIED"           # 部门已反馈
    CENTER_REVIEWING = "CENTER_REVIEWING"   # 企服中心审核
    REVIEW_REJECTED = "REVIEW_REJECTED"     # 审核退回
    REPLIED = "REPLIED"                     # 已回复
    PENDING_EVALUATION = "PENDING_EVALUATION"  # 待评价
    EVALUATED = "EVALUATED"                 # 已评价
    COMPLETED = "COMPLETED"                 # 已办结


class AppealAction:
    SUBMIT = "SUBMIT"
    MODIFY = "MODIFY"
    SUPPLEMENT = "SUPPLEMENT"
    ACCEPT = "ACCEPT"
    RETURN_SUPPLEMENT = "RETURN_SUPPLEMENT"
    REJECT = "REJECT"
    ASSIGN_DEPT = "ASSIGN_DEPT"
    CENTER_HANDLE = "CENTER_HANDLE"
    DEPT_REPLY = "DEPT_REPLY"
    REVIEW_PASS = "REVIEW_PASS"
    REVIEW_REJECT = "REVIEW_REJECT"
    REPLY_ENTERPRISE = "REPLY_ENTERPRISE"
    EVALUATE = "EVALUATE"
    FOLLOW_UP = "FOLLOW_UP"
    COMPLETE = "COMPLETE"


class HandleMode:
    CENTER = "CENTER"
    DEPARTMENT = "DEPARTMENT"


# Maps action_type -> action_name in Chinese
ACTION_NAMES = {
    AppealAction.SUBMIT: "企业提交",
    AppealAction.MODIFY: "企业修改",
    AppealAction.SUPPLEMENT: "补充材料",
    AppealAction.ACCEPT: "受理",
    AppealAction.RETURN_SUPPLEMENT: "退回补充",
    AppealAction.REJECT: "不予受理",
    AppealAction.ASSIGN_DEPT: "分派部门",
    AppealAction.CENTER_HANDLE: "企服中心办理",
    AppealAction.DEPT_REPLY: "部门反馈",
    AppealAction.REVIEW_PASS: "审核通过",
    AppealAction.REVIEW_REJECT: "审核退回",
    AppealAction.REPLY_ENTERPRISE: "回复企业",
    AppealAction.EVALUATE: "企业评价",
    AppealAction.FOLLOW_UP: "线下回访",
    AppealAction.COMPLETE: "办结",
}

# Allowed statuses before each action
ALLOWED_STATUS_FOR_ACTION = {
    AppealAction.MODIFY: [AppealStatus.PENDING_ACCEPT, AppealStatus.NEED_SUPPLEMENT],
    AppealAction.SUPPLEMENT: [AppealStatus.NEED_SUPPLEMENT],
    AppealAction.ACCEPT: [AppealStatus.PENDING_ACCEPT],
    AppealAction.RETURN_SUPPLEMENT: [AppealStatus.PENDING_ACCEPT],
    AppealAction.REJECT: [AppealStatus.PENDING_ACCEPT],
    AppealAction.ASSIGN_DEPT: [AppealStatus.ACCEPTED, AppealStatus.REVIEW_REJECTED],
    AppealAction.CENTER_HANDLE: [AppealStatus.ACCEPTED, AppealStatus.CENTER_HANDLING],
    AppealAction.DEPT_REPLY: [AppealStatus.DEPT_HANDLING, AppealStatus.REVIEW_REJECTED],
    AppealAction.REVIEW_PASS: [AppealStatus.CENTER_REVIEWING],
    AppealAction.REVIEW_REJECT: [AppealStatus.CENTER_REVIEWING],
    AppealAction.EVALUATE: [AppealStatus.REPLIED, AppealStatus.PENDING_EVALUATION],
    AppealAction.COMPLETE: [AppealStatus.EVALUATED],
}
