from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Text, DateTime, SmallInteger, Integer, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class AppealMain(Base, TimestampMixin):
    __tablename__ = "appeal_main"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appeal_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    enterprise_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(64), nullable=False)
    industry_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    industry_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    appeal_type_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    appeal_type_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    urgency_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    handle_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    responsible_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    responsible_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reply_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_appeal_main_enterprise_id", "enterprise_id"),
        Index("ix_appeal_main_credit_code", "credit_code"),
        Index("ix_appeal_main_region_code", "region_code"),
        Index("ix_appeal_main_status", "status"),
        Index("ix_appeal_main_responsible_dept_id", "responsible_dept_id"),
        Index("ix_appeal_main_submitted_at", "submitted_at"),
    )


class AppealRecord(Base):
    __tablename__ = "appeal_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_name: Mapped[str] = mapped_column(String(100), nullable=False)
    before_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    after_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    opinion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operator_type: Mapped[str] = mapped_column(String(30), nullable=False)
    operator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operator_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_appeal_record_appeal_id", "appeal_id"),
        Index("ix_appeal_record_action_type", "action_type"),
        Index("ix_appeal_record_operator", "operator_type", "operator_id"),
    )


class AppealAssignment(Base, TimestampMixin):
    __tablename__ = "appeal_assignment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    assigned_dept_id: Mapped[str] = mapped_column(String(100), nullable=False)
    assigned_dept_name: Mapped[str] = mapped_column(String(200), nullable=False)
    assigned_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_user_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assign_opinion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reply_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_appeal_assignment_appeal_id", "appeal_id"),
        Index("ix_appeal_assignment_assigned_dept_id", "assigned_dept_id"),
        Index("ix_appeal_assignment_status", "status"),
    )


class AppealFollowup(Base):
    __tablename__ = "appeal_followup"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    appeal_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    evaluation_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    responsible_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    responsible_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    followup_status: Mapped[str] = mapped_column(String(50), nullable=False)
    followup_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    followup_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    followup_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    followup_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    followup_user_name: Mapped[str] = mapped_column(String(100), nullable=False)
    followup_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    __table_args__ = (
        Index("ix_appeal_followup_appeal_id", "appeal_id"),
        Index("ix_appeal_followup_evaluation_id", "evaluation_id"),
        Index("ix_appeal_followup_responsible_dept_id", "responsible_dept_id"),
    )
