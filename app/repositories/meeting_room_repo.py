from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.constants.permission import resolve_scope_branch, ScopeBranch
from app.models.meeting_room import (
    MeetingRoom, MeetingRoomImage, MeetingRoomOpenRule, MeetingRoomSpecialDate,
    MeetingRoomOccupy, MeetingRoomMaterialRule, MeetingRoomBooking,
    MeetingRoomBookingAudit, MeetingRoomUsage, MeetingRoomNoShow,
)
from app.models.system import SysAttachment, SysOperationLog
from app.constants.meeting_room import BookingStatus


def generate_booking_no(db: Session) -> str:
    from app.utils.serial_no import generate_daily_serial
    return generate_daily_serial(db, MeetingRoomBooking, MeetingRoomBooking.booking_no, "HY", "MEETING_BOOKING")


class MeetingRoomRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── MeetingRoom ───────────────────────────────────────────────────────────

    def get_room_by_id(self, room_id: int) -> Optional[MeetingRoom]:
        return self.db.query(MeetingRoom).filter(
            MeetingRoom.id == room_id, MeetingRoom.deleted_flag == 0
        ).first()

    def lock_room_for_update(self, room_id: int) -> Optional[MeetingRoom]:
        """对该会议室行加排他锁（SELECT ... FOR UPDATE），锁持续到调用方
        所在事务提交/回滚为止。用于将"同一会议室"的审批操作序列化，
        不同会议室之间互不阻塞。这是一次锁定读，会读取最新已提交数据，
        忽略当前事务（REPEATABLE READ）建立的一致性快照。"""
        return self.db.query(MeetingRoom).filter(
            MeetingRoom.id == room_id, MeetingRoom.deleted_flag == 0
        ).with_for_update().first()

    def list_rooms_enterprise(self, region_code, capacity_min, facility, room_type, page_no, page_size):
        q = self.db.query(MeetingRoom).filter(
            MeetingRoom.status == "ENABLED", MeetingRoom.deleted_flag == 0
        )
        if region_code:
            q = q.filter(MeetingRoom.region_code == region_code)
        if capacity_min:
            q = q.filter(MeetingRoom.capacity >= capacity_min)
        if facility:
            q = q.filter(MeetingRoom.facilities.like(f"%{facility}%"))
        if room_type:
            q = q.filter(MeetingRoom.room_type == room_type)
        total = q.count()
        records = q.order_by(MeetingRoom.id.desc()).offset((page_no-1)*page_size).limit(page_size).all()
        return total, records

    def list_rooms_admin(self, region_code, service_center_id, status, room_type, page_no, page_size, data_scope, current_region_code):
        q = self.db.query(MeetingRoom).filter(MeetingRoom.deleted_flag == 0)
        # Fail Closed：会议室模块没有部门级归属概念，DEPARTMENT/SELF 按区域近似处理
        # （历史设计如此），未知 data_scope 一律不返回数据。
        branch = resolve_scope_branch(data_scope)
        if branch == ScopeBranch.DENY:
            return 0, []
        if branch in (ScopeBranch.REGION, ScopeBranch.DEPARTMENT):
            if not current_region_code:
                return 0, []
            q = q.filter(MeetingRoom.region_code == current_region_code)
        if region_code:
            q = q.filter(MeetingRoom.region_code == region_code)
        if service_center_id:
            q = q.filter(MeetingRoom.service_center_id == service_center_id)
        if status:
            q = q.filter(MeetingRoom.status == status)
        if room_type:
            q = q.filter(MeetingRoom.room_type == room_type)
        total = q.count()
        records = q.order_by(MeetingRoom.id.desc()).offset((page_no-1)*page_size).limit(page_size).all()
        return total, records

    def create_room(self, **kwargs) -> MeetingRoom:
        room = MeetingRoom(**kwargs)
        self.db.add(room)
        self.db.flush()
        return room

    def update_room(self, room: MeetingRoom, **kwargs) -> MeetingRoom:
        for k, v in kwargs.items():
            setattr(room, k, v)
        room.updated_at = datetime.utcnow()
        self.db.flush()
        return room

    # ── Room images ───────────────────────────────────────────────────────────

    def get_room_images(self, room_id: int) -> list[MeetingRoomImage]:
        return self.db.query(MeetingRoomImage).filter(
            MeetingRoomImage.room_id == room_id,
            MeetingRoomImage.deleted_flag == 0,
        ).order_by(MeetingRoomImage.sort_no, MeetingRoomImage.id).all()

    def replace_room_images(
        self,
        room_id: int,
        attachment_ids: list[int],
        cover_attachment_id: Optional[int] = None,
    ) -> None:
        self.db.query(MeetingRoomImage).filter(
            MeetingRoomImage.room_id == room_id,
        ).update({"deleted_flag": 1}, synchronize_session=False)
        if not attachment_ids:
            return
        cover_id = cover_attachment_id or attachment_ids[0]
        for idx, att_id in enumerate(attachment_ids):
            self.db.add(MeetingRoomImage(
                room_id=room_id,
                attachment_id=att_id,
                is_cover=1 if att_id == cover_id else 0,
                sort_no=idx,
            ))

    # ── OpenRules ─────────────────────────────────────────────────────────────

    def get_open_rules(self, room_id: int):
        return self.db.query(MeetingRoomOpenRule).filter(
            MeetingRoomOpenRule.room_id == room_id, MeetingRoomOpenRule.deleted_flag == 0
        ).order_by(MeetingRoomOpenRule.weekday).all()

    def replace_open_rules(self, room_id: int, rules: list) -> None:
        self.db.query(MeetingRoomOpenRule).filter(
            MeetingRoomOpenRule.room_id == room_id
        ).update({"deleted_flag": 1}, synchronize_session=False)
        for r in rules:
            obj = MeetingRoomOpenRule(
                room_id=room_id,
                weekday=r["weekday"],
                open_flag=r["openFlag"],
                start_time=r.get("startTime"),
                end_time=r.get("endTime"),
            )
            self.db.add(obj)
        self.db.flush()

    # ── SpecialDate ───────────────────────────────────────────────────────────

    def create_special_date(self, **kwargs) -> MeetingRoomSpecialDate:
        obj = MeetingRoomSpecialDate(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_special_dates(self, region_code: str, service_center_id: Optional[int], start: datetime, end: datetime):
        q = self.db.query(MeetingRoomSpecialDate).filter(
            MeetingRoomSpecialDate.deleted_flag == 0,
            MeetingRoomSpecialDate.special_date >= start.date(),
            MeetingRoomSpecialDate.special_date <= end.date(),
        )
        q = q.filter(
            or_(
                MeetingRoomSpecialDate.region_code == region_code,
                and_(
                    MeetingRoomSpecialDate.service_center_id == service_center_id,
                    MeetingRoomSpecialDate.service_center_id.isnot(None),
                )
            )
        )
        return q.all()

    def get_special_date_for_date(self, region_code: str, service_center_id: Optional[int], check_date):
        q = self.db.query(MeetingRoomSpecialDate).filter(
            MeetingRoomSpecialDate.deleted_flag == 0,
            MeetingRoomSpecialDate.special_date == check_date,
        )
        q = q.filter(
            or_(
                MeetingRoomSpecialDate.region_code == region_code,
                and_(
                    MeetingRoomSpecialDate.service_center_id == service_center_id,
                    MeetingRoomSpecialDate.service_center_id.isnot(None),
                )
            )
        )
        # MySQL 不支持 NULLS LAST，用 case 表达式代替：service_center_id 非空优先
        from sqlalchemy import case
        return q.order_by(
            case((MeetingRoomSpecialDate.service_center_id.isnot(None), 0), else_=1),
            MeetingRoomSpecialDate.service_center_id.desc(),
        ).first()

    # ── Occupy ────────────────────────────────────────────────────────────────

    def create_occupy(self, **kwargs) -> MeetingRoomOccupy:
        obj = MeetingRoomOccupy(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_occupies_in_range(self, room_id: int, start: datetime, end: datetime, exclude_id: Optional[int] = None):
        q = self.db.query(MeetingRoomOccupy).filter(
            MeetingRoomOccupy.room_id == room_id,
            MeetingRoomOccupy.deleted_flag == 0,
            MeetingRoomOccupy.start_time < end,
            MeetingRoomOccupy.end_time > start,
        )
        if exclude_id:
            q = q.filter(MeetingRoomOccupy.id != exclude_id)
        return q.all()

    # ── MaterialRule ──────────────────────────────────────────────────────────

    def get_material_rules(
        self,
        room_id: Optional[int] = None,
        region_code: Optional[str] = None,
        service_center_id: Optional[int] = None,
        enterprise_type: Optional[str] = None,
        enabled: Optional[int] = None,
    ):
        q = self.db.query(MeetingRoomMaterialRule).filter(MeetingRoomMaterialRule.deleted_flag == 0)
        if region_code is not None:
            q = q.filter(MeetingRoomMaterialRule.region_code == region_code)
        if service_center_id is not None:
            q = q.filter(MeetingRoomMaterialRule.service_center_id == service_center_id)
        elif region_code is not None:
            # When filtering by region only, exclude records tied to a specific service_center
            pass  # return all for that region regardless of service_center_id
        if room_id is not None and region_code is None:
            # Legacy: fall back to room_id filtering if no region given
            q = q.filter(or_(MeetingRoomMaterialRule.room_id == room_id, MeetingRoomMaterialRule.room_id.is_(None)))
        if enterprise_type:
            q = q.filter(or_(MeetingRoomMaterialRule.enterprise_type == enterprise_type, MeetingRoomMaterialRule.enterprise_type.is_(None)))
        if enabled is not None:
            q = q.filter(MeetingRoomMaterialRule.enabled == enabled)
        return q.order_by(MeetingRoomMaterialRule.sort_no, MeetingRoomMaterialRule.id).all()

    def _material_rules_base_query(self, enterprise_type: Optional[str] = None):
        q = self.db.query(MeetingRoomMaterialRule).filter(
            MeetingRoomMaterialRule.deleted_flag == 0,
            MeetingRoomMaterialRule.enabled == 1,
        )
        if enterprise_type:
            q = q.filter(or_(
                MeetingRoomMaterialRule.enterprise_type == enterprise_type,
                MeetingRoomMaterialRule.enterprise_type.is_(None),
            ))
        return q

    def _fetch_material_rules_tier(
        self,
        *,
        region_code: Optional[str] = None,
        service_center_id: Optional[int] = None,
        room_id: Optional[int] = None,
        region_is_null: bool = False,
        service_center_is_null: bool = False,
        enterprise_type: Optional[str] = None,
    ):
        q = self._material_rules_base_query(enterprise_type)
        if room_id is not None:
            q = q.filter(MeetingRoomMaterialRule.room_id == room_id)
        if region_is_null:
            q = q.filter(MeetingRoomMaterialRule.region_code.is_(None))
        elif region_code is not None:
            q = q.filter(MeetingRoomMaterialRule.region_code == region_code)
        if service_center_is_null:
            q = q.filter(MeetingRoomMaterialRule.service_center_id.is_(None))
        elif service_center_id is not None:
            q = q.filter(MeetingRoomMaterialRule.service_center_id == service_center_id)
        return q.order_by(MeetingRoomMaterialRule.sort_no, MeetingRoomMaterialRule.id).all()

    def get_applicable_material_rules(
        self,
        room_id: int,
        region_code: Optional[str],
        service_center_id: Optional[int],
        enterprise_type: Optional[str] = None,
    ) -> list[tuple[int, list]]:
        """按优先级分档返回材料规则：(priority, rules)，priority 越小优先级越高。"""
        tiers: list[tuple[int, list]] = []

        # 1. 区划 + 企服中心精确
        if region_code and service_center_id is not None:
            rules = self._fetch_material_rules_tier(
                region_code=region_code, service_center_id=service_center_id,
                enterprise_type=enterprise_type,
            )
            if rules:
                tiers.append((1, rules))

        # 2. 区划通用（企服中心为空）
        if region_code:
            rules = self._fetch_material_rules_tier(
                region_code=region_code, service_center_is_null=True,
                enterprise_type=enterprise_type,
            )
            if rules:
                tiers.append((2, rules))

        # 3. 企服中心通用（区划为空）
        if service_center_id is not None:
            rules = self._fetch_material_rules_tier(
                region_is_null=True, service_center_id=service_center_id,
                enterprise_type=enterprise_type,
            )
            if rules:
                tiers.append((3, rules))

        # 4. 全局通用
        rules = self._fetch_material_rules_tier(
            region_is_null=True, service_center_is_null=True,
            enterprise_type=enterprise_type,
        )
        if rules:
            tiers.append((4, rules))

        # 5. 兼容旧数据：仅 room_id
        legacy = self._fetch_material_rules_tier(room_id=room_id, enterprise_type=enterprise_type)
        legacy = [r for r in legacy if r.room_id == room_id]
        if legacy:
            tiers.append((5, legacy))

        return tiers

    def get_material_rules_by_region(
        self,
        region_code: str,
        service_center_id: Optional[int],
        enterprise_type: Optional[str] = None,
    ):
        """兼容旧调用：返回区划精确 + 区划通用合并列表（不含全局/企服中心/room）。"""
        tiers = self.get_applicable_material_rules(
            room_id=0, region_code=region_code,
            service_center_id=service_center_id, enterprise_type=enterprise_type,
        )
        out = []
        for pri, rules in tiers:
            if pri <= 2:
                out.extend(rules)
        return out

    def get_material_rule_by_id(self, rule_id: int) -> Optional[MeetingRoomMaterialRule]:
        return self.db.query(MeetingRoomMaterialRule).filter(
            MeetingRoomMaterialRule.id == rule_id, MeetingRoomMaterialRule.deleted_flag == 0
        ).first()

    def create_material_rule(self, **kwargs) -> MeetingRoomMaterialRule:
        obj = MeetingRoomMaterialRule(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_material_rule(self, rule: MeetingRoomMaterialRule, **kwargs) -> MeetingRoomMaterialRule:
        for k, v in kwargs.items():
            setattr(rule, k, v)
        rule.updated_at = datetime.utcnow()
        self.db.flush()
        return rule

    # ── Booking ───────────────────────────────────────────────────────────────

    def get_booking_by_id(self, booking_id: int) -> Optional[MeetingRoomBooking]:
        return self.db.query(MeetingRoomBooking).filter(
            MeetingRoomBooking.id == booking_id, MeetingRoomBooking.deleted_flag == 0
        ).first()

    def get_booking_by_id_for_update(self, booking_id: int) -> Optional[MeetingRoomBooking]:
        """锁定读，配合 lock_room_for_update 使用：在持有房间锁之后重新读取
        该预约的最新状态，避免 REPEATABLE READ 快照读到锁等待期间已被其他
        并发事务修改（例如同一预约被并发重复审批）之前的旧状态。"""
        return self.db.query(MeetingRoomBooking).filter(
            MeetingRoomBooking.id == booking_id, MeetingRoomBooking.deleted_flag == 0
        ).with_for_update().first()

    def get_booking_by_id_and_enterprise(self, booking_id: int, enterprise_id: int) -> Optional[MeetingRoomBooking]:
        return self.db.query(MeetingRoomBooking).filter(
            MeetingRoomBooking.id == booking_id,
            MeetingRoomBooking.enterprise_id == enterprise_id,
            MeetingRoomBooking.deleted_flag == 0,
        ).first()

    def create_booking(self, **kwargs) -> MeetingRoomBooking:
        obj = MeetingRoomBooking(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def update_booking(self, booking: MeetingRoomBooking, **kwargs) -> MeetingRoomBooking:
        for k, v in kwargs.items():
            setattr(booking, k, v)
        booking.updated_at = datetime.utcnow()
        self.db.flush()
        return booking

    def list_bookings_enterprise(self, enterprise_id: int, status: Optional[str], page_no: int, page_size: int):
        q = self.db.query(MeetingRoomBooking).filter(
            MeetingRoomBooking.enterprise_id == enterprise_id, MeetingRoomBooking.deleted_flag == 0
        )
        if status:
            q = q.filter(MeetingRoomBooking.status == status)
        total = q.count()
        records = q.order_by(MeetingRoomBooking.submitted_at.desc()).offset((page_no-1)*page_size).limit(page_size).all()
        return total, records

    def list_bookings_admin(self, room_id, enterprise_name, credit_code, status, start_date, end_date, region_code_filter, service_center_id, page_no, page_size, data_scope, current_region_code):
        q = self.db.query(MeetingRoomBooking).filter(MeetingRoomBooking.deleted_flag == 0)
        # Fail Closed：会议室预约没有部门级归属概念，DEPARTMENT/SELF 按区域近似处理
        # （历史设计如此），未知 data_scope 一律不返回数据。
        branch = resolve_scope_branch(data_scope)
        if branch == ScopeBranch.DENY:
            return 0, []
        if branch in (ScopeBranch.REGION, ScopeBranch.DEPARTMENT):
            if not current_region_code:
                return 0, []
            q = q.filter(MeetingRoomBooking.region_code == current_region_code)
        if room_id:
            q = q.filter(MeetingRoomBooking.room_id == room_id)
        if enterprise_name:
            q = q.filter(MeetingRoomBooking.enterprise_name.like(f"%{enterprise_name}%"))
        if credit_code:
            q = q.filter(MeetingRoomBooking.credit_code == credit_code)
        if status:
            q = q.filter(MeetingRoomBooking.status == status)
        if start_date:
            q = q.filter(MeetingRoomBooking.submitted_at >= start_date)
        if end_date:
            q = q.filter(MeetingRoomBooking.submitted_at <= f"{end_date} 23:59:59")
        if region_code_filter:
            q = q.filter(MeetingRoomBooking.region_code == region_code_filter)
        if service_center_id:
            q = q.filter(MeetingRoomBooking.service_center_id == service_center_id)
        total = q.count()
        records = q.order_by(MeetingRoomBooking.submitted_at.desc()).offset((page_no-1)*page_size).limit(page_size).all()
        return total, records

    def get_conflicting_bookings(self, room_id: int, start: datetime, end: datetime, exclude_id: Optional[int] = None):
        q = self.db.query(MeetingRoomBooking).filter(
            MeetingRoomBooking.room_id == room_id,
            MeetingRoomBooking.deleted_flag == 0,
            MeetingRoomBooking.status.in_([BookingStatus.APPROVED, BookingStatus.WAIT_USE]),
            MeetingRoomBooking.start_time < end,
            MeetingRoomBooking.end_time > start,
        )
        if exclude_id:
            q = q.filter(MeetingRoomBooking.id != exclude_id)
        return q.all()

    # ── Audit Record ──────────────────────────────────────────────────────────

    def add_audit(self, booking_id: int, action_type: str, before_status: Optional[str], after_status: Optional[str],
                  operator_id: str, operator_name: str, audit_opinion: Optional[str] = None,
                  operator_dept_id: Optional[str] = None, operator_dept_name: Optional[str] = None) -> MeetingRoomBookingAudit:
        obj = MeetingRoomBookingAudit(
            booking_id=booking_id, action_type=action_type,
            before_status=before_status, after_status=after_status,
            audit_opinion=audit_opinion, operator_id=operator_id,
            operator_name=operator_name, operator_dept_id=operator_dept_id,
            operator_dept_name=operator_dept_name,
        )
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_audits(self, booking_id: int):
        return self.db.query(MeetingRoomBookingAudit).filter(
            MeetingRoomBookingAudit.booking_id == booking_id
        ).order_by(MeetingRoomBookingAudit.created_at.asc()).all()

    # ── Usage ─────────────────────────────────────────────────────────────────

    def create_usage(self, **kwargs) -> MeetingRoomUsage:
        obj = MeetingRoomUsage(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_usage(self, booking_id: int) -> Optional[MeetingRoomUsage]:
        return self.db.query(MeetingRoomUsage).filter(
            MeetingRoomUsage.booking_id == booking_id, MeetingRoomUsage.deleted_flag == 0
        ).first()

    # ── NoShow ────────────────────────────────────────────────────────────────

    def create_no_show(self, **kwargs) -> MeetingRoomNoShow:
        obj = MeetingRoomNoShow(**kwargs)
        self.db.add(obj)
        self.db.flush()
        return obj

    # ── Attachments ───────────────────────────────────────────────────────────

    def bind_attachments(self, booking_id: int, attachment_ids: list, file_category: Optional[str] = None) -> None:
        if not attachment_ids:
            return
        values = {"business_type": "MEETING_ROOM_BOOKING", "business_id": booking_id}
        if file_category:
            values["file_category"] = file_category
        self.db.query(SysAttachment).filter(
            SysAttachment.id.in_(attachment_ids), SysAttachment.deleted_flag == 0
        ).update(values, synchronize_session=False)

    def bind_attachments_by_materials(self, booking_id: int, material_items: list) -> None:
        """material_items: [{materialCode, attachmentIds}]"""
        bound: set = set()
        for item in material_items:
            code = item.get("materialCode") or item.get("material_code")
            ids = [i for i in (item.get("attachmentIds") or item.get("attachment_ids") or []) if i]
            if not code or not ids:
                continue
            for att_id in ids:
                if att_id in bound:
                    continue
                self.db.query(SysAttachment).filter(
                    SysAttachment.id == att_id, SysAttachment.deleted_flag == 0
                ).update({
                    "business_type": "MEETING_ROOM_BOOKING",
                    "business_id": booking_id,
                    "file_category": code,
                }, synchronize_session=False)
                bound.add(att_id)

    def get_attachments(self, booking_id: int):
        return self.db.query(SysAttachment).filter(
            SysAttachment.business_type == "MEETING_ROOM_BOOKING",
            SysAttachment.business_id == booking_id,
            SysAttachment.deleted_flag == 0,
        ).all()

    # ── Operation Log ─────────────────────────────────────────────────────────

    def add_operation_log(self, operator_type: str, operator_id: str, operator_name: str,
                          operation_type: str, business_id: Optional[int] = None,
                          operation_content: Optional[str] = None,
                          before_status: Optional[str] = None, after_status: Optional[str] = None) -> None:
        log = SysOperationLog(
            operator_type=operator_type, operator_id=operator_id, operator_name=operator_name,
            business_type="MEETING_ROOM_BOOKING", business_id=business_id,
            operation_type=operation_type, operation_content=operation_content,
            before_status=before_status, after_status=after_status,
        )
        self.db.add(log)
        self.db.flush()
