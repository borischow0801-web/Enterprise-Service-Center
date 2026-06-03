"""
初始化演示数据脚本（可重复执行，不重复插入）

执行方式：
  cd /app/Enterprise-Service-Center
  .venv/bin/python scripts/init_demo_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from app.core.database import SessionLocal
from app.models.system import ServiceCenter, SysDictionary
from app.models.meeting_room import (
    MeetingRoom, MeetingRoomOpenRule, MeetingRoomSpecialDate,
    MeetingRoomMaterialRule,
)


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def upsert_dict(db, dict_type, dict_code, dict_label, dict_value, sort_no):
    exists = db.query(SysDictionary).filter(
        SysDictionary.dict_type == dict_type,
        SysDictionary.dict_code == dict_code,
        SysDictionary.deleted_flag == 0,
    ).first()
    if exists:
        return False
    db.add(SysDictionary(
        dict_type=dict_type,
        dict_code=dict_code,
        dict_label=dict_label,
        dict_value=dict_value,
        sort_no=sort_no,
        enabled=1,
    ))
    return True


# ─────────────────────────────────────────────────────────────────────────────
# 字典数据
# ─────────────────────────────────────────────────────────────────────────────

DICT_DATA = [
    # APPEAL_TYPE - 诉求类型
    ("APPEAL_TYPE", "POLICY_ADVICE", "政策咨询", "POLICY_ADVICE", 1),
    ("APPEAL_TYPE", "APPROVAL_COORD", "审批协调", "APPROVAL_COORD", 2),
    ("APPEAL_TYPE", "FACTOR_SUPPORT", "要素保障", "FACTOR_SUPPORT", 3),
    ("APPEAL_TYPE", "RIGHTS_PROTECT", "权益保护", "RIGHTS_PROTECT", 4),
    ("APPEAL_TYPE", "DISPUTE_RESOLVE", "纠纷化解", "DISPUTE_RESOLVE", 5),
    ("APPEAL_TYPE", "OTHER", "其他", "OTHER", 6),

    # APPEAL_STATUS - 诉求状态
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

    # APPEAL_REJECT_REASON - 诉求不予受理原因
    ("APPEAL_REJECT_REASON", "LEGAL_PROCEDURE", "已有法律程序", "LEGAL_PROCEDURE", 1),
    ("APPEAL_REJECT_REASON", "PETITION_CHANNEL", "应走信访渠道", "PETITION_CHANNEL", 2),
    ("APPEAL_REJECT_REASON", "MALICIOUS_OR_FALSE", "恶意/虚假申请", "MALICIOUS_OR_FALSE", 3),
    ("APPEAL_REJECT_REASON", "NON_COMPLIANT", "材料不符合要求", "NON_COMPLIANT", 4),
    ("APPEAL_REJECT_REASON", "OUT_OF_SCOPE", "超出服务范围", "OUT_OF_SCOPE", 5),

    # URGENCY_LEVEL - 紧急程度
    ("URGENCY_LEVEL", "NORMAL", "普通", "NORMAL", 1),
    ("URGENCY_LEVEL", "URGENT", "紧急", "URGENT", 2),
    ("URGENCY_LEVEL", "VERY_URGENT", "非常紧急", "VERY_URGENT", 3),

    # SATISFACTION_LEVEL - 满意度
    ("SATISFACTION_LEVEL", "SATISFIED", "满意", "SATISFIED", 1),
    ("SATISFACTION_LEVEL", "BASIC_SATISFIED", "基本满意", "BASIC_SATISFIED", 2),
    ("SATISFACTION_LEVEL", "UNSATISFIED", "不满意", "UNSATISFIED", 3),

    # INDUSTRY_TYPE - 行业类型
    ("INDUSTRY_TYPE", "MANUFACTURING", "制造业", "MANUFACTURING", 1),
    ("INDUSTRY_TYPE", "IT_SOFTWARE", "信息技术/软件", "IT_SOFTWARE", 2),
    ("INDUSTRY_TYPE", "FINANCE", "金融业", "FINANCE", 3),
    ("INDUSTRY_TYPE", "RETAIL", "批发零售", "RETAIL", 4),
    ("INDUSTRY_TYPE", "CONSTRUCTION", "建筑业", "CONSTRUCTION", 5),
    ("INDUSTRY_TYPE", "CATERING", "餐饮服务", "CATERING", 6),
    ("INDUSTRY_TYPE", "LOGISTICS", "交通运输/物流", "LOGISTICS", 7),
    ("INDUSTRY_TYPE", "EDUCATION", "教育", "EDUCATION", 8),
    ("INDUSTRY_TYPE", "MEDICAL", "医疗卫生", "MEDICAL", 9),
    ("INDUSTRY_TYPE", "OTHER", "其他", "OTHER", 10),

    # ENTERPRISE_TYPE - 企业类型
    ("ENTERPRISE_TYPE", "LIMITED_COMPANY", "有限责任公司", "LIMITED_COMPANY", 1),
    ("ENTERPRISE_TYPE", "JOINT_STOCK", "股份有限公司", "JOINT_STOCK", 2),
    ("ENTERPRISE_TYPE", "SOLE_PROPRIETOR", "个人独资企业", "SOLE_PROPRIETOR", 3),
    ("ENTERPRISE_TYPE", "PARTNERSHIP", "合伙企业", "PARTNERSHIP", 4),
    ("ENTERPRISE_TYPE", "FOREIGN", "外资企业", "FOREIGN", 5),
    ("ENTERPRISE_TYPE", "STATE_OWNED", "国有企业", "STATE_OWNED", 6),

    # MEETING_ROOM_TYPE - 会议室类型
    ("MEETING_ROOM_TYPE", "STANDARD", "标准会议室", "STANDARD", 1),
    ("MEETING_ROOM_TYPE", "MULTI_FUNCTION", "多功能厅", "MULTI_FUNCTION", 2),
    ("MEETING_ROOM_TYPE", "TRAINING", "培训室", "TRAINING", 3),
    ("MEETING_ROOM_TYPE", "BOARD", "董事会室", "BOARD", 4),
    ("MEETING_ROOM_TYPE", "VIDEO_CONF", "视频会议室", "VIDEO_CONF", 5),

    # MEETING_ROOM_FACILITY - 会议室设施
    ("MEETING_ROOM_FACILITY", "PROJECTOR", "投影仪", "PROJECTOR", 1),
    ("MEETING_ROOM_FACILITY", "SCREEN", "投影幕布", "SCREEN", 2),
    ("MEETING_ROOM_FACILITY", "WHITEBOARD", "白板", "WHITEBOARD", 3),
    ("MEETING_ROOM_FACILITY", "VIDEO_CONF", "视频会议系统", "VIDEO_CONF", 4),
    ("MEETING_ROOM_FACILITY", "MICROPHONE", "麦克风", "MICROPHONE", 5),
    ("MEETING_ROOM_FACILITY", "WIFI", "WiFi网络", "WIFI", 6),
    ("MEETING_ROOM_FACILITY", "AIR_COND", "空调", "AIR_COND", 7),
    ("MEETING_ROOM_FACILITY", "WATER", "饮用水", "WATER", 8),

    # MEETING_BOOKING_STATUS - 会议室预约状态
    ("MEETING_BOOKING_STATUS", "PENDING_AUDIT", "待审核", "PENDING_AUDIT", 1),
    ("MEETING_BOOKING_STATUS", "NEED_SUPPLEMENT", "退回补充材料", "NEED_SUPPLEMENT", 2),
    ("MEETING_BOOKING_STATUS", "REJECTED", "审核驳回", "REJECTED", 3),
    ("MEETING_BOOKING_STATUS", "APPROVED", "审核通过", "APPROVED", 4),
    ("MEETING_BOOKING_STATUS", "WAIT_USE", "待使用", "WAIT_USE", 5),
    ("MEETING_BOOKING_STATUS", "CANCELED", "已取消", "CANCELED", 6),
    ("MEETING_BOOKING_STATUS", "COMPLETED", "已完成", "COMPLETED", 7),
    ("MEETING_BOOKING_STATUS", "NO_SHOW", "爽约", "NO_SHOW", 8),

    # MATERIAL_TYPE - 材料类型
    ("MATERIAL_TYPE", "SEAL_APPLICATION", "盖章申请表", "SEAL_APPLICATION", 1),
    ("MATERIAL_TYPE", "BUSINESS_LICENSE", "营业执照复印件", "BUSINESS_LICENSE", 2),
    ("MATERIAL_TYPE", "ID_CARD", "法人身份证复印件", "ID_CARD", 3),
    ("MATERIAL_TYPE", "COMMITMENT_LETTER", "承诺书", "COMMITMENT_LETTER", 4),
    ("MATERIAL_TYPE", "OTHER", "其他材料", "OTHER", 5),

    # GOV_MEETING_TOPIC - 政企约见议题
    ("GOV_MEETING_TOPIC", "POLICY_CONSULT", "政策咨询", "POLICY_CONSULT", 1),
    ("GOV_MEETING_TOPIC", "APPROVAL_COORDINATION", "审批协调", "APPROVAL_COORDINATION", 2),
    ("GOV_MEETING_TOPIC", "FACTOR_SUPPORT", "要素保障", "FACTOR_SUPPORT", 3),
    ("GOV_MEETING_TOPIC", "DISPUTE_RESOLUTION", "纠纷化解", "DISPUTE_RESOLUTION", 4),
    ("GOV_MEETING_TOPIC", "OTHER", "其他", "OTHER", 5),

    # GOV_MEETING_LEVEL - 政企约见级别
    ("GOV_MEETING_LEVEL", "CENTER_STAFF", "企服中心工作人员", "CENTER_STAFF", 1),
    ("GOV_MEETING_LEVEL", "DEPARTMENT_SECTION", "科室负责人", "DEPARTMENT_SECTION", 2),
    ("GOV_MEETING_LEVEL", "DEPARTMENT_LEADER", "局处负责人", "DEPARTMENT_LEADER", 3),
    ("GOV_MEETING_LEVEL", "DISTRICT_LEADER", "区县级领导", "DISTRICT_LEADER", 4),
    ("GOV_MEETING_LEVEL", "CITY_LEADER", "市级领导", "CITY_LEADER", 5),
    ("GOV_MEETING_LEVEL", "SPECIAL_COORDINATION", "特别协调", "SPECIAL_COORDINATION", 6),

    # GOV_MEETING_STATUS - 政企约见状态
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

    # GOV_MEETING_REJECT_REASON - 政企约见驳回原因
    ("GOV_MEETING_REJECT_REASON", "LEGAL_PROCEDURE", "已有法律程序", "LEGAL_PROCEDURE", 1),
    ("GOV_MEETING_REJECT_REASON", "PETITION_CHANNEL", "应走信访渠道", "PETITION_CHANNEL", 2),
    ("GOV_MEETING_REJECT_REASON", "MALICIOUS_OR_FALSE", "恶意或虚假申请", "MALICIOUS_OR_FALSE", 3),
    ("GOV_MEETING_REJECT_REASON", "NON_COMPLIANT", "材料不符合要求", "NON_COMPLIANT", 4),
    ("GOV_MEETING_REJECT_REASON", "SECRET_OR_PRIVACY", "涉密或隐私事项", "SECRET_OR_PRIVACY", 5),
    ("GOV_MEETING_REJECT_REASON", "NON_ENTERPRISE_OPERATION", "非企业经营事项", "NON_ENTERPRISE_OPERATION", 6),
    ("GOV_MEETING_REJECT_REASON", "OUT_OF_SCOPE", "超出服务范围", "OUT_OF_SCOPE", 7),

    # DATA_SCOPE - 数据权限
    ("DATA_SCOPE", "ALL", "全部数据", "ALL", 1),
    ("DATA_SCOPE", "REGION", "本区县数据", "REGION", 2),
    ("DATA_SCOPE", "DEPARTMENT", "本部门数据", "DEPARTMENT", 3),
    ("DATA_SCOPE", "SELF", "本人数据", "SELF", 4),
]


# ─────────────────────────────────────────────────────────────────────────────
# 企服中心
# ─────────────────────────────────────────────────────────────────────────────

SERVICE_CENTERS = [
    {
        "center_name": "威海市企业综合服务中心",
        "region_code": "371000",
        "region_name": "威海市",
        "address": "威海市环翠区文化西路17号",
        "contact_name": "张经理",
        "contact_phone": "0631-5888888",
        "status": "ENABLED",
    },
    {
        "center_name": "环翠区企业综合服务中心",
        "region_code": "371002",
        "region_name": "环翠区",
        "address": "威海市环翠区统一路1号行政服务大厅",
        "contact_name": "李主任",
        "contact_phone": "0631-5666666",
        "status": "ENABLED",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 会议室（需要 service_center_id，动态确定）
# ─────────────────────────────────────────────────────────────────────────────

MEETING_ROOMS = [
    {
        "room_name": "威海市一号会议室",
        "room_type": "STANDARD",
        "region_code": "371000",
        "region_name": "威海市",
        "address": "威海市企业综合服务中心三楼301室",
        "capacity": 20,
        "facilities": "PROJECTOR,SCREEN,WHITEBOARD,WIFI,AIR_COND",
        "description": "标准会议室，配备投影仪和白板，适合中小型会议。",
        "booking_notice": "请提前2天预约，使用前请填写盖章申请表。",
        "status": "ENABLED",
        "center_name": "威海市企业综合服务中心",
    },
    {
        "room_name": "威海市多功能厅",
        "room_type": "MULTI_FUNCTION",
        "region_code": "371000",
        "region_name": "威海市",
        "address": "威海市企业综合服务中心二楼报告厅",
        "capacity": 80,
        "facilities": "PROJECTOR,SCREEN,MICROPHONE,VIDEO_CONF,WIFI,AIR_COND,WATER",
        "description": "大型多功能厅，配备专业音响和视频会议系统，适合大型培训、论坛。",
        "booking_notice": "请提前2天预约，大型活动请联系工作人员协助布置。",
        "status": "ENABLED",
        "center_name": "威海市企业综合服务中心",
    },
]


def init_service_centers(db):
    created = 0
    center_map = {}
    for sc in SERVICE_CENTERS:
        exists = db.query(ServiceCenter).filter(
            ServiceCenter.center_name == sc["center_name"],
            ServiceCenter.deleted_flag == 0,
        ).first()
        if exists:
            center_map[sc["center_name"]] = exists.id
        else:
            obj = ServiceCenter(**sc)
            db.add(obj)
            db.flush()
            center_map[sc["center_name"]] = obj.id
            created += 1
    return created, center_map


def init_meeting_rooms(db, center_map):
    created = 0
    room_ids = []
    for rm in MEETING_ROOMS:
        center_name = rm.pop("center_name")
        center_id = center_map.get(center_name)

        exists = db.query(MeetingRoom).filter(
            MeetingRoom.room_name == rm["room_name"],
            MeetingRoom.deleted_flag == 0,
        ).first()
        if exists:
            rm["center_name"] = center_name  # put it back
            room_ids.append(exists.id)
            continue

        room = MeetingRoom(
            **rm,
            service_center_id=center_id,
            service_center_name=center_name,
        )
        rm["center_name"] = center_name
        db.add(room)
        db.flush()
        room_ids.append(room.id)
        created += 1

        # Configure weekday open rules (Mon-Fri: 08:30-17:30, Sat-Sun: closed)
        for weekday in range(1, 8):
            if weekday <= 5:
                rule = MeetingRoomOpenRule(
                    room_id=room.id,
                    weekday=weekday,
                    open_flag=1,
                    start_time="08:30",
                    end_time="17:30",
                )
            else:
                rule = MeetingRoomOpenRule(
                    room_id=room.id,
                    weekday=weekday,
                    open_flag=0,
                    start_time=None,
                    end_time=None,
                )
            db.add(rule)

        # Add required material rule: 盖章申请表
        mat = MeetingRoomMaterialRule(
            room_id=room.id,
            enterprise_type=None,
            material_name="会议室使用申请表（盖章）",
            material_code="SEAL_APPLICATION",
            required_flag=1,
            template_attachment_id=None,
            description="企业使用会议室须填写并加盖公章的申请表",
            enabled=1,
        )
        db.add(mat)

    return created, room_ids


def init_special_dates(db, center_map):
    created = 0
    # Add National Day holiday closure
    center_id = center_map.get("威海市企业综合服务中心")
    special_dates = [
        {
            "region_code": "371000",
            "service_center_id": center_id,
            "special_date": date(2026, 10, 1),
            "date_type": "HOLIDAY",
            "open_flag": 0,
            "reason": "国庆节假日",
        },
        {
            "region_code": "371000",
            "service_center_id": center_id,
            "special_date": date(2026, 10, 2),
            "date_type": "HOLIDAY",
            "open_flag": 0,
            "reason": "国庆节假日",
        },
        {
            "region_code": "371000",
            "service_center_id": center_id,
            "special_date": date(2026, 10, 7),
            "date_type": "WORKDAY",
            "open_flag": 1,
            "reason": "国庆节调休工作日",
        },
    ]
    for sd in special_dates:
        exists = db.query(MeetingRoomSpecialDate).filter(
            MeetingRoomSpecialDate.region_code == sd["region_code"],
            MeetingRoomSpecialDate.special_date == sd["special_date"],
            MeetingRoomSpecialDate.deleted_flag == 0,
        ).first()
        if not exists:
            db.add(MeetingRoomSpecialDate(**sd))
            created += 1
    return created


def main():
    db = SessionLocal()
    try:
        print("=" * 50)
        print("初始化演示数据")
        print("=" * 50)

        # 1. Dictionaries
        dict_ins = dict_skip = 0
        for item in DICT_DATA:
            if upsert_dict(db, *item):
                dict_ins += 1
            else:
                dict_skip += 1
        db.flush()
        print(f"[字典] 新增 {dict_ins} 条，跳过 {dict_skip} 条")

        # 2. Service centers
        sc_created, center_map = init_service_centers(db)
        db.flush()
        print(f"[企服中心] 新增 {sc_created} 条，共 {len(center_map)} 个")

        # 3. Meeting rooms
        rm_created, room_ids = init_meeting_rooms(db, center_map)
        db.flush()
        print(f"[会议室] 新增 {rm_created} 个（含开放规则和材料规则）")

        # 4. Special dates
        sd_created = init_special_dates(db, center_map)
        db.flush()
        print(f"[特殊日期] 新增 {sd_created} 条")

        db.commit()
        print("=" * 50)
        print("✓ 演示数据初始化完成")
        print("=" * 50)
        print(f"\n企服中心 ID 映射: {center_map}")
        print(f"会议室 IDs: {room_ids}")

    except Exception as e:
        db.rollback()
        print(f"✗ 初始化失败: {e}")
        import traceback; traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
