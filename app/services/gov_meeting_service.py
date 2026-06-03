"""
Government-Enterprise Meeting (政企约见) Service.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.constants.gov_meeting import (
    GovMeetingStatus, GovMeetingAction, ACTION_NAMES, ALLOWED_STATUS_FOR_ACTION,
)
from app.core.exceptions import StatusNotAllowedException, NotFoundException, ParamException
from app.repositories.gov_meeting_repo import GovMeetingRepository, generate_apply_no
from app.repositories.enterprise_repo import EnterpriseRepository
from app.models.gov_meeting import GovMeetingApply


def _check_status(apply: GovMeetingApply, action: str) -> None:
    allowed = ALLOWED_STATUS_FOR_ACTION.get(action, [])
    if apply.status not in allowed:
        raise StatusNotAllowedException(
            f"当前申请状态【{apply.status}】不允许执行【{ACTION_NAMES.get(action, action)}】操作"
        )


def _apply_to_dict(apply: GovMeetingApply) -> dict:
    return {
        "id": apply.id,
        "applyNo": apply.apply_no,
        "enterpriseId": apply.enterprise_id,
        "enterpriseName": apply.enterprise_name,
        "creditCode": apply.credit_code,
        "contactName": apply.contact_name,
        "contactPhone": apply.contact_phone,
        "topicCode": apply.topic_code,
        "topicName": apply.topic_name,
        "meetingLevel": apply.meeting_level,
        "expectedLevelCode": apply.expected_level_code,
        "expectedLevelName": apply.expected_level_name,
        "finalLevelCode": apply.final_level_code,
        "finalLevelName": apply.final_level_name,
        "title": apply.title,
        "content": apply.meeting_content,
        "discussionItem": apply.discussion_item,
        "urgencyLevel": apply.urgency_level,
        "industryCode": apply.industry_code,
        "industryName": apply.industry_name,
        "registeredAddress": apply.registered_address,
        "description": apply.description,
        "commitmentChecked": apply.commitment_checked,
        "regionCode": apply.region_code,
        "regionName": apply.region_name,
        "serviceCenterId": apply.service_center_id,
        "serviceCenterName": apply.service_center_name,
        "status": apply.status,
        "rejectReasonCode": apply.reject_reason_code,
        "rejectReasonName": apply.reject_reason_name,
        "rejectOpinion": apply.reject_opinion,
        "submittedAt": apply.submitted_at.isoformat() if apply.submitted_at else None,
        "acceptedAt": apply.accepted_at.isoformat() if apply.accepted_at else None,
        "arrangedAt": apply.arranged_at.isoformat() if apply.arranged_at else None,
        "meetingAt": apply.meeting_at.isoformat() if apply.meeting_at else None,
        "completedAt": apply.completed_at.isoformat() if apply.completed_at else None,
        "evaluatedAt": apply.evaluated_at.isoformat() if apply.evaluated_at else None,
        "finishedAt": apply.finished_at.isoformat() if apply.finished_at else None,
        "createdAt": apply.created_at.isoformat() if apply.created_at else None,
        "updatedAt": apply.updated_at.isoformat() if apply.updated_at else None,
    }


def _arrangement_to_dict(arr, participants=None) -> dict:
    if arr is None:
        return None
    return {
        "id": arr.id,
        "applyId": arr.apply_id,
        "meetingDate": arr.meeting_date.isoformat() if arr.meeting_date else None,
        "meetingPlace": arr.meeting_place,
        "meetingMethod": arr.meeting_method,
        "govContactName": arr.gov_contact_name,
        "govContactPhone": arr.gov_contact_phone,
        "startTime": arr.start_time.isoformat() if arr.start_time else None,
        "endTime": arr.end_time.isoformat() if arr.end_time else None,
        "hostDeptId": arr.host_dept_id,
        "hostDeptName": arr.host_dept_name,
        "notes": arr.notes,
        "remark": arr.remark,
        "confirmedFlag": arr.confirmed_flag,
        "participants": [
            {
                "id": p.id,
                "participantType": p.participant_type,
                "participantName": p.participant_name,
                "participantTitle": p.participant_title,
                "participantDeptId": p.participant_dept_id,
                "participantDeptName": p.participant_dept_name,
                "contactPhone": p.contact_phone,
                "roleName": p.role_name,
                "sortNo": p.sort_no,
            }
            for p in (participants or [])
        ],
    }


def _record_to_dict(rec) -> dict:
    return {
        "id": rec.id,
        "applyId": rec.apply_id,
        "arrangementId": rec.arrangement_id,
        "content": rec.content,
        "conclusions": rec.conclusions,
        "followUpItems": rec.follow_up_items,
        "recorderId": rec.recorder_id,
        "recorderName": rec.recorder_name,
        "recordTime": rec.record_time.isoformat() if rec.record_time else None,
        "createdAt": rec.created_at.isoformat() if rec.created_at else None,
    }


def _audit_to_dict(a) -> dict:
    return {
        "id": a.id,
        "applyId": a.apply_id,
        "actionType": a.action_type,
        "actionName": a.action_name,
        "beforeStatus": a.before_status,
        "afterStatus": a.after_status,
        "opinion": a.opinion,
        "operatorType": a.operator_type,
        "operatorId": a.operator_id,
        "operatorName": a.operator_name,
        "operatorDeptId": a.operator_dept_id,
        "operatorDeptName": a.operator_dept_name,
        "createdAt": a.created_at.isoformat() if a.created_at else None,
    }


class GovMeetingService:

    def __init__(self, db: Session):
        self.db = db
        self.repo = GovMeetingRepository(db)
        self.ent_repo = EnterpriseRepository(db)

    def _build_detail(self, apply: GovMeetingApply) -> dict:
        result = _apply_to_dict(apply)
        # arrangement
        arr = self.repo.get_arrangement_by_apply(apply.id)
        if arr:
            participants = self.repo.get_participants(arr.id)
            result["arrangement"] = _arrangement_to_dict(arr, participants)
        else:
            result["arrangement"] = None
        # audit trail
        result["auditTrail"] = [_audit_to_dict(a) for a in self.repo.get_audits(apply.id)]
        # records
        result["records"] = [_record_to_dict(r) for r in self.repo.get_records(apply.id)]
        # attachments
        atts = self.repo.get_attachments(apply.id)
        result["attachments"] = [
            {"id": a.id, "originalName": a.original_name, "fileExt": a.file_ext,
             "fileSize": a.file_size, "storagePath": a.storage_path}
            for a in atts
        ]
        # evaluation
        eva = self.repo.get_evaluation(apply.id)
        if eva:
            result["evaluation"] = {
                "id": eva.id,
                "satisfaction": eva.satisfaction,
                "score": eva.score,
                "resolvedFlag": eva.resolved_flag,
                "comment": eva.comment,
                "createdAt": eva.created_at.isoformat() if eva.created_at else None,
            }
        else:
            result["evaluation"] = None
        return result

    # ── Enterprise actions ────────────────────────────────────────────────────

    def submit_apply(self, enterprise_id: int, data: dict) -> dict:
        if data.get("commitmentChecked") != 1:
            raise ParamException("请勾选承诺声明")

        enterprise = self.ent_repo.get_by_id(enterprise_id)
        if enterprise is None:
            raise NotFoundException("企业信息不存在")

        # content/description: new form uses 'content' field mapped to meeting_content;
        # description falls back to content for backward compat
        meeting_content = data.get("content") or data.get("description") or ""
        description_val = data.get("description") or data.get("content") or ""

        apply = self.repo.create_apply(
            apply_no=generate_apply_no(self.db),
            enterprise_id=enterprise.id,
            enterprise_name=enterprise.enterprise_name,
            credit_code=enterprise.credit_code,
            contact_name=data["contactName"],
            contact_phone=data["contactPhone"],
            topic_code=data.get("topicCode"),
            topic_name=data.get("topicName"),
            meeting_level=data.get("meetingLevel") or data.get("expectedLevelCode"),
            expected_level_code=data.get("expectedLevelCode"),
            expected_level_name=data.get("expectedLevelName"),
            title=data.get("title"),
            meeting_content=meeting_content,
            discussion_item=data.get("discussionItem"),
            urgency_level=data.get("urgencyLevel"),
            industry_code=data.get("industryCode"),
            industry_name=data.get("industryName"),
            registered_address=data.get("registeredAddress"),
            description=description_val,
            commitment_checked=1,
            region_code=data.get("regionCode") or enterprise.region_code or "",
            region_name=data.get("regionName") or enterprise.region_name or "",
            service_center_id=data.get("serviceCenterId"),
            service_center_name=data.get("serviceCenterName"),
            status=GovMeetingStatus.PENDING_AUDIT,
            submitted_at=datetime.utcnow(),
        )

        if data.get("attachmentIds"):
            self.repo.bind_attachments(apply.id, data["attachmentIds"])

        self.repo.add_audit(
            apply_id=apply.id,
            action_type=GovMeetingAction.SUBMIT,
            action_name=ACTION_NAMES[GovMeetingAction.SUBMIT],
            before_status=None,
            after_status=GovMeetingStatus.PENDING_AUDIT,
            operator_type="ENTERPRISE",
            operator_id=str(enterprise.id),
            operator_name=enterprise.enterprise_name,
        )

        self.repo.add_operation_log(
            operator_type="ENTERPRISE", operator_id=str(enterprise.id),
            operator_name=enterprise.enterprise_name,
            operation_type=GovMeetingAction.SUBMIT, business_id=apply.id,
            operation_content="企业提交政企约见申请",
            after_status=GovMeetingStatus.PENDING_AUDIT,
        )

        self.db.commit()
        return _apply_to_dict(apply)

    def modify_apply(self, enterprise_id: int, apply_id: int, data: dict) -> dict:
        apply = self.repo.get_apply_by_id_and_enterprise(apply_id, enterprise_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.MODIFY)

        update_fields = {}
        for field, key in [
            ("contact_name", "contactName"), ("contact_phone", "contactPhone"),
            ("topic_code", "topicCode"), ("topic_name", "topicName"),
            ("meeting_level", "meetingLevel"), ("description", "description"),
        ]:
            if data.get(key) is not None:
                update_fields[field] = data[key]

        if update_fields:
            self.repo.update_apply(apply, **update_fields)

        if data.get("attachmentIds"):
            self.repo.bind_attachments(apply.id, data["attachmentIds"])

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.MODIFY,
            action_name=ACTION_NAMES[GovMeetingAction.MODIFY],
            before_status=apply.status, after_status=apply.status,
            operator_type="ENTERPRISE", operator_id=str(enterprise_id),
            operator_name=apply.enterprise_name,
        )

        self.db.commit()
        return _apply_to_dict(apply)

    def supplement_apply(self, enterprise_id: int, apply_id: int, data: dict) -> dict:
        apply = self.repo.get_apply_by_id_and_enterprise(apply_id, enterprise_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.SUPPLEMENT)

        before = apply.status
        update = {"status": GovMeetingStatus.PENDING_AUDIT}
        supplement_content = data.get("content") or data.get("description")
        if supplement_content:
            update["description"] = supplement_content
            update["meeting_content"] = supplement_content
        self.repo.update_apply(apply, **update)

        if data.get("attachmentIds"):
            self.repo.bind_attachments(apply.id, data["attachmentIds"])

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.SUPPLEMENT,
            action_name=ACTION_NAMES[GovMeetingAction.SUPPLEMENT],
            before_status=before, after_status=GovMeetingStatus.PENDING_AUDIT,
            operator_type="ENTERPRISE", operator_id=str(enterprise_id),
            operator_name=apply.enterprise_name,
        )

        self.db.commit()
        return _apply_to_dict(apply)

    def list_applies_enterprise(self, enterprise_id: int, data: dict) -> tuple:
        total, records = self.repo.list_applies_enterprise(
            enterprise_id=enterprise_id,
            status=data.get("status"),
            page_no=data.get("pageNo", 1),
            page_size=data.get("pageSize", 10),
        )
        return total, [_apply_to_dict(r) for r in records]

    def get_apply_detail_enterprise(self, enterprise_id: int, apply_id: int) -> dict:
        apply = self.repo.get_apply_by_id_and_enterprise(apply_id, enterprise_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        return self._build_detail(apply)

    def evaluate_apply(self, enterprise_id: int, apply_id: int, data: dict) -> dict:
        apply = self.repo.get_apply_by_id_and_enterprise(apply_id, enterprise_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.EVALUATE)

        existing = self.repo.get_evaluation(apply.id)
        if existing:
            raise ParamException("该申请已评价")

        self.repo.create_evaluation(
            business_type="GOV_MEETING",
            business_id=apply.id,
            enterprise_id=enterprise_id,
            satisfaction=data["satisfaction"],
            score=data["score"],
            resolved_flag=data.get("resolvedFlag"),
            comment=data.get("comment"),
            evaluate_time=datetime.utcnow(),
        )

        before = apply.status
        self.repo.update_apply(apply, status=GovMeetingStatus.EVALUATED, evaluated_at=datetime.utcnow())

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.EVALUATE,
            action_name=ACTION_NAMES[GovMeetingAction.EVALUATE],
            before_status=before, after_status=GovMeetingStatus.EVALUATED,
            operator_type="ENTERPRISE", operator_id=str(enterprise_id),
            operator_name=apply.enterprise_name,
        )

        self.db.commit()
        return _apply_to_dict(apply)

    # ── Admin actions ─────────────────────────────────────────────────────────

    def list_applies_admin(self, data: dict, data_scope: str, current_region_code: str) -> tuple:
        total, records = self.repo.list_applies_admin(
            enterprise_name=data.get("enterpriseName"),
            credit_code=data.get("creditCode"),
            status=data.get("status"),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
            region_code_filter=data.get("regionCode"),
            service_center_id=data.get("serviceCenterId"),
            page_no=data.get("pageNo", 1),
            page_size=data.get("pageSize", 10),
            data_scope=data_scope,
            current_region_code=current_region_code,
        )
        return total, [_apply_to_dict(r) for r in records]

    def get_apply_detail_admin(self, apply_id: int) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        return self._build_detail(apply)

    def audit_apply(self, apply_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")

        audit_type = data.get("auditType")
        if audit_type == "ACCEPT":
            _check_status(apply, GovMeetingAction.ACCEPT)
            before = apply.status
            accept_fields = {
                "status": GovMeetingStatus.PENDING_ARRANGE,
                "accepted_at": datetime.utcnow(),
            }
            if data.get("finalLevelCode"):
                accept_fields["final_level_code"] = data["finalLevelCode"]
                accept_fields["final_level_name"] = data.get("finalLevelName") or data["finalLevelCode"]
            self.repo.update_apply(apply, **accept_fields)
            self.repo.add_audit(
                apply_id=apply.id, action_type=GovMeetingAction.ACCEPT,
                action_name=ACTION_NAMES[GovMeetingAction.ACCEPT],
                before_status=before, after_status=GovMeetingStatus.PENDING_ARRANGE,
                operator_type=op["operator_type"], operator_id=op["operator_id"],
                operator_name=op["operator_name"],
                opinion=data.get("opinion"),
                operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
                operator_dept_name=op.get("department_name"),
            )

        elif audit_type == "RETURN_SUPPLEMENT":
            _check_status(apply, GovMeetingAction.RETURN_SUPPLEMENT)
            before = apply.status
            self.repo.update_apply(apply, status=GovMeetingStatus.NEED_SUPPLEMENT)
            self.repo.add_audit(
                apply_id=apply.id, action_type=GovMeetingAction.RETURN_SUPPLEMENT,
                action_name=ACTION_NAMES[GovMeetingAction.RETURN_SUPPLEMENT],
                before_status=before, after_status=GovMeetingStatus.NEED_SUPPLEMENT,
                operator_type=op["operator_type"], operator_id=op["operator_id"],
                operator_name=op["operator_name"],
                opinion=data.get("opinion"),
                operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
                operator_dept_name=op.get("department_name"),
            )

        elif audit_type == "REJECT":
            _check_status(apply, GovMeetingAction.REJECT)
            before = apply.status
            self.repo.update_apply(apply,
                status=GovMeetingStatus.REJECTED,
                reject_reason_code=data.get("rejectReasonCode"),
                reject_reason_name=data.get("rejectReasonName"),
                reject_opinion=data.get("opinion"))
            self.repo.add_audit(
                apply_id=apply.id, action_type=GovMeetingAction.REJECT,
                action_name=ACTION_NAMES[GovMeetingAction.REJECT],
                before_status=before, after_status=GovMeetingStatus.REJECTED,
                operator_type=op["operator_type"], operator_id=op["operator_id"],
                operator_name=op["operator_name"],
                opinion=data.get("opinion"),
                operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
                operator_dept_name=op.get("department_name"),
            )

        else:
            raise ParamException(f"无效的审核类型: {audit_type}")

        self.repo.add_operation_log(
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            operation_type=f"AUDIT_{audit_type}", business_id=apply.id,
            after_status=apply.status,
        )

        self.db.commit()
        return _apply_to_dict(apply)

    def arrange_apply(self, apply_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.ARRANGE)

        arr = self.repo.create_arrangement(
            apply_id=apply_id,
            meeting_date=data.get("meetingDate"),
            meeting_place=data.get("meetingPlace"),
            meeting_method=data.get("meetingMethod"),
            start_time=data.get("startTime"),
            end_time=data.get("endTime"),
            host_dept_id=data.get("hostDeptId"),
            host_dept_name=data.get("hostDeptName"),
            notes=data.get("notes"),
            gov_contact_name=data.get("govContactName"),
            gov_contact_phone=data.get("govContactPhone"),
            remark=data.get("remark"),
            confirmed_flag=0,
        )

        if data.get("participants"):
            self.repo.replace_participants(arr.id, apply_id, data["participants"])

        before = apply.status
        self.repo.update_apply(apply,
            status=GovMeetingStatus.ARRANGED,
            arranged_at=datetime.utcnow())

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.ARRANGE,
            action_name=ACTION_NAMES[GovMeetingAction.ARRANGE],
            before_status=before, after_status=GovMeetingStatus.ARRANGED,
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
            operator_dept_name=op.get("department_name"),
        )

        self.db.commit()
        participants = self.repo.get_participants(arr.id)
        return _arrangement_to_dict(arr, participants)

    def update_arrangement(self, apply_id: int, arr_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.UPDATE_ARRANGEMENT)

        arr = self.repo.get_arrangement_by_id(arr_id)
        if arr is None or arr.apply_id != apply_id:
            raise NotFoundException("安排记录不存在")

        update_fields = {}
        for field, key in [
            ("meeting_date", "meetingDate"), ("meeting_place", "meetingPlace"),
            ("meeting_method", "meetingMethod"), ("gov_contact_name", "govContactName"),
            ("gov_contact_phone", "govContactPhone"), ("remark", "remark"),
            ("start_time", "startTime"), ("end_time", "endTime"),
            ("host_dept_id", "hostDeptId"), ("host_dept_name", "hostDeptName"),
            ("notes", "notes"),
        ]:
            if data.get(key) is not None:
                update_fields[field] = data[key]

        if update_fields:
            self.repo.update_arrangement(arr, **update_fields)

        if data.get("participants") is not None:
            self.repo.replace_participants(arr.id, apply_id, data["participants"])

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.UPDATE_ARRANGEMENT,
            action_name=ACTION_NAMES[GovMeetingAction.UPDATE_ARRANGEMENT],
            before_status=apply.status, after_status=apply.status,
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
            operator_dept_name=op.get("department_name"),
        )

        self.db.commit()
        participants = self.repo.get_participants(arr.id)
        return _arrangement_to_dict(arr, participants)

    def confirm_apply(self, apply_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.CONFIRM)

        arr = self.repo.get_arrangement_by_apply(apply_id)
        if arr:
            self.repo.update_arrangement(arr, confirmed_flag=1)

        before = apply.status
        self.repo.update_apply(apply, status=GovMeetingStatus.WAIT_MEETING)

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.CONFIRM,
            action_name=ACTION_NAMES[GovMeetingAction.CONFIRM],
            before_status=before, after_status=GovMeetingStatus.WAIT_MEETING,
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            opinion=data.get("opinion"),
            operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
            operator_dept_name=op.get("department_name"),
        )

        self.db.commit()
        return _apply_to_dict(apply)

    def complete_apply(self, apply_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.COMPLETE)

        before = apply.status
        self.repo.update_apply(apply,
            status=GovMeetingStatus.MEETING_COMPLETED,
            meeting_at=data.get("meetingAt") or datetime.utcnow(),
            completed_at=datetime.utcnow())

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.COMPLETE,
            action_name=ACTION_NAMES[GovMeetingAction.COMPLETE],
            before_status=before, after_status=GovMeetingStatus.MEETING_COMPLETED,
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            opinion=data.get("opinion"),
            operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
            operator_dept_name=op.get("department_name"),
        )

        self.db.commit()
        return _apply_to_dict(apply)

    def add_record(self, apply_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.ADD_RECORD)

        rec = self.repo.create_record(
            apply_id=apply_id,
            arrangement_id=data.get("arrangementId"),
            content=data["content"],
            conclusions=data.get("conclusions"),
            follow_up_items=data.get("followUpItems"),
            recorder_id=op["operator_id"],
            recorder_name=op["operator_name"],
            record_time=data.get("recordTime") or datetime.utcnow(),
        )

        before_status = apply.status
        after_status = apply.status
        if apply.status == GovMeetingStatus.MEETING_COMPLETED:
            after_status = GovMeetingStatus.PENDING_EVALUATION
            self.repo.update_apply(apply, status=after_status)

        self.repo.add_audit(
            apply_id=apply.id, action_type=GovMeetingAction.ADD_RECORD,
            action_name=ACTION_NAMES[GovMeetingAction.ADD_RECORD],
            before_status=before_status, after_status=after_status,
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
            operator_dept_name=op.get("department_name"),
        )

        self.db.commit()
        return _record_to_dict(rec)

    def finish_apply(self, apply_id: int, data: dict, op: dict) -> dict:
        apply = self.repo.get_apply_by_id(apply_id)
        if apply is None:
            raise NotFoundException("申请不存在")
        _check_status(apply, GovMeetingAction.FINISH)

        send_evaluation = data.get("sendEvaluation", 1)
        before = apply.status

        if send_evaluation == 1 and apply.status == GovMeetingStatus.MEETING_COMPLETED:
            after_status = GovMeetingStatus.PENDING_EVALUATION
            action_type = GovMeetingAction.NOTIFY_EVALUATION
            action_name = ACTION_NAMES[GovMeetingAction.NOTIFY_EVALUATION]
        else:
            after_status = GovMeetingStatus.COMPLETED
            action_type = GovMeetingAction.FINISH
            action_name = ACTION_NAMES[GovMeetingAction.FINISH]

        update = {"status": after_status}
        if after_status == GovMeetingStatus.COMPLETED:
            update["finished_at"] = datetime.utcnow()

        self.repo.update_apply(apply, **update)

        self.repo.add_audit(
            apply_id=apply.id, action_type=action_type, action_name=action_name,
            before_status=before, after_status=after_status,
            operator_type=op["operator_type"], operator_id=op["operator_id"],
            operator_name=op["operator_name"],
            opinion=data.get("opinion"),
            operator_dept_id=str(op["department_id"]) if op.get("department_id") else None,
            operator_dept_name=op.get("department_name"),
        )

        self.db.commit()
        return _apply_to_dict(apply)
