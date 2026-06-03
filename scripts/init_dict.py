"""
Initialize base dictionary data.
Run: python scripts/init_dict.py
Safe to run multiple times — existing records are skipped.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.core.database import SessionLocal
from app.models.system import SysDictionary

# (dict_type, dict_code, dict_label, dict_value, sort_no)
DICT_DATA = [
    # ── 满意度 ───────────────────────────────────────────────────────────────
    ("SATISFACTION_LEVEL", "SATISFIED", "满意", "SATISFIED", 1),
    ("SATISFACTION_LEVEL", "BASIC_SATISFIED", "基本满意", "BASIC_SATISFIED", 2),
    ("SATISFACTION_LEVEL", "UNSATISFIED", "不满意", "UNSATISFIED", 3),

    # ── 紧急程度 ─────────────────────────────────────────────────────────────
    ("URGENCY_LEVEL", "NORMAL", "普通", "NORMAL", 1),
    ("URGENCY_LEVEL", "URGENT", "紧急", "URGENT", 2),

    # ── 诉求状态 ─────────────────────────────────────────────────────────────
    ("APPEAL_STATUS", "PENDING_ACCEPT", "待受理", "PENDING_ACCEPT", 1),
    ("APPEAL_STATUS", "NEED_SUPPLEMENT", "退回补充", "NEED_SUPPLEMENT", 2),
    ("APPEAL_STATUS", "REJECTED", "不予受理", "REJECTED", 3),
    ("APPEAL_STATUS", "ACCEPTED", "已受理", "ACCEPTED", 4),
    ("APPEAL_STATUS", "CENTER_HANDLING", "企服中心办理中", "CENTER_HANDLING", 5),
    ("APPEAL_STATUS", "DEPT_HANDLING", "部门办理中", "DEPT_HANDLING", 6),
    ("APPEAL_STATUS", "DEPT_REPLIED", "部门已反馈", "DEPT_REPLIED", 7),
    ("APPEAL_STATUS", "CENTER_REVIEWING", "企服中心审核", "CENTER_REVIEWING", 8),
    ("APPEAL_STATUS", "REVIEW_REJECTED", "审核退回", "REVIEW_REJECTED", 9),
    ("APPEAL_STATUS", "REPLIED", "已回复", "REPLIED", 10),
    ("APPEAL_STATUS", "PENDING_EVALUATION", "待评价", "PENDING_EVALUATION", 11),
    ("APPEAL_STATUS", "EVALUATED", "已评价", "EVALUATED", 12),
    ("APPEAL_STATUS", "COMPLETED", "已办结", "COMPLETED", 13),

    # ── 诉求类型 ─────────────────────────────────────────────────────────────
    ("APPEAL_TYPE", "NORMAL_APPEAL", "普通诉求", "NORMAL_APPEAL", 1),
    ("APPEAL_TYPE", "SPECIAL_APPEAL", "特殊诉求", "SPECIAL_APPEAL", 2),
    ("APPEAL_TYPE", "POLICY_CONSULT", "政策咨询", "POLICY_CONSULT", 3),
    ("APPEAL_TYPE", "POLICY_ADVICE", "政策诉求", "POLICY_ADVICE", 4),
    ("APPEAL_TYPE", "BIZ_CONSULT", "业务咨询", "BIZ_CONSULT", 5),
    ("APPEAL_TYPE", "PROBLEM_COORDINATION", "问题协调", "PROBLEM_COORDINATION", 6),
    ("APPEAL_TYPE", "COMPLAINT_SUGGESTION", "投诉建议", "COMPLAINT_SUGGESTION", 7),
    ("APPEAL_TYPE", "HELP", "帮办代办", "HELP", 8),
    ("APPEAL_TYPE", "OTHER", "其他", "OTHER", 9),

    # ── 不予受理原因 ─────────────────────────────────────────────────────────
    ("APPEAL_REJECT_REASON", "OUT_OF_SCOPE", "不属于受理范围", "OUT_OF_SCOPE", 1),
    ("APPEAL_REJECT_REASON", "MATERIAL_INCOMPLETE", "材料不完整", "MATERIAL_INCOMPLETE", 2),
    ("APPEAL_REJECT_REASON", "DUPLICATE_SUBMIT", "重复提交", "DUPLICATE_SUBMIT", 3),
    ("APPEAL_REJECT_REASON", "LEGAL_PROCEDURE", "应通过诉讼仲裁等程序解决", "LEGAL_PROCEDURE", 4),
    ("APPEAL_REJECT_REASON", "PETITION_CHANNEL", "已进入信访渠道", "PETITION_CHANNEL", 5),
    ("APPEAL_REJECT_REASON", "OTHER", "其他", "OTHER", 6),

    # ── 行业类型 ─────────────────────────────────────────────────────────────
    ("INDUSTRY_TYPE", "MANUFACTURING", "制造业", "MANUFACTURING", 1),
    ("INDUSTRY_TYPE", "SERVICE", "服务业", "SERVICE", 2),
    ("INDUSTRY_TYPE", "AGRICULTURE", "农业", "AGRICULTURE", 3),
    ("INDUSTRY_TYPE", "CONSTRUCTION", "建筑业", "CONSTRUCTION", 4),
    ("INDUSTRY_TYPE", "TRADE", "商贸流通", "TRADE", 5),
    ("INDUSTRY_TYPE", "TECH", "科技创新", "TECH", 6),
    ("INDUSTRY_TYPE", "OTHER", "其他", "OTHER", 7),

    # ── 区划（威海市下属区划） ────────────────────────────────────────────────
    ("REGION", "371000", "威海市", "371000", 1),
    ("REGION", "371002", "环翠区", "371002", 2),
    ("REGION", "371003", "文登区", "371003", 3),
    ("REGION", "371082", "荣成市", "371082", 4),
    ("REGION", "371083", "乳山市", "371083", 5),

    # ── 预约状态 ─────────────────────────────────────────────────────────────
    ("MEETING_BOOKING_STATUS", "PENDING_AUDIT", "待审核", "PENDING_AUDIT", 1),
    ("MEETING_BOOKING_STATUS", "NEED_SUPPLEMENT", "退回补充材料", "NEED_SUPPLEMENT", 2),
    ("MEETING_BOOKING_STATUS", "REJECTED", "审核驳回", "REJECTED", 3),
    ("MEETING_BOOKING_STATUS", "APPROVED", "审核通过", "APPROVED", 4),
    ("MEETING_BOOKING_STATUS", "WAIT_USE", "待使用", "WAIT_USE", 5),
    ("MEETING_BOOKING_STATUS", "CANCELED", "已取消", "CANCELED", 6),
    ("MEETING_BOOKING_STATUS", "COMPLETED", "已完成", "COMPLETED", 7),
    ("MEETING_BOOKING_STATUS", "NO_SHOW", "爽约", "NO_SHOW", 8),

    # ── 政企约见状态 ─────────────────────────────────────────────────────────
    ("GOV_MEETING_STATUS", "PENDING_AUDIT", "待审核", "PENDING_AUDIT", 1),
    ("GOV_MEETING_STATUS", "NEED_SUPPLEMENT", "退回补正", "NEED_SUPPLEMENT", 2),
    ("GOV_MEETING_STATUS", "REJECTED", "不予受理", "REJECTED", 3),
    ("GOV_MEETING_STATUS", "ACCEPTED", "受理通过", "ACCEPTED", 4),
    ("GOV_MEETING_STATUS", "PENDING_ARRANGE", "待安排", "PENDING_ARRANGE", 5),
    ("GOV_MEETING_STATUS", "ARRANGED", "已安排", "ARRANGED", 6),
    ("GOV_MEETING_STATUS", "WAIT_MEETING", "待约见", "WAIT_MEETING", 7),
    ("GOV_MEETING_STATUS", "MEETING_COMPLETED", "约见完成", "MEETING_COMPLETED", 8),
    ("GOV_MEETING_STATUS", "PENDING_EVALUATION", "待评价", "PENDING_EVALUATION", 9),
    ("GOV_MEETING_STATUS", "EVALUATED", "已评价", "EVALUATED", 10),
    ("GOV_MEETING_STATUS", "COMPLETED", "已办结", "COMPLETED", 11),

    # ── 政企约见议题 ─────────────────────────────────────────────────────────
    ("GOV_MEETING_TOPIC", "POLICY_CONSULT", "政策咨询", "POLICY_CONSULT", 1),
    ("GOV_MEETING_TOPIC", "APPROVAL_COORDINATION", "审批协调", "APPROVAL_COORDINATION", 2),
    ("GOV_MEETING_TOPIC", "FACTOR_SUPPORT", "要素保障", "FACTOR_SUPPORT", 3),
    ("GOV_MEETING_TOPIC", "DISPUTE_RESOLUTION", "纠纷化解", "DISPUTE_RESOLUTION", 4),
    ("GOV_MEETING_TOPIC", "OTHER", "其他", "OTHER", 5),

    # ── 政企约见级别 ─────────────────────────────────────────────────────────
    ("GOV_MEETING_LEVEL", "CENTER_STAFF", "企服中心工作人员", "CENTER_STAFF", 1),
    ("GOV_MEETING_LEVEL", "DEPARTMENT_SECTION", "科室负责人", "DEPARTMENT_SECTION", 2),
    ("GOV_MEETING_LEVEL", "DEPARTMENT_LEADER", "局处负责人", "DEPARTMENT_LEADER", 3),
    ("GOV_MEETING_LEVEL", "DISTRICT_LEADER", "区县级领导", "DISTRICT_LEADER", 4),
    ("GOV_MEETING_LEVEL", "CITY_LEADER", "市级领导", "CITY_LEADER", 5),
    ("GOV_MEETING_LEVEL", "SPECIAL_COORDINATION", "特别协调", "SPECIAL_COORDINATION", 6),

    # ── 政企约见驳回原因 ─────────────────────────────────────────────────────
    ("GOV_MEETING_REJECT_REASON", "LEGAL_PROCEDURE", "已进入司法或行政复议程序，不适合通过约见方式处理", "LEGAL_PROCEDURE", 1),
    ("GOV_MEETING_REJECT_REASON", "PETITION_CHANNEL", "事项性质属于信访投诉类，应通过信访渠道反映", "PETITION_CHANNEL", 2),
    ("GOV_MEETING_REJECT_REASON", "MALICIOUS_OR_FALSE", "申请内容存在恶意、虚假或重复提交情形", "MALICIOUS_OR_FALSE", 3),
    ("GOV_MEETING_REJECT_REASON", "NON_COMPLIANT", "提交材料不完整或不符合规定要求", "NON_COMPLIANT", 4),
    ("GOV_MEETING_REJECT_REASON", "SECRET_OR_PRIVACY", "申请涉及国家秘密、商业秘密或个人隐私，不宜约见", "SECRET_OR_PRIVACY", 5),
    ("GOV_MEETING_REJECT_REASON", "NON_ENTERPRISE_OPERATION", "申请事项与企业生产经营无关", "NON_ENTERPRISE_OPERATION", 6),
    ("GOV_MEETING_REJECT_REASON", "OUT_OF_SCOPE", "申请事项超出政企约见服务受理范围", "OUT_OF_SCOPE", 7),
    ("GOV_MEETING_REJECT_REASON", "OTHER", "其他原因（详见审核意见）", "OTHER", 8),

    # ── 数据范围 ─────────────────────────────────────────────────────────────
    ("DATA_SCOPE", "ALL", "全部数据", "ALL", 1),
    ("DATA_SCOPE", "REGION", "本区县数据", "REGION", 2),
    ("DATA_SCOPE", "DEPARTMENT", "本部门数据", "DEPARTMENT", 3),
    ("DATA_SCOPE", "SELF", "本人数据", "SELF", 4),

    # ── 回访方式 ─────────────────────────────────────────────────────────────
    ("FOLLOWUP_METHOD", "PHONE", "电话回访", "PHONE", 1),
    ("FOLLOWUP_METHOD", "VISIT", "上门回访", "VISIT", 2),
    ("FOLLOWUP_METHOD", "ONLINE", "线上回访", "ONLINE", 3),
    ("FOLLOWUP_METHOD", "OTHER", "其他方式", "OTHER", 4),

    # ── 申请主体类型（会议室预约）────────────────────────────────────────────
    ("ENTERPRISE_TYPE", "ENTERPRISE", "企业", "ENTERPRISE", 1),
    ("ENTERPRISE_TYPE", "PRIVATE_NON_ENTERPRISE", "民办非企业", "PRIVATE_NON_ENTERPRISE", 2),
    ("ENTERPRISE_TYPE", "TRAINING_INSTITUTION", "非事业单位培训教育机构", "TRAINING_INSTITUTION", 3),
    ("ENTERPRISE_TYPE", "MEDICAL_INSTITUTION", "非事业单位医疗机构", "MEDICAL_INSTITUTION", 4),
    ("ENTERPRISE_TYPE", "FOUNDATION", "基金会", "FOUNDATION", 5),
    ("ENTERPRISE_TYPE", "SOCIAL_ORGANIZATION", "社会团体", "SOCIAL_ORGANIZATION", 6),
    ("ENTERPRISE_TYPE", "RELIGIOUS_ORGANIZATION", "宗教团体", "RELIGIOUS_ORGANIZATION", 7),
    ("ENTERPRISE_TYPE", "OTHER", "其他", "OTHER", 8),

    # ── 会议室类型 ───────────────────────────────────────────────────────────
    ("MEETING_ROOM_TYPE", "STANDARD", "标准会议室", "STANDARD", 1),
    ("MEETING_ROOM_TYPE", "MULTI_FUNCTION", "多功能厅", "MULTI_FUNCTION", 2),
    ("MEETING_ROOM_TYPE", "TRAINING", "培训室", "TRAINING", 3),
    ("MEETING_ROOM_TYPE", "BOARD", "董事会室", "BOARD", 4),
    ("MEETING_ROOM_TYPE", "VIDEO_CONF", "视频会议室", "VIDEO_CONF", 5),

    # ── 会议室设施 ─────────────────────────────────────────────────────────────
    ("MEETING_ROOM_FACILITY", "PROJECTOR", "投影仪", "PROJECTOR", 1),
    ("MEETING_ROOM_FACILITY", "SCREEN", "投影幕布", "SCREEN", 2),
    ("MEETING_ROOM_FACILITY", "WHITEBOARD", "白板", "WHITEBOARD", 3),
    ("MEETING_ROOM_FACILITY", "VIDEO_CONF", "视频会议系统", "VIDEO_CONF", 4),
    ("MEETING_ROOM_FACILITY", "MICROPHONE", "麦克风", "MICROPHONE", 5),
    ("MEETING_ROOM_FACILITY", "WIFI", "WiFi网络", "WIFI", 6),
    ("MEETING_ROOM_FACILITY", "AIR_COND", "空调", "AIR_COND", 7),
    ("MEETING_ROOM_FACILITY", "WATER", "饮用水", "WATER", 8),

    # ── 材料类型 ───────────────────────────────────────────────────────────────
    ("MATERIAL_TYPE", "SEAL_APPLICATION", "盖章申请表", "SEAL_APPLICATION", 1),
    ("MATERIAL_TYPE", "BUSINESS_LICENSE", "营业执照复印件", "BUSINESS_LICENSE", 2),
    ("MATERIAL_TYPE", "ID_CARD", "法人身份证复印件", "ID_CARD", 3),
    ("MATERIAL_TYPE", "COMMITMENT_LETTER", "承诺书", "COMMITMENT_LETTER", 4),
    ("MATERIAL_TYPE", "OTHER", "其他材料", "OTHER", 5),
]


def init_dict():
    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0
        for dict_type, dict_code, dict_label, dict_value, sort_no in DICT_DATA:
            exists = db.query(SysDictionary).filter(
                SysDictionary.dict_type == dict_type,
                SysDictionary.dict_code == dict_code,
                SysDictionary.deleted_flag == 0,
            ).first()
            if exists:
                skipped += 1
                continue
            item = SysDictionary(
                dict_type=dict_type,
                dict_code=dict_code,
                dict_label=dict_label,
                dict_value=dict_value,
                sort_no=sort_no,
                enabled=1,
            )
            db.add(item)
            inserted += 1
        db.commit()
        print(f"初始化完成：新增 {inserted} 条，跳过 {skipped} 条")
    except Exception as e:
        db.rollback()
        print(f"初始化失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_dict()
