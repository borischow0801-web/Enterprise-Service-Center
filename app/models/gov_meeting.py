from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, Text, DateTime, SmallInteger, Integer, Date, Time, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.base import TimestampMixin


class GovMeetingApply(Base, TimestampMixin):
    """政企约见申请主表"""
    __tablename__ = "gov_meeting_apply"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    apply_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    enterprise_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(64), nullable=False)
    topic_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    topic_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meeting_level: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 兼容旧字段，已拆分
    expected_level_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 企业期望约见层级
    expected_level_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    final_level_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # 后台研判约见层级
    final_level_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)              # 约见申请标题
    meeting_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)           # 约见内容
    discussion_item: Mapped[Optional[str]] = mapped_column(Text, nullable=True)           # 洽谈事项
    urgency_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)       # 紧急程度
    industry_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)      # 所属行业代码
    industry_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)      # 所属行业名称
    registered_address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True) # 注册地址
    description: Mapped[str] = mapped_column(Text, nullable=False)  # 申请说明（兼容）
    commitment_checked: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    service_center_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    service_center_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    reject_reason_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reject_reason_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reject_opinion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    arranged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    meeting_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)    # 实际约见时间
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_gov_meeting_apply_enterprise_id", "enterprise_id"),
        Index("ix_gov_meeting_apply_credit_code", "credit_code"),
        Index("ix_gov_meeting_apply_region_code", "region_code"),
        Index("ix_gov_meeting_apply_status", "status"),
        Index("ix_gov_meeting_apply_submitted_at", "submitted_at"),
    )


class GovMeetingAudit(Base):
    """政企约见审核/操作流水"""
    __tablename__ = "gov_meeting_audit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    apply_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    action_name: Mapped[str] = mapped_column(String(100), nullable=False)
    before_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    after_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    opinion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    operator_type: Mapped[str] = mapped_column(String(30), nullable=False)   # USER / ENTERPRISE
    operator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    operator_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_gov_meeting_audit_apply_id", "apply_id"),
        Index("ix_gov_meeting_audit_action_type", "action_type"),
    )


class GovMeetingArrangement(Base, TimestampMixin):
    """政企约见安排"""
    __tablename__ = "gov_meeting_arrangement"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    apply_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    meeting_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 约见日期时间
    meeting_place: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    meeting_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)   # ON_SITE/VIDEO/PHONE
    gov_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    gov_contact_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)     # 约见开始时间
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)       # 约见结束时间
    host_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)    # 主持部门ID
    host_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 主持部门名称
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)                  # 备注说明
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confirmed_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    __table_args__ = (
        Index("ix_gov_meeting_arrangement_apply_id", "apply_id"),
    )


class GovMeetingParticipant(Base):
    """政企约见参与人"""
    __tablename__ = "gov_meeting_participant"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    arrangement_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    apply_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    participant_type: Mapped[str] = mapped_column(String(30), nullable=False)   # GOV / ENTERPRISE
    participant_name: Mapped[str] = mapped_column(String(100), nullable=False)
    participant_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    participant_dept_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)    # 所在部门ID
    participant_dept_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)  # 所在部门名称
    contact_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)           # 联系电话
    role_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)              # 参会角色
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_gov_meeting_participant_arrangement_id", "arrangement_id"),
        Index("ix_gov_meeting_participant_apply_id", "apply_id"),
    )


class GovMeetingRecord(Base):
    """政企约见纪要"""
    __tablename__ = "gov_meeting_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    apply_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    arrangement_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)          # 会议内容
    conclusions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)    # 会议结论
    follow_up_items: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # 后续事项
    recorder_id: Mapped[str] = mapped_column(String(100), nullable=False)
    recorder_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    deleted_flag: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    __table_args__ = (
        Index("ix_gov_meeting_record_apply_id", "apply_id"),
        Index("ix_gov_meeting_record_arrangement_id", "arrangement_id"),
    )
