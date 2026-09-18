"""
Appeal service layer — all business logic lives here.
"""
from datetime import datetime
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.constants.appeal import AppealStatus, AppealAction, HandleMode, ACTION_NAMES, ALLOWED_STATUS_FOR_ACTION
from app.core.exceptions import StatusNotAllowedException, NotFoundException, AppException, ErrorCode
from app.core.permission import DataPermissionService
from app.repositories.appeal_repo import AppealRepository, generate_appeal_no
from app.repositories.enterprise_repo import EnterpriseRepository
from app.models.appeal import AppealMain


def _check_status(appeal: AppealMain, action: str) -> None:
    allowed = ALLOWED_STATUS_FOR_ACTION.get(action, [])
    if appeal.status not in allowed:
        raise StatusNotAllowedException(
            f"当前诉求状态【{appeal.status}】不允许执行【{ACTION_NAMES.get(action, action)}】操作"
        )


def _appeal_to_dict(appeal: AppealMain) -> dict:
    return {
        "id": appeal.id,
        "appealNo": appeal.appeal_no,
        "enterpriseId": appeal.enterprise_id,
        "enterpriseName": appeal.enterprise_name,
        "creditCode": appeal.credit_code,
        "title": appeal.title,
        "content": appeal.content,
        "contactName": appeal.contact_name,
        "contactPhone": appeal.contact_phone,
        "industryCode": appeal.industry_code,
        "industryName": appeal.industry_name,
        "regionCode": appeal.region_code,
        "regionName": appeal.region_name,
        "appealTypeCode": appeal.appeal_type_code,
        "appealTypeName": appeal.appeal_type_name,
        "urgencyLevel": appeal.urgency_level,
        "status": appeal.status,
        "handleMode": appeal.handle_mode,
        "responsibleDeptId": appeal.responsible_dept_id,
        "responsibleDeptName": appeal.responsible_dept_name,
        "replyDeadline": appeal.reply_deadline.isoformat() if appeal.reply_deadline else None,
        "submittedAt": appeal.submitted_at.isoformat() if appeal.submitted_at else None,
        "acceptedAt": appeal.accepted_at.isoformat() if appeal.accepted_at else None,
        "repliedAt": appeal.replied_at.isoformat() if appeal.replied_at else None,
        "completedAt": appeal.completed_at.isoformat() if appeal.completed_at else None,
        "evaluatedAt": appeal.evaluated_at.isoformat() if appeal.evaluated_at else None,
        "createdAt": appeal.created_at.isoformat() if appeal.created_at else None,
        "updatedAt": appeal.updated_at.isoformat() if appeal.updated_at else None,
    }


class AppealService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = AppealRepository(db)
        self.ent_repo = EnterpriseRepository(db)

    # ── Enterprise actions ────────────────────────────────────────────────────

    def submit_appeal(self, enterprise_id: int, data: dict) -> dict:
        enterprise = self.ent_repo.get_by_id(enterprise_id)
        if enterprise is None:
            raise NotFoundException("企业信息不存在")

        appeal = self.repo.create_appeal(
            appeal_no=generate_appeal_no(self.db),
            enterprise_id=enterprise.id,
            enterprise_name=enterprise.enterprise_name,
            credit_code=enterprise.credit_code,
            title=data["title"],
            content=data["content"],
            contact_name=data["contactName"],
            contact_phone=data["contactPhone"],
            industry_code=data.get("industryCode"),
            industry_name=data.get("industryName"),
            region_code=data.get("regionCode") or enterprise.region_code or "",
            region_name=data.get("regionName") or enterprise.region_name or "",
            urgency_level=data.get("urgencyLevel"),
            status=AppealStatus.PENDING_ACCEPT,
            submitted_at=datetime.utcnow(),
        )

        if data.get("attachmentIds"):
            self.repo.bind_attachments(appeal.id, data["attachmentIds"])

        self.repo.add_record(
            appeal_id=appeal.id,
            action_type=AppealAction.SUBMIT,
            action_name=ACTION_NAMES[AppealAction.SUBMIT],
            before_status=None,
            after_status=AppealStatus.PENDING_ACCEPT,
            operator_type="ENTERPRISE",
            operator_id=str(enterprise.id),
            operator_name=enterprise.enterprise_name,
        )
        self.repo.add_operation_log(
            operator_type="ENTERPRISE",
            operator_id=str(enterprise.id),
            operator_name=enterprise.enterprise_name,
            operation_type=AppealAction.SUBMIT,
            business_id=appeal.id,
            operation_content=f"企业提交诉求：{appeal.title}",
            after_status=AppealStatus.PENDING_ACCEPT,
        )
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def list_enterprise_appeals(self, enterprise_id: int, status: Optional[str], page_no: int, page_size: int):
        total, records = self.repo.list_for_enterprise(enterprise_id, status, page_no, page_size)
        return total, [_appeal_to_dict(r) for r in records]

    def get_appeal_detail_for_enterprise(self, appeal_id: int, enterprise_id: int) -> dict:
        appeal = self.repo.get_by_id_and_enterprise(appeal_id, enterprise_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        return self._build_detail(appeal)

    def modify_appeal(self, appeal_id: int, enterprise_id: int, data: dict) -> dict:
        appeal = self.repo.get_by_id_and_enterprise(appeal_id, enterprise_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        _check_status(appeal, AppealAction.MODIFY)

        update_fields = {k: v for k, v in {
            "title": data.get("title"),
            "content": data.get("content"),
            "contact_name": data.get("contactName"),
            "contact_phone": data.get("contactPhone"),
            "industry_code": data.get("industryCode"),
            "industry_name": data.get("industryName"),
            "region_code": data.get("regionCode"),
            "region_name": data.get("regionName"),
            "urgency_level": data.get("urgencyLevel"),
        }.items() if v is not None}

        self.repo.update_appeal(appeal, **update_fields)
        enterprise = self.ent_repo.get_by_id(enterprise_id)
        self.repo.add_record(
            appeal_id=appeal.id,
            action_type=AppealAction.MODIFY,
            action_name=ACTION_NAMES[AppealAction.MODIFY],
            before_status=appeal.status,
            after_status=appeal.status,
            operator_type="ENTERPRISE",
            operator_id=str(enterprise_id),
            operator_name=enterprise.enterprise_name if enterprise else str(enterprise_id),
        )
        self.repo.add_operation_log(
            operator_type="ENTERPRISE",
            operator_id=str(enterprise_id),
            operator_name=enterprise.enterprise_name if enterprise else str(enterprise_id),
            operation_type=AppealAction.MODIFY,
            business_id=appeal.id,
            operation_content="企业修改诉求",
        )
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def supplement_appeal(self, appeal_id: int, enterprise_id: int, data: dict) -> dict:
        appeal = self.repo.get_by_id_and_enterprise(appeal_id, enterprise_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        _check_status(appeal, AppealAction.SUPPLEMENT)

        old_status = appeal.status
        self.repo.update_appeal(appeal, status=AppealStatus.PENDING_ACCEPT)

        if data.get("attachmentIds"):
            self.repo.bind_attachments(appeal.id, data["attachmentIds"])

        enterprise = self.ent_repo.get_by_id(enterprise_id)
        op_name = enterprise.enterprise_name if enterprise else str(enterprise_id)
        self.repo.add_record(
            appeal_id=appeal.id,
            action_type=AppealAction.SUPPLEMENT,
            action_name=ACTION_NAMES[AppealAction.SUPPLEMENT],
            before_status=old_status,
            after_status=AppealStatus.PENDING_ACCEPT,
            operator_type="ENTERPRISE",
            operator_id=str(enterprise_id),
            operator_name=op_name,
            opinion=data.get("content"),
        )
        self.repo.add_operation_log(
            operator_type="ENTERPRISE",
            operator_id=str(enterprise_id),
            operator_name=op_name,
            operation_type=AppealAction.SUPPLEMENT,
            business_id=appeal.id,
            operation_content="企业补充材料",
            before_status=old_status,
            after_status=AppealStatus.PENDING_ACCEPT,
        )
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def evaluate_appeal(self, appeal_id: int, enterprise_id: int, data: dict) -> dict:
        appeal = self.repo.get_by_id_and_enterprise(appeal_id, enterprise_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        _check_status(appeal, AppealAction.EVALUATE)

        existing_eval = self.repo.get_evaluation(appeal_id)
        if existing_eval:
            raise AppException(ErrorCode.STATUS_NOT_ALLOWED, "该诉求已评价，不能重复评价")

        now = datetime.utcnow()
        self.repo.create_evaluation(
            business_type="APPEAL",
            business_id=appeal.id,
            enterprise_id=enterprise_id,
            satisfaction=data["satisfaction"],
            score=data["score"],
            resolved_flag=data.get("resolvedFlag"),
            comment=data.get("comment"),
            evaluate_time=now,
        )

        new_status = AppealStatus.EVALUATED
        old_status = appeal.status
        self.repo.update_appeal(appeal, status=new_status, evaluated_at=now)

        enterprise = self.ent_repo.get_by_id(enterprise_id)
        op_name = enterprise.enterprise_name if enterprise else str(enterprise_id)
        self.repo.add_record(
            appeal_id=appeal.id,
            action_type=AppealAction.EVALUATE,
            action_name=ACTION_NAMES[AppealAction.EVALUATE],
            before_status=old_status,
            after_status=new_status,
            operator_type="ENTERPRISE",
            operator_id=str(enterprise_id),
            operator_name=op_name,
            opinion=data.get("comment"),
        )
        self.repo.add_operation_log(
            operator_type="ENTERPRISE",
            operator_id=str(enterprise_id),
            operator_name=op_name,
            operation_type=AppealAction.EVALUATE,
            business_id=appeal.id,
            operation_content=f"企业评价：{data['satisfaction']}，{data['score']}星",
            before_status=old_status,
            after_status=new_status,
        )
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    # ── Admin actions ─────────────────────────────────────────────────────────

    def list_admin_appeals(self, query: dict, data_scope: str, current_region_code: str, current_dept_id: str):
        total, records = self.repo.list_for_admin(
            enterprise_name=query.get("enterpriseName"),
            credit_code=query.get("creditCode"),
            status=query.get("status"),
            appeal_type_code=query.get("appealTypeCode"),
            region_code_filter=query.get("regionCode"),
            dept_id_filter=query.get("responsibleDeptId"),
            start_date=query.get("startDate"),
            end_date=query.get("endDate"),
            page_no=query.get("pageNo", 1),
            page_size=query.get("pageSize", 10),
            data_scope=data_scope,
            current_region_code=current_region_code,
            current_dept_id=current_dept_id,
        )
        return total, [_appeal_to_dict(r) for r in records]

    def get_appeal_detail_for_admin(self, appeal_id: int, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        return self._build_detail(appeal)

    def _assert_scope(self, appeal: AppealMain, operator: dict) -> None:
        assignments = self.repo.get_assignments(appeal.id)
        dept_ids = {appeal.responsible_dept_id} | {a.assigned_dept_id for a in assignments}
        DataPermissionService.assert_can_access(operator, region_code=appeal.region_code, dept_ids=dept_ids)

    def accept_appeal(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.ACCEPT)

        old_status = appeal.status
        now = datetime.utcnow()
        self.repo.update_appeal(
            appeal,
            status=AppealStatus.ACCEPTED,
            appeal_type_code=data["appealTypeCode"],
            appeal_type_name=data["appealTypeName"],
            reply_deadline=data.get("replyDeadline"),
            accepted_at=now,
        )
        self._write_audit_trail(appeal, AppealAction.ACCEPT, old_status, AppealStatus.ACCEPTED, operator, data.get("opinion"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def return_supplement(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.RETURN_SUPPLEMENT)

        old_status = appeal.status
        self.repo.update_appeal(appeal, status=AppealStatus.NEED_SUPPLEMENT)
        self._write_audit_trail(appeal, AppealAction.RETURN_SUPPLEMENT, old_status, AppealStatus.NEED_SUPPLEMENT, operator, data.get("opinion"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def reject_appeal(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.REJECT)

        old_status = appeal.status
        opinion = data.get("opinion", "")
        if data.get("reasonName"):
            opinion = f"[{data['reasonName']}] {opinion}"
        self.repo.update_appeal(appeal, status=AppealStatus.REJECTED)
        self._write_audit_trail(appeal, AppealAction.REJECT, old_status, AppealStatus.REJECTED, operator, opinion)
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def center_handle(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.CENTER_HANDLE)

        old_status = appeal.status
        now = datetime.utcnow()
        self.repo.update_appeal(
            appeal,
            handle_mode=HandleMode.CENTER,
            status=AppealStatus.PENDING_EVALUATION,
            replied_at=now,
        )
        if data.get("attachmentIds"):
            self.repo.bind_attachments(appeal.id, data["attachmentIds"])

        self._write_audit_trail(appeal, AppealAction.CENTER_HANDLE, old_status, AppealStatus.PENDING_EVALUATION, operator, data.get("replyContent"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def assign_dept(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.ASSIGN_DEPT)

        old_status = appeal.status
        now = datetime.utcnow()
        self.repo.update_appeal(
            appeal,
            handle_mode=HandleMode.DEPARTMENT,
            responsible_dept_id=data["assignedDeptId"],
            responsible_dept_name=data["assignedDeptName"],
            status=AppealStatus.DEPT_HANDLING,
        )
        self.repo.create_assignment(
            appeal_id=appeal.id,
            assigned_dept_id=data["assignedDeptId"],
            assigned_dept_name=data["assignedDeptName"],
            assign_opinion=data.get("assignOpinion"),
            assigned_at=now,
            deadline=data.get("deadline"),
            status="PENDING",
        )
        self._write_audit_trail(appeal, AppealAction.ASSIGN_DEPT, old_status, AppealStatus.DEPT_HANDLING, operator, data.get("assignOpinion"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def dept_reply(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.DEPT_REPLY)

        old_status = appeal.status
        now = datetime.utcnow()
        assignment = self.repo.get_latest_active_assignment(appeal_id)
        if assignment:
            assignment.reply_content = data.get("replyContent")
            assignment.replied_at = now
            assignment.status = "REPLIED"
            self.db.flush()

        if data.get("attachmentIds"):
            self.repo.bind_attachments(appeal.id, data["attachmentIds"])

        self.repo.update_appeal(appeal, status=AppealStatus.CENTER_REVIEWING, replied_at=now)
        self._write_audit_trail(appeal, AppealAction.DEPT_REPLY, old_status, AppealStatus.CENTER_REVIEWING, operator, data.get("replyContent"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def review_reply(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.REVIEW_PASS)

        old_status = appeal.status
        if data["passed"]:
            new_status = AppealStatus.PENDING_EVALUATION
            action = AppealAction.REVIEW_PASS
        else:
            new_status = AppealStatus.REVIEW_REJECTED
            action = AppealAction.REVIEW_REJECT

        self.repo.update_appeal(appeal, status=new_status)
        self._write_audit_trail(appeal, action, old_status, new_status, operator, data.get("opinion"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def complete_appeal(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)
        _check_status(appeal, AppealAction.COMPLETE)

        old_status = appeal.status
        now = datetime.utcnow()
        self.repo.update_appeal(appeal, status=AppealStatus.COMPLETED, completed_at=now)
        self._write_audit_trail(appeal, AppealAction.COMPLETE, old_status, AppealStatus.COMPLETED, operator, data.get("remark"))
        self.db.commit()
        self.db.refresh(appeal)
        return _appeal_to_dict(appeal)

    def add_followup(self, appeal_id: int, data: dict, operator: dict) -> dict:
        appeal = self.repo.get_by_id(appeal_id)
        if appeal is None:
            raise NotFoundException("诉求不存在")
        self._assert_scope(appeal, operator)

        now = datetime.utcnow()
        self.repo.create_followup(
            appeal_id=appeal_id,
            responsible_dept_id=data.get("responsibleDeptId"),
            responsible_dept_name=data.get("responsibleDeptName"),
            followup_status="COMPLETED",
            followup_method=data.get("followupMethod"),
            followup_content=data.get("followupContent"),
            followup_result=data.get("followupResult"),
            followup_user_id=operator["user_id_str"],
            followup_user_name=operator["real_name"],
            followup_time=now,
        )
        self._write_audit_trail(appeal, AppealAction.FOLLOW_UP, appeal.status, appeal.status, operator, data.get("followupContent"))
        self.db.commit()
        return {"appealId": appeal_id}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _write_audit_trail(
        self,
        appeal: AppealMain,
        action: str,
        before_status: Optional[str],
        after_status: Optional[str],
        operator: dict,
        opinion: Optional[str] = None,
    ) -> None:
        op_type = operator.get("operator_type", "USER")
        op_id = operator.get("operator_id", "")
        op_name = operator.get("operator_name", "")
        dept_id = operator.get("department_id")
        dept_name = operator.get("department_name")

        self.repo.add_record(
            appeal_id=appeal.id,
            action_type=action,
            action_name=ACTION_NAMES.get(action, action),
            before_status=before_status,
            after_status=after_status,
            operator_type=op_type,
            operator_id=op_id,
            operator_name=op_name,
            opinion=opinion,
            operator_dept_id=dept_id,
            operator_dept_name=dept_name,
        )
        self.repo.add_operation_log(
            operator_type=op_type,
            operator_id=op_id,
            operator_name=op_name,
            operation_type=action,
            business_id=appeal.id,
            operation_content=opinion,
            before_status=before_status,
            after_status=after_status,
        )

    def _build_detail(self, appeal: AppealMain) -> dict:
        base = _appeal_to_dict(appeal)
        # Attachments
        attachments = self.repo.get_attachments(appeal.id)
        base["attachments"] = [
            {
                "id": a.id,
                "originalName": a.original_name,
                "fileExt": a.file_ext,
                "fileSize": a.file_size,
                "storagePath": a.storage_path,
                "createdAt": a.created_at.isoformat() if a.created_at else None,
            }
            for a in attachments
        ]
        # Records
        records = self.repo.get_records(appeal.id)
        base["records"] = [
            {
                "id": r.id,
                "actionType": r.action_type,
                "actionName": r.action_name,
                "beforeStatus": r.before_status,
                "afterStatus": r.after_status,
                "opinion": r.opinion,
                "operatorType": r.operator_type,
                "operatorName": r.operator_name,
                "operatorDeptName": r.operator_dept_name,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]
        # Assignments
        assignments = self.repo.get_assignments(appeal.id)
        base["assignments"] = [
            {
                "id": a.id,
                "assignedDeptId": a.assigned_dept_id,
                "assignedDeptName": a.assigned_dept_name,
                "assignOpinion": a.assign_opinion,
                "assignedAt": a.assigned_at.isoformat() if a.assigned_at else None,
                "deadline": a.deadline.isoformat() if a.deadline else None,
                "status": a.status,
                "replyContent": a.reply_content,
                "repliedAt": a.replied_at.isoformat() if a.replied_at else None,
            }
            for a in assignments
        ]
        # Evaluation
        ev = self.repo.get_evaluation(appeal.id)
        base["evaluation"] = (
            {
                "id": ev.id,
                "satisfaction": ev.satisfaction,
                "score": ev.score,
                "resolvedFlag": ev.resolved_flag,
                "comment": ev.comment,
                "evaluateTime": ev.evaluate_time.isoformat() if ev.evaluate_time else None,
            }
            if ev
            else None
        )
        # Followups
        followups = self.repo.get_followups(appeal.id)
        base["followups"] = [
            {
                "id": f.id,
                "followupStatus": f.followup_status,
                "followupMethod": f.followup_method,
                "followupContent": f.followup_content,
                "followupResult": f.followup_result,
                "followupUserName": f.followup_user_name,
                "followupTime": f.followup_time.isoformat() if f.followup_time else None,
            }
            for f in followups
        ]
        return base
