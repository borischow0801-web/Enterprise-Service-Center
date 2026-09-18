import random
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.constants.permission import resolve_scope_branch, ScopeBranch
from app.models.gov_meeting import (
    GovMeetingApply, GovMeetingAudit, GovMeetingArrangement,
    GovMeetingParticipant, GovMeetingRecord,
)
from app.models.system import SysAttachment, SysOperationLog, SysEvaluation


def generate_apply_no(db: Session) -> str:
    from app.utils.serial_no import generate_daily_serial
    return generate_daily_serial(db, GovMeetingApply, GovMeetingApply.apply_no, "YJ", "GOV_MEETING")


class GovMeetingRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Apply ─────────────────────────────────────────────────────────────────

    def get_apply_by_id(self, apply_id: int) -> Optional[GovMeetingApply]:
        return self.db.query(GovMeetingApply).filter(
            GovMeetingApply.id == apply_id,
            GovMeetingApply.deleted_flag == 0,
        ).first()

    def get_apply_by_id_and_enterprise(self, apply_id: int, enterprise_id: int) -> Optional[GovMeetingApply]:
        return self.db.query(GovMeetingApply).filter(
            GovMeetingApply.id == apply_id,
            GovMeetingApply.enterprise_id == enterprise_id,
            GovMeetingApply.deleted_flag == 0,
        ).first()

    def create_apply(self, **kwargs) -> GovMeetingApply:
        obj = GovMeetingApply(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_apply(self, apply: GovMeetingApply, **kwargs) -> GovMeetingApply:
        for k, v in kwargs.items():
            setattr(apply, k, v)
        apply.updated_at = datetime.utcnow()
        self.db.flush()
        return apply

    def list_applies_enterprise(self, enterprise_id: int, status: Optional[str], page_no: int, page_size: int):
        q = self.db.query(GovMeetingApply).filter(
            GovMeetingApply.enterprise_id == enterprise_id,
            GovMeetingApply.deleted_flag == 0,
        )
        if status:
            q = q.filter(GovMeetingApply.status == status)
        total = q.count()
        records = q.order_by(GovMeetingApply.submitted_at.desc()).offset((page_no - 1) * page_size).limit(page_size).all()
        return total, records

    def list_applies_admin(self, enterprise_name, credit_code, status, start_date, end_date,
                           region_code_filter, service_center_id, page_no, page_size,
                           data_scope, current_region_code):
        q = self.db.query(GovMeetingApply).filter(GovMeetingApply.deleted_flag == 0)
        # Fail Closed：政企约见没有部门级归属概念，DEPARTMENT/SELF 按区域近似处理
        # （与会议室模块一致的历史设计），未知 data_scope 一律不返回数据。
        branch = resolve_scope_branch(data_scope)
        if branch == ScopeBranch.DENY:
            return 0, []
        if branch in (ScopeBranch.REGION, ScopeBranch.DEPARTMENT):
            if not current_region_code:
                return 0, []
            q = q.filter(GovMeetingApply.region_code == current_region_code)
        if enterprise_name:
            q = q.filter(GovMeetingApply.enterprise_name.like(f"%{enterprise_name}%"))
        if credit_code:
            q = q.filter(GovMeetingApply.credit_code == credit_code)
        if status:
            q = q.filter(GovMeetingApply.status == status)
        if start_date:
            q = q.filter(GovMeetingApply.submitted_at >= start_date)
        if end_date:
            q = q.filter(GovMeetingApply.submitted_at <= f"{end_date} 23:59:59")
        if region_code_filter:
            q = q.filter(GovMeetingApply.region_code == region_code_filter)
        if service_center_id:
            q = q.filter(GovMeetingApply.service_center_id == service_center_id)
        total = q.count()
        records = q.order_by(GovMeetingApply.submitted_at.desc()).offset((page_no - 1) * page_size).limit(page_size).all()
        return total, records

    # ── Audit ─────────────────────────────────────────────────────────────────

    def add_audit(self, apply_id: int, action_type: str, action_name: str,
                  before_status: Optional[str], after_status: Optional[str],
                  operator_type: str, operator_id: str, operator_name: str,
                  opinion: Optional[str] = None,
                  operator_dept_id: Optional[str] = None,
                  operator_dept_name: Optional[str] = None) -> GovMeetingAudit:
        obj = GovMeetingAudit(
            apply_id=apply_id, action_type=action_type, action_name=action_name,
            before_status=before_status, after_status=after_status,
            opinion=opinion, operator_type=operator_type,
            operator_id=operator_id, operator_name=operator_name,
            operator_dept_id=operator_dept_id, operator_dept_name=operator_dept_name,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_audits(self, apply_id: int):
        return self.db.query(GovMeetingAudit).filter(
            GovMeetingAudit.apply_id == apply_id
        ).order_by(GovMeetingAudit.created_at.asc()).all()

    # ── Arrangement ───────────────────────────────────────────────────────────

    def get_arrangement_by_id(self, arr_id: int) -> Optional[GovMeetingArrangement]:
        return self.db.query(GovMeetingArrangement).filter(
            GovMeetingArrangement.id == arr_id,
            GovMeetingArrangement.deleted_flag == 0,
        ).first()

    def get_arrangement_by_apply(self, apply_id: int) -> Optional[GovMeetingArrangement]:
        return self.db.query(GovMeetingArrangement).filter(
            GovMeetingArrangement.apply_id == apply_id,
            GovMeetingArrangement.deleted_flag == 0,
        ).order_by(GovMeetingArrangement.id.desc()).first()

    def create_arrangement(self, **kwargs) -> GovMeetingArrangement:
        obj = GovMeetingArrangement(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_arrangement(self, arr: GovMeetingArrangement, **kwargs) -> GovMeetingArrangement:
        for k, v in kwargs.items():
            setattr(arr, k, v)
        arr.updated_at = datetime.utcnow()
        self.db.flush()
        return arr

    # ── Participants ──────────────────────────────────────────────────────────

    def replace_participants(self, arrangement_id: int, apply_id: int, participants: list) -> None:
        self.db.query(GovMeetingParticipant).filter(
            GovMeetingParticipant.arrangement_id == arrangement_id
        ).delete(synchronize_session=False)
        for p in participants:
            obj = GovMeetingParticipant(
                arrangement_id=arrangement_id,
                apply_id=apply_id,
                participant_type=p["participantType"],
                participant_name=p["participantName"],
                participant_title=p.get("participantTitle"),
                participant_dept_id=p.get("participantDeptId"),
                participant_dept_name=p.get("participantDeptName"),
                contact_phone=p.get("contactPhone"),
                role_name=p.get("roleName"),
                sort_no=p.get("sortNo", 0),
            )
            self.db.add(obj)
        self.db.flush()

    def get_participants(self, arrangement_id: int):
        return self.db.query(GovMeetingParticipant).filter(
            GovMeetingParticipant.arrangement_id == arrangement_id
        ).order_by(GovMeetingParticipant.participant_type, GovMeetingParticipant.sort_no).all()

    # ── Record ────────────────────────────────────────────────────────────────

    def create_record(self, **kwargs) -> GovMeetingRecord:
        obj = GovMeetingRecord(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_records(self, apply_id: int):
        return self.db.query(GovMeetingRecord).filter(
            GovMeetingRecord.apply_id == apply_id,
            GovMeetingRecord.deleted_flag == 0,
        ).order_by(GovMeetingRecord.created_at.asc()).all()

    # ── Attachments ───────────────────────────────────────────────────────────

    def bind_attachments(self, apply_id: int, attachment_ids: list) -> None:
        if not attachment_ids:
            return
        self.db.query(SysAttachment).filter(
            SysAttachment.id.in_(attachment_ids),
            SysAttachment.deleted_flag == 0,
        ).update({"business_type": "GOV_MEETING", "business_id": apply_id}, synchronize_session=False)

    def get_attachments(self, apply_id: int):
        return self.db.query(SysAttachment).filter(
            SysAttachment.business_type == "GOV_MEETING",
            SysAttachment.business_id == apply_id,
            SysAttachment.deleted_flag == 0,
        ).all()

    # ── Evaluation ────────────────────────────────────────────────────────────

    def get_evaluation(self, apply_id: int) -> Optional[SysEvaluation]:
        return self.db.query(SysEvaluation).filter(
            SysEvaluation.business_type == "GOV_MEETING",
            SysEvaluation.business_id == apply_id,
            SysEvaluation.deleted_flag == 0,
        ).first()

    def create_evaluation(self, **kwargs) -> SysEvaluation:
        obj = SysEvaluation(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    # ── Operation Log ─────────────────────────────────────────────────────────

    def add_operation_log(self, operator_type: str, operator_id: str, operator_name: str,
                          operation_type: str, business_id: Optional[int] = None,
                          operation_content: Optional[str] = None,
                          before_status: Optional[str] = None,
                          after_status: Optional[str] = None) -> None:
        log = SysOperationLog(
            operator_type=operator_type, operator_id=operator_id, operator_name=operator_name,
            business_type="GOV_MEETING", business_id=business_id,
            operation_type=operation_type, operation_content=operation_content,
            before_status=before_status, after_status=after_status,
        )
        self.db.add(log)
        self.db.flush()
