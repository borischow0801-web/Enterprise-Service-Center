"""
Meeting Room Service — all business logic.
"""
from datetime import datetime, timedelta, date
from typing import Optional, Any
from sqlalchemy.orm import Session

from app.constants.meeting_room import (
    BookingStatus, RoomStatus, AuditAction, AUDIT_ACTION_NAMES,
    ALLOWED_STATUS_FOR_ACTION, NO_SHOW_DISABLE_THRESHOLD,
    MIN_ADVANCE_DAYS, MIN_DURATION_MINUTES, MAX_DURATION_HOURS, MIN_CANCEL_HOURS,
)
from app.core.exceptions import (
    StatusNotAllowedException, NotFoundException, AppException,
    MeetingRoomConflictException, EnterpriseRestrictedException, ParamException, ErrorCode,
)
from app.repositories.meeting_room_repo import MeetingRoomRepository, generate_booking_no
from app.repositories.enterprise_repo import EnterpriseRepository
from app.models.meeting_room import MeetingRoom, MeetingRoomBooking
from app.models.system import SysAttachment


def _parse_datetime(val) -> datetime:
    """兼容 YYYY-MM-DD HH:mm:ss 与 ISO 格式。"""
    if isinstance(val, datetime):
        return val
    if not isinstance(val, str):
        raise ParamException("时间格式无效")
    s = val.strip()
    try:
        return datetime.fromisoformat(s.replace(" ", "T", 1))
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
    raise ParamException("时间格式无效，请使用 YYYY-MM-DD HH:mm:ss")


def _material_rule_to_dict(r) -> dict:
    return {
        "id": r.id,
        "roomId": r.room_id,
        "regionCode": r.region_code,
        "regionName": r.region_name,
        "serviceCenterId": r.service_center_id,
        "serviceCenterName": r.service_center_name,
        "enterpriseType": r.enterprise_type,
        "materialName": r.material_name,
        "materialCode": r.material_code,
        "requiredFlag": r.required_flag,
        "templateAttachmentId": r.template_attachment_id,
        "description": r.description,
        "enabled": r.enabled,
        "sortNo": r.sort_no if hasattr(r, 'sort_no') else 0,
    }


def _attachment_url(att_id: int) -> str:
    return f"/api/common/attachments/{att_id}/download"


def _room_to_dict(room: MeetingRoom) -> dict:
    return {
        "id": room.id,
        "roomName": room.room_name,
        "roomType": room.room_type,
        "regionCode": room.region_code,
        "regionName": room.region_name,
        "serviceCenterId": room.service_center_id,
        "serviceCenterName": room.service_center_name,
        "address": room.address,
        "capacity": room.capacity,
        "facilities": room.facilities.split(",") if room.facilities else [],
        "description": room.description,
        "coverAttachmentId": room.cover_attachment_id,
        "bookingNotice": room.booking_notice,
        "status": room.status,
        "createdAt": room.created_at.isoformat() if room.created_at else None,
    }


def _booking_to_dict(b: MeetingRoomBooking) -> dict:
    return {
        "id": b.id,
        "bookingNo": b.booking_no,
        "roomId": b.room_id,
        "roomName": b.room_name,
        "enterpriseId": b.enterprise_id,
        "enterpriseName": b.enterprise_name,
        "creditCode": b.credit_code,
        "enterpriseType": getattr(b, "enterprise_type", None),
        "enterpriseTypeName": getattr(b, "enterprise_type_name", None),
        "regionCode": b.region_code,
        "regionName": b.region_name,
        "serviceCenterId": b.service_center_id,
        "meetingSubject": b.meeting_subject,
        "participantCount": b.participant_count,
        "contactName": b.contact_name,
        "contactPhone": b.contact_phone,
        "startTime": b.start_time.isoformat() if b.start_time else None,
        "endTime": b.end_time.isoformat() if b.end_time else None,
        "supportItems": b.support_items.split(",") if b.support_items else [],
        "status": b.status,
        "cancelReason": b.cancel_reason,
        "canceledAt": b.canceled_at.isoformat() if b.canceled_at else None,
        "submittedAt": b.submitted_at.isoformat() if b.submitted_at else None,
        "approvedAt": b.approved_at.isoformat() if b.approved_at else None,
        "completedAt": b.completed_at.isoformat() if b.completed_at else None,
        "createdAt": b.created_at.isoformat() if b.created_at else None,
    }


class MeetingRoomService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MeetingRoomRepository(db)
        self.ent_repo = EnterpriseRepository(db)

    def _enrich_room_media(self, room: MeetingRoom) -> dict:
        d = _room_to_dict(room)
        images_db = self.repo.get_room_images(room.id)
        if images_db:
            d["images"] = [
                {
                    "attachmentId": img.attachment_id,
                    "url": _attachment_url(img.attachment_id),
                    "isCover": img.is_cover,
                    "sortNo": img.sort_no,
                }
                for img in images_db
            ]
            cover_img = next((i for i in images_db if i.is_cover), images_db[0])
            d["coverAttachmentId"] = cover_img.attachment_id
            d["coverImageUrl"] = _attachment_url(cover_img.attachment_id)
        elif room.cover_attachment_id:
            url = _attachment_url(room.cover_attachment_id)
            d["coverImageUrl"] = url
            d["images"] = [{
                "attachmentId": room.cover_attachment_id,
                "url": url,
                "isCover": 1,
                "sortNo": 0,
            }]
        else:
            d["coverImageUrl"] = None
            d["images"] = []
        return d

    def _sync_room_images(self, room_id: int, data: dict) -> None:
        image_ids = data.get("imageAttachmentIds")
        if image_ids is None:
            return
        cover_id = data.get("coverAttachmentId")
        self.repo.replace_room_images(room_id, image_ids, cover_id)
        room = self.repo.get_room_by_id(room_id)
        if room and image_ids:
            final_cover = cover_id if cover_id in image_ids else image_ids[0]
            self.repo.update_room(room, cover_attachment_id=final_cover)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _check_status(self, booking: MeetingRoomBooking, action: str) -> None:
        allowed = ALLOWED_STATUS_FOR_ACTION.get(action, [])
        if booking.status not in allowed:
            raise StatusNotAllowedException(
                f"当前预约状态【{booking.status}】不允许执行【{AUDIT_ACTION_NAMES.get(action, action)}】操作"
            )

    def _check_booking_conflict(self, room_id: int, start: datetime, end: datetime, exclude_id: Optional[int] = None) -> None:
        conflicts = self.repo.get_conflicting_bookings(room_id, start, end, exclude_id)
        if conflicts:
            raise MeetingRoomConflictException("预约时间段与已有预约冲突")

    def _check_occupy_conflict(self, room_id: int, start: datetime, end: datetime, exclude_id: Optional[int] = None) -> None:
        conflicts = self.repo.get_occupies_in_range(room_id, start, end, exclude_id)
        if conflicts:
            raise MeetingRoomConflictException("预约时间段与手工占用冲突")

    def _check_room_open(self, room: MeetingRoom, start: datetime, end: datetime) -> None:
        now = datetime.utcnow()

        # At least MIN_ADVANCE_DAYS days ahead
        if start < now + timedelta(days=MIN_ADVANCE_DAYS):
            raise ParamException(f"预约必须至少提前 {MIN_ADVANCE_DAYS} 天")

        # Duration checks
        duration_minutes = (end - start).total_seconds() / 60
        if duration_minutes < MIN_DURATION_MINUTES:
            raise ParamException(f"预约时长不能少于 {MIN_DURATION_MINUTES} 分钟")
        if duration_minutes > MAX_DURATION_HOURS * 60:
            raise ParamException(f"单次预约不能超过 {MAX_DURATION_HOURS} 小时")
        if end <= start:
            raise ParamException("结束时间必须晚于开始时间")

        # Check each date in range
        current = start.date()
        end_date = end.date()
        while current <= end_date:
            special = self.repo.get_special_date_for_date(room.region_code, room.service_center_id, current)
            if special:
                if special.open_flag == 0:
                    raise ParamException(f"{current} 为特殊关闭日期（{special.reason or special.date_type}），不可预约")
            else:
                # Default: Saturday=6, Sunday=7 (isoweekday: Mon=1...Sun=7)
                if current.isoweekday() >= 6:
                    raise ParamException(f"{current} 为周末，不可预约")

                # Check open rules
                rules = self.repo.get_open_rules(room.id)
                rule_map = {r.weekday: r for r in rules}
                wd = current.isoweekday()
                if wd in rule_map:
                    rule = rule_map[wd]
                    if not rule.open_flag:
                        raise ParamException(f"会议室周{wd}不开放")
                    # Check time within open hours
                    if current == start.date() and rule.start_time:
                        open_start = datetime.strptime(f"{current} {rule.start_time}", "%Y-%m-%d %H:%M")
                        open_end = datetime.strptime(f"{current} {rule.end_time}", "%Y-%m-%d %H:%M")
                        if start < open_start or end > open_end:
                            raise ParamException(f"预约时间不在会议室开放时间（{rule.start_time}-{rule.end_time}）内")
            current += timedelta(days=1)

    def _write_audit(self, booking_id: int, action: str, before: Optional[str], after: Optional[str],
                     operator: dict, opinion: Optional[str] = None) -> None:
        op_id = operator.get("operator_id", "")
        op_name = operator.get("operator_name", "")
        dept_id = operator.get("department_id")
        dept_name = operator.get("department_name")
        op_type = operator.get("operator_type", "USER")

        self.repo.add_audit(booking_id, action, before, after, op_id, op_name, opinion, dept_id, dept_name)
        self.repo.add_operation_log(
            operator_type=op_type, operator_id=op_id, operator_name=op_name,
            operation_type=action, business_id=booking_id,
            operation_content=opinion, before_status=before, after_status=after,
        )

    def _merge_material_rules_tiered(self, tiers: list[tuple[int, list]]) -> list:
        """多级匹配合并：优先级高的覆盖低的；同优先级下主体专属覆盖通用。"""
        by_code: dict = {}
        for priority in sorted({p for p, _ in tiers}, reverse=True):
            tier_rules = next(rules for p, rules in tiers if p == priority)
            tier_rules = sorted(
                tier_rules,
                key=lambda r: (0 if r.enterprise_type else 1, r.sort_no, r.id),
            )
            for r in tier_rules:
                by_code[r.material_code] = r
        return sorted(by_code.values(), key=lambda x: (x.sort_no, x.id))

    def get_applicable_material_rules(self, room_id: int, enterprise_type: Optional[str]) -> list:
        room = self.repo.get_room_by_id(room_id)
        if not room:
            return []
        return self._get_booking_material_rules(room, enterprise_type)

    def _get_booking_material_rules(self, room: MeetingRoom, enterprise_type: Optional[str]) -> list:
        tiers = self.repo.get_applicable_material_rules(
            room_id=room.id,
            region_code=room.region_code,
            service_center_id=room.service_center_id,
            enterprise_type=enterprise_type,
        )
        return self._merge_material_rules_tiered(tiers)

    def _build_booking_detail(self, booking: MeetingRoomBooking) -> dict:
        d = _booking_to_dict(booking)
        attachments = self.repo.get_attachments(booking.id)
        att_list = [
            {"id": a.id, "originalName": a.original_name, "fileExt": a.file_ext,
             "fileSize": a.file_size, "fileCategory": a.file_category,
             "createdAt": a.created_at.isoformat() if a.created_at else None,
             "downloadUrl": _attachment_url(a.id)}
            for a in attachments
        ]
        d["attachments"] = att_list
        att_by_cat: dict = {}
        for a in att_list:
            cat = a.get("fileCategory") or "OTHER"
            att_by_cat.setdefault(cat, []).append(a)

        room = self.repo.get_room_by_id(booking.room_id)
        rule_list = self._get_booking_material_rules(room, booking.enterprise_type) if room else []
        materials_out = []
        seen_codes = set()
        for r in rule_list:
            code = r.material_code
            seen_codes.add(code)
            materials_out.append({
                "materialCode": code,
                "materialName": r.material_name,
                "requiredFlag": r.required_flag,
                "description": r.description,
                "attachments": att_by_cat.get(code, []),
            })
        for code, atts in att_by_cat.items():
            if code not in seen_codes:
                materials_out.append({
                    "materialCode": code,
                    "materialName": code,
                    "requiredFlag": 0,
                    "attachments": atts,
                })
        d["materials"] = materials_out
        audits = self.repo.get_audits(booking.id)
        d["auditRecords"] = [
            {"id": a.id, "actionType": a.action_type,
             "actionName": AUDIT_ACTION_NAMES.get(a.action_type, a.action_type),
             "beforeStatus": a.before_status,
             "afterStatus": a.after_status, "auditOpinion": a.audit_opinion,
             "operatorName": a.operator_name, "operatorDeptName": a.operator_dept_name,
             "createdAt": a.created_at.isoformat() if a.created_at else None}
            for a in audits
        ]
        usage = self.repo.get_usage(booking.id)
        d["usageRecord"] = (
            {"id": usage.id, "usageStatus": usage.usage_status,
             "actualStartTime": usage.actual_start_time.isoformat() if usage.actual_start_time else None,
             "actualEndTime": usage.actual_end_time.isoformat() if usage.actual_end_time else None,
             "confirmUserName": usage.confirm_user_name,
             "confirmTime": usage.confirm_time.isoformat() if usage.confirm_time else None,
             "remark": usage.remark}
            if usage else None
        )
        return d

    # ── Enterprise: Room ──────────────────────────────────────────────────────

    def list_rooms_enterprise(self, region_code, capacity_min, facility, room_type, page_no, page_size):
        total, rooms = self.repo.list_rooms_enterprise(region_code, capacity_min, facility, room_type, page_no, page_size)
        return total, [self._enrich_room_media(r) for r in rooms]

    def get_room_detail_enterprise(self, room_id: int, admin: bool = False) -> dict:
        room = self.repo.get_room_by_id(room_id)
        if not room:
            raise NotFoundException("会议室不存在")
        if not admin and room.status == RoomStatus.DISABLED:
            raise NotFoundException("会议室不存在")
        d = self._enrich_room_media(room)
        d["openRules"] = [
            {"weekday": r.weekday, "openFlag": r.open_flag, "startTime": r.start_time, "endTime": r.end_time}
            for r in self.repo.get_open_rules(room_id)
        ]
        mat_rules = self._get_booking_material_rules(room, None)
        d["materialRules"] = [
            {"id": mr.id, "materialName": mr.material_name, "materialCode": mr.material_code,
             "requiredFlag": mr.required_flag, "description": mr.description,
             "templateAttachmentId": mr.template_attachment_id}
            for mr in mat_rules
        ]
        return d

    def get_room_calendar(self, room_id: int, start_date_str: str, end_date_str: str) -> dict:
        room = self.repo.get_room_by_id(room_id)
        if not room or room.status == RoomStatus.DISABLED:
            raise NotFoundException("会议室不存在")

        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

        approved_bookings = self.repo.get_conflicting_bookings(room_id, start_dt, end_dt)
        occupies = self.repo.get_occupies_in_range(room_id, start_dt, end_dt)
        special_dates = self.repo.get_special_dates(room.region_code, room.service_center_id, start_dt, end_dt)
        open_rules = self.repo.get_open_rules(room_id)

        return {
            "roomId": room_id,
            "startDate": start_date_str,
            "endDate": end_date_str,
            "bookedSlots": [
                {"bookingId": b.id, "startTime": b.start_time.isoformat(), "endTime": b.end_time.isoformat(), "status": b.status}
                for b in approved_bookings
            ],
            "occupiedSlots": [
                {"occupyId": o.id, "title": o.occupy_title, "startTime": o.start_time.isoformat(), "endTime": o.end_time.isoformat()}
                for o in occupies
            ],
            "specialDates": [
                {"date": str(s.special_date), "dateType": s.date_type, "openFlag": s.open_flag, "reason": s.reason}
                for s in special_dates
            ],
            "openRules": [
                {"weekday": r.weekday, "openFlag": r.open_flag, "startTime": r.start_time, "endTime": r.end_time}
                for r in open_rules
            ],
        }

    def get_material_rules_enterprise(self, room_id: int, enterprise_type: Optional[str]) -> list:
        room = self.repo.get_room_by_id(room_id)
        if not room:
            return []
        rules = self._get_booking_material_rules(room, enterprise_type)
        return [
            {"id": r.id, "materialName": r.material_name, "materialCode": r.material_code,
             "requiredFlag": r.required_flag, "description": r.description,
             "templateAttachmentId": r.template_attachment_id,
             "templateDownloadUrl": _attachment_url(r.template_attachment_id) if r.template_attachment_id else None,
             "sortNo": r.sort_no, "enterpriseType": r.enterprise_type}
            for r in rules
        ]

    # ── Enterprise: Booking ───────────────────────────────────────────────────

    def submit_booking(self, enterprise_id: int, data: dict) -> dict:
        enterprise = self.ent_repo.get_by_id(enterprise_id)
        if not enterprise:
            raise NotFoundException("企业信息不存在")
        if enterprise.meeting_booking_disabled:
            raise EnterpriseRestrictedException()

        room = self.repo.get_room_by_id(data["roomId"])
        if not room or room.status != RoomStatus.ENABLED:
            raise NotFoundException("会议室不存在或已停用")

        start_time = _parse_datetime(data["startTime"])
        end_time = _parse_datetime(data["endTime"])

        self._check_room_open(room, start_time, end_time)
        self._check_booking_conflict(room.id, start_time, end_time)
        self._check_occupy_conflict(room.id, start_time, end_time)

        enterprise_type = data.get("enterpriseType")
        if not enterprise_type:
            raise ParamException("请选择申请主体类型")
        enterprise_type_name = data.get("enterpriseTypeName")
        if not enterprise_type_name and enterprise_type:
            from app.models.system import SysDictionary
            dict_item = self.db.query(SysDictionary).filter(
                SysDictionary.dict_type == "ENTERPRISE_TYPE",
                SysDictionary.dict_code == enterprise_type,
                SysDictionary.deleted_flag == 0,
            ).first()
            if dict_item:
                enterprise_type_name = dict_item.dict_label

        merged_rules = self._get_booking_material_rules(room, enterprise_type)
        materials_payload = data.get("materials") or []
        material_map, all_attachment_ids = self._validate_required_materials(
            merged_rules,
            materials_payload,
            data.get("attachmentIds") or data.get("attachment_ids") or [],
        )

        support_items_str = ",".join(data.get("supportItems") or []) if data.get("supportItems") else None
        now = datetime.utcnow()
        booking = self.repo.create_booking(
            booking_no=generate_booking_no(self.db),
            room_id=room.id,
            room_name=room.room_name,
            enterprise_id=enterprise.id,
            enterprise_name=enterprise.enterprise_name,
            credit_code=enterprise.credit_code,
            region_code=room.region_code,
            region_name=room.region_name,
            service_center_id=room.service_center_id,
            meeting_subject=data["meetingSubject"],
            participant_count=data["participantCount"],
            contact_name=data["contactName"],
            contact_phone=data["contactPhone"],
            start_time=start_time,
            end_time=end_time,
            support_items=support_items_str,
            enterprise_type=enterprise_type,
            enterprise_type_name=enterprise_type_name,
            status=BookingStatus.PENDING_AUDIT,
            submitted_at=now,
        )

        if materials_payload:
            self.repo.bind_attachments_by_materials(booking.id, materials_payload)
        if all_attachment_ids:
            self.repo.bind_attachments(booking.id, all_attachment_ids)

        op = {"operator_type": "ENTERPRISE", "operator_id": str(enterprise.id),
              "operator_name": enterprise.enterprise_name}
        self._write_audit(booking.id, AuditAction.SUBMIT, None, BookingStatus.PENDING_AUDIT, op)
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)

    def list_bookings_enterprise(self, enterprise_id: int, status: Optional[str], page_no: int, page_size: int):
        total, records = self.repo.list_bookings_enterprise(enterprise_id, status, page_no, page_size)
        return total, [_booking_to_dict(b) for b in records]

    def get_booking_detail_enterprise(self, booking_id: int, enterprise_id: int) -> dict:
        booking = self.repo.get_booking_by_id_and_enterprise(booking_id, enterprise_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        return self._build_booking_detail(booking)

    def cancel_booking_enterprise(self, booking_id: int, enterprise_id: int, data: dict) -> dict:
        booking = self.repo.get_booking_by_id_and_enterprise(booking_id, enterprise_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.CANCEL)

        # If approved/wait_use, must cancel at least MIN_CANCEL_HOURS hours ahead
        if booking.status in [BookingStatus.APPROVED, BookingStatus.WAIT_USE]:
            min_cancel_time = booking.start_time - timedelta(hours=MIN_CANCEL_HOURS)
            if datetime.utcnow() > min_cancel_time:
                raise StatusNotAllowedException(f"审核通过后的预约至少需提前 {MIN_CANCEL_HOURS} 小时取消")

        enterprise = self.ent_repo.get_by_id(enterprise_id)
        old_status = booking.status
        now = datetime.utcnow()
        self.repo.update_booking(booking, status=BookingStatus.CANCELED,
                                 cancel_reason=data.get("cancelReason"), canceled_at=now)
        self.repo.create_usage(booking_id=booking.id, room_id=booking.room_id, usage_status="CANCELED",
                               confirm_time=now)
        op = {"operator_type": "ENTERPRISE", "operator_id": str(enterprise_id),
              "operator_name": enterprise.enterprise_name if enterprise else str(enterprise_id)}
        self._write_audit(booking.id, AuditAction.CANCEL, old_status, BookingStatus.CANCELED, op,
                          data.get("cancelReason"))
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)

    def _validate_required_materials(
        self,
        merged_rules: list,
        materials_payload: list,
        extra_attachment_ids: list,
        existing_attachments: Optional[list] = None,
    ) -> tuple[dict, list]:
        """校验必传材料，返回 material_map 与全部 attachment id 列表。"""
        material_map: dict = {}
        for m in materials_payload:
            code = m.get("materialCode") or m.get("material_code")
            if not code:
                continue
            ids = [i for i in (m.get("attachmentIds") or m.get("attachment_ids") or []) if i]
            if ids:
                material_map[code] = list(dict.fromkeys((material_map.get(code) or []) + ids))

        existing_by_cat: dict = {}
        for a in existing_attachments or []:
            cat = a.file_category or "OTHER"
            existing_by_cat.setdefault(cat, [])

        all_attachment_ids = list(extra_attachment_ids or [])
        for ids in material_map.values():
            all_attachment_ids.extend(ids)
        all_attachment_ids = list(dict.fromkeys(i for i in all_attachment_ids if i))

        required_rules = [r for r in merged_rules if r.required_flag]
        if required_rules:
            missing = []
            for r in required_rules:
                code = r.material_code
                has_new = bool(material_map.get(code))
                has_old = bool(existing_by_cat.get(code))
                if not has_new and not has_old:
                    missing.append(r.material_name)
            if missing:
                raise ParamException(f"请上传必传材料：{'、'.join(missing)}")
            elif not materials_payload and not all_attachment_ids and not existing_attachments:
                raise ParamException(
                    f"请上传必传材料：{'、'.join(r.material_name for r in required_rules)}"
                )

        if all_attachment_ids:
            found = self.db.query(SysAttachment.id).filter(
                SysAttachment.id.in_(all_attachment_ids),
                SysAttachment.deleted_flag == 0,
            ).all()
            found_ids = {row[0] for row in found}
            missing_ids = set(all_attachment_ids) - found_ids
            if missing_ids:
                raise ParamException("部分附件不存在或已失效，请重新上传")

        return material_map, all_attachment_ids

    def supplement_booking_enterprise(self, booking_id: int, enterprise_id: int, data: dict) -> dict:
        booking = self.repo.get_booking_by_id_and_enterprise(booking_id, enterprise_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.SUPPLEMENT)

        room = self.repo.get_room_by_id(booking.room_id)
        if not room:
            raise NotFoundException("会议室不存在")
        merged_rules = self._get_booking_material_rules(room, booking.enterprise_type)
        materials_payload = data.get("materials") or []
        existing_attachments = self.repo.get_attachments(booking.id)

        material_map, all_attachment_ids = self._validate_required_materials(
            merged_rules,
            materials_payload,
            data.get("attachmentIds") or data.get("attachment_ids") or [],
            existing_attachments=existing_attachments,
        )

        old_status = booking.status
        self.repo.update_booking(booking, status=BookingStatus.PENDING_AUDIT)

        if materials_payload:
            self.repo.bind_attachments_by_materials(booking.id, materials_payload)
        elif material_map:
            items = [{"materialCode": k, "attachmentIds": v} for k, v in material_map.items()]
            self.repo.bind_attachments_by_materials(booking.id, items)
        if all_attachment_ids:
            self.repo.bind_attachments(booking.id, all_attachment_ids)

        enterprise = self.ent_repo.get_by_id(enterprise_id)
        remark = data.get("remark") or "企业已补充材料"
        op = {"operator_type": "ENTERPRISE", "operator_id": str(enterprise_id),
              "operator_name": enterprise.enterprise_name if enterprise else str(enterprise_id)}
        self._write_audit(
            booking.id, AuditAction.SUPPLEMENT, old_status, BookingStatus.PENDING_AUDIT, op, remark,
        )
        self.db.commit()
        self.db.refresh(booking)
        return self._build_booking_detail(booking)

    # ── Admin: Room ───────────────────────────────────────────────────────────

    def list_rooms_admin(self, query: dict, data_scope: str, current_region_code: str):
        total, rooms = self.repo.list_rooms_admin(
            region_code=query.get("regionCode"),
            service_center_id=query.get("serviceCenterId"),
            status=query.get("status"),
            room_type=query.get("roomType"),
            page_no=query.get("pageNo", 1),
            page_size=query.get("pageSize", 10),
            data_scope=data_scope,
            current_region_code=current_region_code,
        )
        return total, [self._enrich_room_media(r) for r in rooms]

    def create_room(self, data: dict, operator: dict) -> dict:
        facilities_str = ",".join(data.get("facilities") or []) if data.get("facilities") else None
        room = self.repo.create_room(
            room_name=data["roomName"],
            room_type=data.get("roomType"),
            region_code=data["regionCode"],
            region_name=data["regionName"],
            service_center_id=data.get("serviceCenterId"),
            service_center_name=data.get("serviceCenterName"),
            address=data.get("address"),
            capacity=data["capacity"],
            facilities=facilities_str,
            description=data.get("description"),
            cover_attachment_id=data.get("coverAttachmentId"),
            booking_notice=data.get("bookingNotice"),
            status=RoomStatus.ENABLED,
        )
        self._sync_room_images(room.id, data)
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="CREATE_ROOM",
            business_id=room.id,
            operation_content=f"新增会议室：{room.room_name}",
        )
        self.db.commit()
        self.db.refresh(room)
        return self._enrich_room_media(room)

    def update_room(self, room_id: int, data: dict, operator: dict) -> dict:
        room = self.repo.get_room_by_id(room_id)
        if not room:
            raise NotFoundException("会议室不存在")
        update_fields = {k: v for k, v in {
            "room_name": data.get("roomName"),
            "room_type": data.get("roomType"),
            "address": data.get("address"),
            "capacity": data.get("capacity"),
            "facilities": ",".join(data["facilities"]) if data.get("facilities") else None,
            "description": data.get("description"),
            "cover_attachment_id": data.get("coverAttachmentId"),
            "booking_notice": data.get("bookingNotice"),
        }.items() if v is not None}
        self.repo.update_room(room, **update_fields)
        self._sync_room_images(room_id, data)
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="UPDATE_ROOM",
            business_id=room.id,
            operation_content=f"修改会议室：{room.room_name}",
        )
        self.db.commit()
        self.db.refresh(room)
        return self._enrich_room_media(room)

    def set_room_status(self, room_id: int, status: str, operator: dict) -> dict:
        if status not in [RoomStatus.ENABLED, RoomStatus.DISABLED]:
            raise ParamException("无效的状态值")
        room = self.repo.get_room_by_id(room_id)
        if not room:
            raise NotFoundException("会议室不存在")
        self.repo.update_room(room, status=status)
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="SET_ROOM_STATUS",
            business_id=room.id,
            operation_content=f"会议室状态变更为：{status}",
        )
        self.db.commit()
        self.db.refresh(room)
        return _room_to_dict(room)

    def set_open_rules(self, room_id: int, rules: list, operator: dict) -> dict:
        room = self.repo.get_room_by_id(room_id)
        if not room:
            raise NotFoundException("会议室不存在")
        self.repo.replace_open_rules(room_id, rules)
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="SET_OPEN_RULES",
            business_id=room_id,
            operation_content="更新开放规则",
        )
        self.db.commit()
        return {"roomId": room_id, "rules": rules}

    def create_special_date(self, data: dict, operator: dict) -> dict:
        from datetime import date as date_type
        special_date = data["specialDate"]
        if isinstance(special_date, str):
            special_date = date_type.fromisoformat(special_date)
        obj = self.repo.create_special_date(
            region_code=data["regionCode"],
            service_center_id=data.get("serviceCenterId"),
            special_date=special_date,
            date_type=data["dateType"],
            open_flag=data["openFlag"],
            reason=data.get("reason"),
        )
        self.db.commit()
        self.db.refresh(obj)
        return {"id": obj.id, "specialDate": str(obj.special_date), "dateType": obj.date_type,
                "openFlag": obj.open_flag, "reason": obj.reason}

    def create_occupy(self, data: dict, operator: dict) -> dict:
        room = self.repo.get_room_by_id(data["roomId"])
        if not room:
            raise NotFoundException("会议室不存在")
        start = data["startTime"]
        end = data["endTime"]
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        if end <= start:
            raise ParamException("结束时间必须晚于开始时间")
        self._check_booking_conflict(room.id, start, end)
        self._check_occupy_conflict(room.id, start, end)

        obj = self.repo.create_occupy(
            room_id=room.id,
            occupy_title=data["occupyTitle"],
            occupy_reason=data.get("occupyReason"),
            start_time=start,
            end_time=end,
            created_by=operator.get("operator_id", ""),
            created_by_name=operator.get("operator_name", ""),
        )
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type=AuditAction.OCCUPY,
            business_id=obj.id,
            operation_content=f"手工占用：{data['occupyTitle']}",
        )
        self.db.commit()
        self.db.refresh(obj)
        return {"id": obj.id, "roomId": obj.room_id, "occupyTitle": obj.occupy_title,
                "startTime": obj.start_time.isoformat(), "endTime": obj.end_time.isoformat()}

    def list_material_rules(
        self,
        region_code: Optional[str] = None,
        service_center_id: Optional[int] = None,
        room_id: Optional[int] = None,
        enterprise_type: Optional[str] = None,
        enabled: Optional[int] = None,
    ):
        rules = self.repo.get_material_rules(
            region_code=region_code, service_center_id=service_center_id,
            room_id=room_id, enterprise_type=enterprise_type, enabled=enabled,
        )
        return [_material_rule_to_dict(r) for r in rules]

    def create_material_rule(self, data: dict, operator: dict) -> dict:
        rule = self.repo.create_material_rule(
            room_id=data.get("roomId"),
            region_code=data.get("regionCode"),
            region_name=data.get("regionName"),
            service_center_id=data.get("serviceCenterId"),
            service_center_name=data.get("serviceCenterName"),
            enterprise_type=data.get("enterpriseType"),
            material_name=data["materialName"],
            material_code=data["materialCode"],
            required_flag=data.get("requiredFlag", 1),
            template_attachment_id=data.get("templateAttachmentId"),
            description=data.get("description"),
            sort_no=data.get("sortNo", 0),
        )
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="CREATE_MATERIAL_RULE",
            operation_content=f"新增材料规则：{rule.material_name}",
        )
        self.db.commit()
        self.db.refresh(rule)
        return _material_rule_to_dict(rule)

    def update_material_rule(self, rule_id: int, data: dict, operator: dict) -> dict:
        rule = self.repo.get_material_rule_by_id(rule_id)
        if not rule:
            raise NotFoundException("材料规则不存在")
        field_map = {
            "region_code": "regionCode", "region_name": "regionName",
            "service_center_id": "serviceCenterId", "service_center_name": "serviceCenterName",
            "material_name": "materialName", "required_flag": "requiredFlag",
            "template_attachment_id": "templateAttachmentId",
            "description": "description", "enabled": "enabled", "sort_no": "sortNo",
        }
        update_fields = {db_k: data[api_k] for db_k, api_k in field_map.items() if api_k in data and data[api_k] is not None}
        self.repo.update_material_rule(rule, **update_fields)
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="UPDATE_MATERIAL_RULE",
            operation_content=f"修改材料规则：{rule.material_name}",
        )
        self.db.commit()
        self.db.refresh(rule)
        return _material_rule_to_dict(rule)

    def delete_material_rule(self, rule_id: int, operator: dict) -> None:
        rule = self.repo.get_material_rule_by_id(rule_id)
        if not rule:
            raise NotFoundException("材料规则不存在")
        rule.deleted_flag = 1
        self.db.flush()
        self.repo.add_operation_log(
            operator_type=operator.get("operator_type", "USER"),
            operator_id=operator.get("operator_id", ""),
            operator_name=operator.get("operator_name", ""),
            operation_type="DELETE_MATERIAL_RULE",
            operation_content=f"删除材料规则：{rule.material_name}",
        )
        self.db.commit()

    # ── Admin: Booking ────────────────────────────────────────────────────────

    def list_bookings_admin(self, query: dict, data_scope: str, current_region_code: str):
        total, records = self.repo.list_bookings_admin(
            room_id=query.get("roomId"),
            enterprise_name=query.get("enterpriseName"),
            credit_code=query.get("creditCode"),
            status=query.get("status"),
            start_date=query.get("startDate"),
            end_date=query.get("endDate"),
            region_code_filter=query.get("regionCode"),
            service_center_id=query.get("serviceCenterId"),
            page_no=query.get("pageNo", 1),
            page_size=query.get("pageSize", 10),
            data_scope=data_scope,
            current_region_code=current_region_code,
        )
        return total, [_booking_to_dict(b) for b in records]

    def get_booking_detail_admin(self, booking_id: int) -> dict:
        booking = self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        d = self._build_booking_detail(booking)
        enterprise = self.ent_repo.get_by_id(booking.enterprise_id)
        if enterprise:
            d["enterpriseInfo"] = {
                "id": enterprise.id, "enterpriseName": enterprise.enterprise_name,
                "creditCode": enterprise.credit_code,
                "regionName": booking.region_name or enterprise.region_name,
                "legalPersonMobile": enterprise.legal_person_mobile,
                "meetingNoShowCount": enterprise.meeting_no_show_count,
                "meetingBookingDisabled": enterprise.meeting_booking_disabled,
            }
        room = self.repo.get_room_by_id(booking.room_id)
        if room:
            facilities = room.facilities.split(",") if room.facilities else []
            d["roomInfo"] = {
                "roomName": room.room_name,
                "address": room.address,
                "capacity": room.capacity,
                "facilities": facilities,
                "serviceCenterName": room.service_center_name,
            }
        return d

    def approve_booking(self, booking_id: int, data: dict, operator: dict) -> dict:
        booking = self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.APPROVE)

        # Re-check conflicts on approval
        self._check_booking_conflict(booking.room_id, booking.start_time, booking.end_time, exclude_id=booking_id)
        self._check_occupy_conflict(booking.room_id, booking.start_time, booking.end_time)

        old_status = booking.status
        now = datetime.utcnow()
        new_status = BookingStatus.APPROVED
        self.repo.update_booking(booking, status=new_status, approved_at=now)
        self._write_audit(booking.id, AuditAction.APPROVE, old_status, new_status, operator,
                          data.get("auditOpinion"))
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)

    def reject_booking(self, booking_id: int, data: dict, operator: dict) -> dict:
        booking = self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.REJECT)
        old_status = booking.status
        self.repo.update_booking(booking, status=BookingStatus.REJECTED)
        self._write_audit(booking.id, AuditAction.REJECT, old_status, BookingStatus.REJECTED, operator,
                          data.get("auditOpinion"))
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)

    def return_supplement(self, booking_id: int, data: dict, operator: dict) -> dict:
        booking = self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.RETURN_SUPPLEMENT)
        old_status = booking.status
        self.repo.update_booking(booking, status=BookingStatus.NEED_SUPPLEMENT)
        self._write_audit(booking.id, AuditAction.RETURN_SUPPLEMENT, old_status, BookingStatus.NEED_SUPPLEMENT,
                          operator, data.get("auditOpinion"))
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)

    def complete_booking(self, booking_id: int, data: dict, operator: dict) -> dict:
        booking = self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.COMPLETE)
        old_status = booking.status
        now = datetime.utcnow()
        self.repo.update_booking(booking, status=BookingStatus.COMPLETED, completed_at=now)
        self.repo.create_usage(
            booking_id=booking.id, room_id=booking.room_id, usage_status="COMPLETED",
            actual_start_time=data.get("actualStartTime"), actual_end_time=data.get("actualEndTime"),
            confirm_user_id=operator.get("operator_id"), confirm_user_name=operator.get("operator_name"),
            confirm_time=now, remark=data.get("remark"),
        )
        self._write_audit(booking.id, AuditAction.COMPLETE, old_status, BookingStatus.COMPLETED, operator,
                          data.get("remark"))
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)

    def no_show_booking(self, booking_id: int, data: dict, operator: dict) -> dict:
        booking = self.repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException("预约记录不存在")
        self._check_status(booking, AuditAction.NO_SHOW)
        old_status = booking.status
        now = datetime.utcnow()
        self.repo.update_booking(booking, status=BookingStatus.NO_SHOW)
        self.repo.create_usage(
            booking_id=booking.id, room_id=booking.room_id, usage_status="NO_SHOW",
            confirm_user_id=operator.get("operator_id"), confirm_user_name=operator.get("operator_name"),
            confirm_time=now, remark=data.get("reason"),
        )
        self.repo.create_no_show(
            enterprise_id=booking.enterprise_id, enterprise_name=booking.enterprise_name,
            credit_code=booking.credit_code, booking_id=booking.id, room_id=booking.room_id,
            no_show_time=now, reason=data.get("reason"),
            operator_id=operator.get("operator_id", ""), operator_name=operator.get("operator_name", ""),
        )
        # Update enterprise no-show count
        enterprise = self.ent_repo.get_by_id(booking.enterprise_id)
        if enterprise:
            new_count = enterprise.meeting_no_show_count + 1
            disabled = 1 if new_count >= NO_SHOW_DISABLE_THRESHOLD else enterprise.meeting_booking_disabled
            enterprise.meeting_no_show_count = new_count
            enterprise.meeting_booking_disabled = disabled
            self.db.flush()

        self._write_audit(booking.id, AuditAction.NO_SHOW, old_status, BookingStatus.NO_SHOW, operator,
                          data.get("reason"))
        self.db.commit()
        self.db.refresh(booking)
        return _booking_to_dict(booking)
