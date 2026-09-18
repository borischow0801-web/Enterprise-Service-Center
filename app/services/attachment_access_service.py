"""
Attachment access control.

Two categories of SysAttachment row exist in this system:

1. Bound to a specific business record (business_type in APPEAL / MEETING_ROOM_BOOKING /
   GOV_MEETING) — access is checked against that record's ownership (enterprise side) or
   data scope + role permission (admin side), reusing the exact same repositories and
   DataPermissionService the business modules themselves use. No separate, drift-prone
   attachment-only permission logic.

2. "TEMP" — either (a) a freshly uploaded file not yet bound to any business record (private
   to its uploader until bound), or (b) a permanently-TEMP reference asset that was never meant
   to belong to a single owner: meeting room cover/gallery images and material-rule template
   files, referenced only via a foreign attachment_id column (MeetingRoomImage,
   MeetingRoom.cover_attachment_id, MeetingRoomMaterialRule.template_attachment_id). Those are
   legitimately public reference material — any authenticated caller needs to see them while
   just browsing rooms, before any booking exists — so they get their own rule: readable by any
   authenticated (not anonymous) caller.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.constants.permission import Permission, has_any_permission
from app.core.exceptions import ForbiddenException
from app.core.permission import DataPermissionService
from app.models.meeting_room import MeetingRoom, MeetingRoomImage, MeetingRoomMaterialRule
from app.models.system import SysAttachment
from app.repositories.appeal_repo import AppealRepository
from app.repositories.gov_meeting_repo import GovMeetingRepository
from app.repositories.meeting_room_repo import MeetingRoomRepository

BUSINESS_TYPE_APPEAL = "APPEAL"
BUSINESS_TYPE_MEETING_ROOM_BOOKING = "MEETING_ROOM_BOOKING"
BUSINESS_TYPE_GOV_MEETING = "GOV_MEETING"
BUSINESS_TYPE_TEMP = "TEMP"

_DENIED = ForbiddenException("无权访问该附件")


def is_public_reference_asset(db: Session, attachment_id: int) -> bool:
    if db.query(MeetingRoomImage.id).filter(MeetingRoomImage.attachment_id == attachment_id).first():
        return True
    if db.query(MeetingRoom.id).filter(MeetingRoom.cover_attachment_id == attachment_id).first():
        return True
    if db.query(MeetingRoomMaterialRule.id).filter(
        MeetingRoomMaterialRule.template_attachment_id == attachment_id
    ).first():
        return True
    return False


def _assert_enterprise_can_access(db: Session, attachment: SysAttachment, enterprise_id: int) -> None:
    if attachment.business_type == BUSINESS_TYPE_APPEAL:
        record = AppealRepository(db).get_by_id_and_enterprise(attachment.business_id, enterprise_id)
    elif attachment.business_type == BUSINESS_TYPE_MEETING_ROOM_BOOKING:
        record = MeetingRoomRepository(db).get_booking_by_id_and_enterprise(attachment.business_id, enterprise_id)
    elif attachment.business_type == BUSINESS_TYPE_GOV_MEETING:
        record = GovMeetingRepository(db).get_apply_by_id_and_enterprise(attachment.business_id, enterprise_id)
    else:
        record = None
    if record is None:
        raise _DENIED


def _assert_admin_can_access(db: Session, attachment: SysAttachment, operator: dict) -> None:
    role_codes = operator.get("role_codes")

    if attachment.business_type == BUSINESS_TYPE_APPEAL:
        appeal_repo = AppealRepository(db)
        appeal = appeal_repo.get_by_id(attachment.business_id)
        if appeal is None:
            raise _DENIED
        if not has_any_permission(
            role_codes, [Permission.APPEAL_VIEW, Permission.APPEAL_HANDLE, Permission.APPEAL_DEPT_REPLY]
        ):
            raise ForbiddenException("当前角色无权查看诉求附件")
        assignments = appeal_repo.get_assignments(appeal.id)
        dept_ids = {appeal.responsible_dept_id} | {a.assigned_dept_id for a in assignments}
        DataPermissionService.assert_can_access(operator, region_code=appeal.region_code, dept_ids=dept_ids)
        return

    if attachment.business_type == BUSINESS_TYPE_MEETING_ROOM_BOOKING:
        booking = MeetingRoomRepository(db).get_booking_by_id(attachment.business_id)
        if booking is None:
            raise _DENIED
        if not has_any_permission(role_codes, [Permission.MEETING_ROOM_VIEW, Permission.MEETING_BOOKING_HANDLE]):
            raise ForbiddenException("当前角色无权查看会议室预约附件")
        DataPermissionService.assert_can_access(operator, region_code=booking.region_code)
        return

    if attachment.business_type == BUSINESS_TYPE_GOV_MEETING:
        apply_ = GovMeetingRepository(db).get_apply_by_id(attachment.business_id)
        if apply_ is None:
            raise _DENIED
        if not has_any_permission(role_codes, [Permission.GOV_MEETING_VIEW, Permission.GOV_MEETING_HANDLE]):
            raise ForbiddenException("当前角色无权查看政企约见附件")
        DataPermissionService.assert_can_access(operator, region_code=apply_.region_code)
        return

    raise _DENIED


def assert_attachment_accessible(db: Session, attachment: SysAttachment, payload: dict[str, Any]) -> None:
    """Entry point used by the shared download route. `payload` is the decoded JWT
    (enterprise or admin) of the authenticated caller — anonymous callers never reach here
    because the route itself requires a valid token first."""
    token_type = payload.get("token_type")

    if attachment.business_type == BUSINESS_TYPE_TEMP:
        if is_public_reference_asset(db, attachment.id):
            return
        caller_type = "ENTERPRISE" if token_type == "enterprise" else "USER"
        caller_id = str(payload.get("enterprise_id") or payload.get("user_id") or "")
        if attachment.uploaded_by_type == caller_type and attachment.uploaded_by_id == caller_id:
            return
        raise _DENIED

    if token_type == "enterprise":
        _assert_enterprise_can_access(db, attachment, payload.get("enterprise_id"))
        return

    if token_type == "admin":
        _assert_admin_can_access(db, attachment, payload)
        return

    raise _DENIED
