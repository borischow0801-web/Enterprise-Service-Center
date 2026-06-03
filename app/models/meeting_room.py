from datetime import datetime, date
from typing import Optional
from sqlalchemy import BigInteger, String, Text, DateTime, SmallInteger, Integer, Index, UniqueConstraint, Date
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class MeetingRoom(Base, TimestampMixin):
    __tablename__ = "meeting_room"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_name: Mapped[str] = mapped_column(String(200), nullable=False)
    room_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    service_center_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    facilities: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cover_attachment_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    booking_notice: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ENABLED")

    __table_args__ = (
        Index("ix_meeting_room_region_code", "region_code"),
        Index("ix_meeting_room_service_center_id", "service_center_id"),
        Index("ix_meeting_room_status", "status"),
    )


class MeetingRoomImage(Base, TimestampMixin):
    """会议室图片（多图 + 封面标记）"""
    __tablename__ = "meeting_room_image"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    attachment_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_cover: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MeetingRoomOpenRule(Base, TimestampMixin):
    __tablename__ = "meeting_room_open_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)  # 1=Mon ... 7=Sun
    open_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    start_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    end_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    __table_args__ = (
        Index("ix_meeting_room_open_rule_room_id", "room_id"),
        Index("ix_meeting_room_open_rule_weekday", "weekday"),
    )


class MeetingRoomSpecialDate(Base, TimestampMixin):
    __tablename__ = "meeting_room_special_date"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    service_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    special_date: Mapped[date] = mapped_column(Date, nullable=False)
    date_type: Mapped[str] = mapped_column(String(50), nullable=False)
    open_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    reason: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    __table_args__ = (
        Index("ix_meeting_room_special_date_region_code", "region_code"),
        Index("ix_meeting_room_special_date_service_center_id", "service_center_id"),
        Index("ix_meeting_room_special_date_special_date", "special_date"),
    )


class MeetingRoomOccupy(Base, TimestampMixin):
    __tablename__ = "meeting_room_occupy"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    occupy_title: Mapped[str] = mapped_column(String(200), nullable=False)
    occupy_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False)
    created_by_name: Mapped[str] = mapped_column(String(100), nullable=False)

    __table_args__ = (
        Index("ix_meeting_room_occupy_room_id", "room_id"),
        Index("ix_meeting_room_occupy_start_time", "start_time"),
        Index("ix_meeting_room_occupy_end_time", "end_time"),
    )


class MeetingRoomMaterialRule(Base, TimestampMixin):
    __tablename__ = "meeting_room_material_rule"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    room_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # deprecated: use region_code+service_center_id
    region_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    region_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    service_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    service_center_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enterprise_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    material_name: Mapped[str] = mapped_column(String(200), nullable=False)
    material_code: Mapped[str] = mapped_column(String(100), nullable=False)
    required_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    template_attachment_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    enabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_mrmr_room_id", "room_id"),
        Index("ix_mrmr_region_code", "region_code"),
        Index("ix_mrmr_service_center_id", "service_center_id"),
        Index("ix_mrmr_region_center", "region_code", "service_center_id"),
        Index("ix_mrmr_material_code", "material_code"),
        Index("ix_mrmr_enterprise_type", "enterprise_type"),
    )


class MeetingRoomBooking(Base, TimestampMixin):
    __tablename__ = "meeting_room_booking"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    room_name: Mapped[str] = mapped_column(String(200), nullable=False)
    enterprise_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    meeting_subject: Mapped[str] = mapped_column(String(200), nullable=False)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(64), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    support_items: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    enterprise_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    enterprise_type_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_meeting_room_booking_room_id", "room_id"),
        Index("ix_meeting_room_booking_enterprise_id", "enterprise_id"),
        Index("ix_meeting_room_booking_credit_code", "credit_code"),
        Index("ix_meeting_room_booking_region_code", "region_code"),
        Index("ix_meeting_room_booking_service_center_id", "service_center_id"),
        Index("ix_meeting_room_booking_status", "status"),
        Index("ix_meeting_room_booking_start_time", "start_time"),
        Index("ix_meeting_room_booking_end_time", "end_time"),
    )


class MeetingRoomBookingAudit(Base):
    __tablename__ = "meeting_room_booking_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    before_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    after_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    audit_opinion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operator_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_meeting_room_booking_audit_booking_id", "booking_id"),
        Index("ix_meeting_room_booking_audit_action_type", "action_type"),
        Index("ix_meeting_room_booking_audit_operator_id", "operator_id"),
    )


class MeetingRoomUsage(Base, TimestampMixin):
    __tablename__ = "meeting_room_usage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    booking_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    usage_status: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    actual_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confirm_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confirm_user_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confirm_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        Index("ix_meeting_room_usage_booking_id", "booking_id"),
        Index("ix_meeting_room_usage_room_id", "room_id"),
        Index("ix_meeting_room_usage_usage_status", "usage_status"),
    )


class MeetingRoomNoShow(Base):
    __tablename__ = "meeting_room_no_show"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False)
    booking_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    no_show_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    operator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    __table_args__ = (
        Index("ix_meeting_room_no_show_enterprise_id", "enterprise_id"),
        Index("ix_meeting_room_no_show_credit_code", "credit_code"),
        Index("ix_meeting_room_no_show_booking_id", "booking_id"),
        Index("ix_meeting_room_no_show_room_id", "room_id"),
    )
