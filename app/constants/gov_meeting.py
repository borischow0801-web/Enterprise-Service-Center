class GovMeetingStatus:
    PENDING_AUDIT = "PENDING_AUDIT"           # 待审核
    NEED_SUPPLEMENT = "NEED_SUPPLEMENT"       # 退回补正
    REJECTED = "REJECTED"                     # 不予受理
    ACCEPTED = "ACCEPTED"                     # 受理通过
    PENDING_ARRANGE = "PENDING_ARRANGE"       # 待安排
    ARRANGED = "ARRANGED"                     # 已安排
    WAIT_MEETING = "WAIT_MEETING"             # 待约见
    MEETING_COMPLETED = "MEETING_COMPLETED"   # 约见完成
    PENDING_EVALUATION = "PENDING_EVALUATION" # 待评价
    EVALUATED = "EVALUATED"                   # 已评价
    COMPLETED = "COMPLETED"                   # 已办结


class GovMeetingAction:
    SUBMIT = "SUBMIT"
    MODIFY = "MODIFY"
    SUPPLEMENT = "SUPPLEMENT"
    ACCEPT = "ACCEPT"                         # admin: 受理通过 → PENDING_ARRANGE
    RETURN_SUPPLEMENT = "RETURN_SUPPLEMENT"   # admin: 退回补正 → NEED_SUPPLEMENT
    REJECT = "REJECT"                         # admin: 不予受理 → REJECTED
    ARRANGE = "ARRANGE"                       # admin: 创建安排 → ARRANGED
    UPDATE_ARRANGEMENT = "UPDATE_ARRANGEMENT" # admin: 修改安排 (no status change)
    CONFIRM = "CONFIRM"                       # admin: 确认通知 → WAIT_MEETING
    COMPLETE = "COMPLETE"                     # admin: 约见完成 → MEETING_COMPLETED
    ADD_RECORD = "ADD_RECORD"                 # admin: 填写纪要 (no status change)
    NOTIFY_EVALUATION = "NOTIFY_EVALUATION"   # admin: 触发评价 → PENDING_EVALUATION
    EVALUATE = "EVALUATE"                     # enterprise: 评价 → EVALUATED
    FINISH = "FINISH"                         # admin: 办结 → COMPLETED


class MeetingMethod:
    ON_SITE = "ON_SITE"           # 现场会议
    VIDEO = "VIDEO"               # 视频会议
    PHONE = "PHONE"               # 电话沟通


class ParticipantType:
    GOV = "GOV"
    ENTERPRISE = "ENTERPRISE"


ACTION_NAMES = {
    GovMeetingAction.SUBMIT: "企业提交",
    GovMeetingAction.MODIFY: "企业修改",
    GovMeetingAction.SUPPLEMENT: "补充材料",
    GovMeetingAction.ACCEPT: "受理通过",
    GovMeetingAction.RETURN_SUPPLEMENT: "退回补正",
    GovMeetingAction.REJECT: "不予受理",
    GovMeetingAction.ARRANGE: "安排约见",
    GovMeetingAction.UPDATE_ARRANGEMENT: "修改安排",
    GovMeetingAction.CONFIRM: "确认通知",
    GovMeetingAction.COMPLETE: "约见完成",
    GovMeetingAction.ADD_RECORD: "填写纪要",
    GovMeetingAction.NOTIFY_EVALUATION: "触发评价",
    GovMeetingAction.EVALUATE: "企业评价",
    GovMeetingAction.FINISH: "办结",
}

ALLOWED_STATUS_FOR_ACTION = {
    GovMeetingAction.MODIFY: [GovMeetingStatus.PENDING_AUDIT, GovMeetingStatus.NEED_SUPPLEMENT],
    GovMeetingAction.SUPPLEMENT: [GovMeetingStatus.NEED_SUPPLEMENT],
    GovMeetingAction.ACCEPT: [GovMeetingStatus.PENDING_AUDIT],
    GovMeetingAction.RETURN_SUPPLEMENT: [GovMeetingStatus.PENDING_AUDIT],
    GovMeetingAction.REJECT: [GovMeetingStatus.PENDING_AUDIT],
    GovMeetingAction.ARRANGE: [GovMeetingStatus.PENDING_ARRANGE],
    GovMeetingAction.UPDATE_ARRANGEMENT: [GovMeetingStatus.ARRANGED, GovMeetingStatus.WAIT_MEETING],
    GovMeetingAction.CONFIRM: [GovMeetingStatus.ARRANGED],
    GovMeetingAction.COMPLETE: [GovMeetingStatus.WAIT_MEETING],
    GovMeetingAction.ADD_RECORD: [
        GovMeetingStatus.MEETING_COMPLETED,
        GovMeetingStatus.PENDING_EVALUATION,
        GovMeetingStatus.EVALUATED,
        GovMeetingStatus.COMPLETED,
    ],
    GovMeetingAction.NOTIFY_EVALUATION: [GovMeetingStatus.MEETING_COMPLETED],
    GovMeetingAction.EVALUATE: [GovMeetingStatus.PENDING_EVALUATION],
    GovMeetingAction.FINISH: [
        GovMeetingStatus.MEETING_COMPLETED,
        GovMeetingStatus.PENDING_EVALUATION,
        GovMeetingStatus.EVALUATED,
    ],
}
