from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.appeal import AppealMain, AppealRecord, AppealAssignment, AppealFollowup
from app.models.system import SysAttachment, SysEvaluation, SysOperationLog


def generate_appeal_no(db: Session) -> str:
    from app.models.appeal import AppealMain
    from app.utils.serial_no import generate_daily_serial
    return generate_daily_serial(db, AppealMain, AppealMain.appeal_no, "SQ")


class AppealRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── AppealMain ──────────────────────────────────────────────────────────

    def get_by_id(self, appeal_id: int) -> Optional[AppealMain]:
        return self.db.query(AppealMain).filter(
            AppealMain.id == appeal_id,
            AppealMain.deleted_flag == 0,
        ).first()

    def get_by_id_and_enterprise(self, appeal_id: int, enterprise_id: int) -> Optional[AppealMain]:
        return self.db.query(AppealMain).filter(
            AppealMain.id == appeal_id,
            AppealMain.enterprise_id == enterprise_id,
            AppealMain.deleted_flag == 0,
        ).first()

    def create_appeal(self, **kwargs) -> AppealMain:
        appeal = AppealMain(**kwargs)
        self.db.add(appeal)
        self.db.flush()
        return appeal

    def update_appeal(self, appeal: AppealMain, **kwargs) -> AppealMain:
        for k, v in kwargs.items():
            setattr(appeal, k, v)
        appeal.updated_at = datetime.utcnow()
        self.db.flush()
        return appeal

    def list_for_enterprise(
        self,
        enterprise_id: int,
        status: Optional[str],
        page_no: int,
        page_size: int,
    ):
        q = self.db.query(AppealMain).filter(
            AppealMain.enterprise_id == enterprise_id,
            AppealMain.deleted_flag == 0,
        )
        if status:
            q = q.filter(AppealMain.status == status)
        total = q.count()
        records = (
            q.order_by(AppealMain.submitted_at.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return total, records

    def list_for_admin(
        self,
        enterprise_name: Optional[str],
        credit_code: Optional[str],
        status: Optional[str],
        appeal_type_code: Optional[str],
        region_code_filter: Optional[str],
        dept_id_filter: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
        page_no: int,
        page_size: int,
        data_scope: str,
        current_region_code: Optional[str],
        current_dept_id: Optional[str],
    ):
        q = self.db.query(AppealMain).filter(AppealMain.deleted_flag == 0)

        # Data scope filtering
        if data_scope == "REGION" and current_region_code:
            q = q.filter(AppealMain.region_code == current_region_code)
        elif data_scope in ("DEPARTMENT", "SELF") and current_dept_id:
            # TODO: SELF scope — currently treated same as DEPARTMENT
            q = q.filter(
                or_(
                    AppealMain.responsible_dept_id == current_dept_id,
                    AppealMain.id.in_(
                        self.db.query(AppealAssignment.appeal_id).filter(
                            AppealAssignment.assigned_dept_id == current_dept_id
                        )
                    ),
                )
            )

        if enterprise_name:
            q = q.filter(AppealMain.enterprise_name.like(f"%{enterprise_name}%"))
        if credit_code:
            q = q.filter(AppealMain.credit_code == credit_code)
        if status:
            q = q.filter(AppealMain.status == status)
        if appeal_type_code:
            q = q.filter(AppealMain.appeal_type_code == appeal_type_code)
        if region_code_filter:
            q = q.filter(AppealMain.region_code == region_code_filter)
        if dept_id_filter:
            q = q.filter(AppealMain.responsible_dept_id == dept_id_filter)
        if start_date:
            q = q.filter(AppealMain.submitted_at >= start_date)
        if end_date:
            q = q.filter(AppealMain.submitted_at <= f"{end_date} 23:59:59")

        total = q.count()
        records = (
            q.order_by(AppealMain.submitted_at.desc())
            .offset((page_no - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return total, records

    # ── AppealRecord ──────────────────────────────────────────────────────────

    def add_record(
        self,
        appeal_id: int,
        action_type: str,
        action_name: str,
        before_status: Optional[str],
        after_status: Optional[str],
        operator_type: str,
        operator_id: str,
        operator_name: str,
        opinion: Optional[str] = None,
        operator_dept_id: Optional[str] = None,
        operator_dept_name: Optional[str] = None,
    ) -> AppealRecord:
        rec = AppealRecord(
            appeal_id=appeal_id,
            action_type=action_type,
            action_name=action_name,
            before_status=before_status,
            after_status=after_status,
            opinion=opinion,
            operator_type=operator_type,
            operator_id=operator_id,
            operator_name=operator_name,
            operator_dept_id=operator_dept_id,
            operator_dept_name=operator_dept_name,
        )
        self.db.add(rec)
        self.db.flush()
        return rec

    def get_records(self, appeal_id: int):
        return (
            self.db.query(AppealRecord)
            .filter(AppealRecord.appeal_id == appeal_id)
            .order_by(AppealRecord.created_at.asc())
            .all()
        )

    # ── AppealAssignment ──────────────────────────────────────────────────────

    def create_assignment(self, **kwargs) -> AppealAssignment:
        obj = AppealAssignment(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_latest_active_assignment(self, appeal_id: int) -> Optional[AppealAssignment]:
        return (
            self.db.query(AppealAssignment)
            .filter(
                AppealAssignment.appeal_id == appeal_id,
                AppealAssignment.deleted_flag == 0,
            )
            .order_by(AppealAssignment.id.desc())
            .first()
        )

    def get_assignments(self, appeal_id: int):
        return (
            self.db.query(AppealAssignment)
            .filter(AppealAssignment.appeal_id == appeal_id, AppealAssignment.deleted_flag == 0)
            .order_by(AppealAssignment.id.asc())
            .all()
        )

    # ── AppealFollowup ────────────────────────────────────────────────────────

    def create_followup(self, **kwargs) -> AppealFollowup:
        obj = AppealFollowup(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_followups(self, appeal_id: int):
        return (
            self.db.query(AppealFollowup)
            .filter(AppealFollowup.appeal_id == appeal_id, AppealFollowup.deleted_flag == 0)
            .order_by(AppealFollowup.id.asc())
            .all()
        )

    # ── Attachments ───────────────────────────────────────────────────────────

    def bind_attachments(self, appeal_id: int, attachment_ids: list[int]) -> None:
        if not attachment_ids:
            return
        self.db.query(SysAttachment).filter(
            SysAttachment.id.in_(attachment_ids),
            SysAttachment.deleted_flag == 0,
        ).update(
            {"business_type": "APPEAL", "business_id": appeal_id},
            synchronize_session=False,
        )

    def get_attachments(self, appeal_id: int):
        return (
            self.db.query(SysAttachment)
            .filter(
                SysAttachment.business_type == "APPEAL",
                SysAttachment.business_id == appeal_id,
                SysAttachment.deleted_flag == 0,
            )
            .all()
        )

    # ── Evaluation ────────────────────────────────────────────────────────────

    def get_evaluation(self, appeal_id: int) -> Optional[SysEvaluation]:
        return (
            self.db.query(SysEvaluation)
            .filter(
                SysEvaluation.business_type == "APPEAL",
                SysEvaluation.business_id == appeal_id,
                SysEvaluation.deleted_flag == 0,
            )
            .first()
        )

    def create_evaluation(self, **kwargs) -> SysEvaluation:
        obj = SysEvaluation(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    # ── OperationLog ──────────────────────────────────────────────────────────

    def add_operation_log(
        self,
        operator_type: str,
        operator_id: str,
        operator_name: str,
        operation_type: str,
        business_id: Optional[int] = None,
        operation_content: Optional[str] = None,
        before_status: Optional[str] = None,
        after_status: Optional[str] = None,
    ) -> None:
        log = SysOperationLog(
            operator_type=operator_type,
            operator_id=operator_id,
            operator_name=operator_name,
            business_type="APPEAL",
            business_id=business_id,
            operation_type=operation_type,
            operation_content=operation_content,
            before_status=before_status,
            after_status=after_status,
        )
        self.db.add(log)
        self.db.flush()
