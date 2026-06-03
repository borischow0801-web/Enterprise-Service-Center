"""管理端可维护字典类型定义。"""

# 管理端字典维护页面允许维护的 dictType
MAINTAINABLE_DICT_TYPES = frozenset({
    "APPEAL_TYPE",
    "APPEAL_REJECT_REASON",
    "GOV_MEETING_TOPIC",
    "GOV_MEETING_LEVEL",
    "GOV_MEETING_REJECT_REASON",
    "INDUSTRY_TYPE",
    "REGION",
    "MEETING_ROOM_TYPE",
    "MEETING_ROOM_FACILITY",
    "ENTERPRISE_TYPE",
    "MATERIAL_TYPE",
    "URGENCY_LEVEL",
})

# 系统内置字典，不在管理端维护页面展示
SYSTEM_DICT_TYPES = frozenset({
    "APPEAL_STATUS",
    "MEETING_BOOKING_STATUS",
    "GOV_MEETING_STATUS",
    "SATISFACTION_LEVEL",
    "DATA_SCOPE",
})

DICT_NOT_MAINTAINABLE_MSG = "该字典属于系统内置字典，不允许在管理端维护"


def is_maintainable_dict_type(dict_type: str) -> bool:
    return dict_type in MAINTAINABLE_DICT_TYPES
