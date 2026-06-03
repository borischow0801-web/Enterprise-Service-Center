"""
初始化共享会议室默认材料规则（全局通用 + 环翠区可选）。
Run: python scripts/init_material_rules.py
可重复执行，已存在同 scope + material_code + enterprise_type 的规则将跳过。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.meeting_room import MeetingRoomMaterialRule

REGION_CODE = "371002"
REGION_NAME = "环翠区"

# (enterprise_type or None, material_code, material_name, required_flag, sort_no, description)
RULES = [
    (None, "MEETING_ROOM_APPLICATION_FORM", "会议室使用申请表", 1, 1,
     "下载模板填写盖章后扫描上传。"),
    (None, "APPLICANT_ID_CARD_PHOTO", "申请人身份证照片", 1, 2, None),
    (None, "MEETING_PLAN", "会议方案", 1, 3, None),
    ("ENTERPRISE", "BUSINESS_LICENSE", "营业执照复印件", 1, 10, None),
    ("PRIVATE_NON_ENTERPRISE", "PRIVATE_NON_ENTERPRISE_CERT", "民办非企业登记证书", 1, 10, None),
    ("TRAINING_INSTITUTION", "SCHOOL_LICENSE", "办学许可证", 1, 10, None),
    ("MEDICAL_INSTITUTION", "MEDICAL_INSTITUTION_LICENSE", "医疗机构执业许可证", 1, 10, None),
    ("FOUNDATION", "FOUNDATION_LEGAL_PERSON_CERT", "基金会法人登记证书", 1, 10, None),
    ("SOCIAL_ORGANIZATION", "SOCIAL_ORGANIZATION_CERT", "社会团体登记证书", 1, 10, None),
    ("RELIGIOUS_ORGANIZATION", "SOCIAL_ORGANIZATION_CERT", "社会团体登记证书", 1, 10, None),
    ("RELIGIOUS_ORGANIZATION", "RELIGIOUS_AFFAIRS_APPROVAL", "宗教事务管理部门批文或证明", 1, 11, None),
    ("OTHER", "OTHER_QUALIFICATION", "其他主体资质证明", 1, 10, None),
]


def _exists_rule(db, *, region_code, service_center_id, ent_type, code):
    q = db.query(MeetingRoomMaterialRule).filter(
        MeetingRoomMaterialRule.deleted_flag == 0,
        MeetingRoomMaterialRule.material_code == code,
        MeetingRoomMaterialRule.service_center_id == service_center_id,
    )
    if region_code is None:
        q = q.filter(MeetingRoomMaterialRule.region_code.is_(None))
    else:
        q = q.filter(MeetingRoomMaterialRule.region_code == region_code)
    if ent_type is None:
        q = q.filter(MeetingRoomMaterialRule.enterprise_type.is_(None))
    else:
        q = q.filter(MeetingRoomMaterialRule.enterprise_type == ent_type)
    return q.first()


def _insert_rules(db, region_code, region_name, service_center_id):
    inserted = skipped = 0
    for ent_type, code, name, req, sort_no, desc in RULES:
        if _exists_rule(db, region_code=region_code, service_center_id=service_center_id,
                        ent_type=ent_type, code=code):
            skipped += 1
            continue
        db.add(MeetingRoomMaterialRule(
            region_code=region_code,
            region_name=region_name,
            service_center_id=service_center_id,
            enterprise_type=ent_type,
            material_name=name,
            material_code=code,
            required_flag=req,
            description=desc,
            enabled=1,
            sort_no=sort_no,
        ))
        inserted += 1
    return inserted, skipped


def init_material_rules():
    db = SessionLocal()
    try:
        g_ins, g_skip = _insert_rules(db, region_code=None, region_name=None, service_center_id=None)
        r_ins, r_skip = _insert_rules(db, region_code=REGION_CODE, region_name=REGION_NAME, service_center_id=None)
        db.commit()
        print(
            f"材料规则初始化完成：全局新增 {g_ins} 跳过 {g_skip}；"
            f"{REGION_CODE} 新增 {r_ins} 跳过 {r_skip}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_material_rules()
