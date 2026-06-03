from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Index, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class ServiceCenter(TimestampMixin, Base):
    __tablename__ = "service_center"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    center_name: Mapped[str] = mapped_column(String(200), nullable=False)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ENABLED")


class SysUserSnapshot(TimestampMixin, Base):
    __tablename__ = "sys_user_snapshot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    platform_user_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    real_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    department_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    department_name: Mapped[str] = mapped_column(String(200), nullable=False)
    region_code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    region_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role_codes: Mapped[str] = mapped_column(String(500), nullable=False)
    role_names: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    data_scope: Mapped[str] = mapped_column(String(50), nullable=False)
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class SysDictionary(TimestampMixin, Base):
    __tablename__ = "sys_dictionary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    dict_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dict_code: Mapped[str] = mapped_column(String(100), nullable=False)
    dict_label: Mapped[str] = mapped_column(String(200), nullable=False)
    dict_value: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    sort_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    enabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    parent_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extra_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("dict_type", "dict_code", name="uq_sys_dictionary_type_code"),
    )


class SysAttachment(Base):
    __tablename__ = "sys_attachment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_type: Mapped[str] = mapped_column(String(50), nullable=False)
    business_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    file_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_ext: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_by_type: Mapped[str] = mapped_column(String(20), nullable=False)
    uploaded_by_id: Mapped[str] = mapped_column(String(100), nullable=False)
    uploaded_by_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_flag: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    __table_args__ = (
        Index("ix_sys_attachment_business", "business_type", "business_id"),
    )


class SysMessageRecord(Base):
    __tablename__ = "sys_message_record"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    business_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    receiver_type: Mapped[str] = mapped_column(String(30), nullable=False)
    receiver_id: Mapped[str] = mapped_column(String(100), nullable=False)
    receiver_name: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="SYSTEM")
    send_status: Mapped[str] = mapped_column(String(30), nullable=False, default="SENT")
    send_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    read_status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    read_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_sys_message_record_receiver", "receiver_type", "receiver_id"),
        Index("ix_sys_message_record_business", "business_type", "business_id"),
    )


class SysEvaluation(Base):
    __tablename__ = "sys_evaluation"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_type: Mapped[str] = mapped_column(String(50), nullable=False)
    business_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    enterprise_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    satisfaction: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    resolved_flag: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    evaluate_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    deleted_flag: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    __table_args__ = (
        Index("ix_sys_evaluation_business", "business_type", "business_id"),
        Index("ix_sys_evaluation_enterprise_id", "enterprise_id"),
    )


class SysOperationLog(Base):
    __tablename__ = "sys_operation_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    operator_type: Mapped[str] = mapped_column(String(30), nullable=False)
    operator_id: Mapped[str] = mapped_column(String(100), nullable=False)
    operator_name: Mapped[str] = mapped_column(String(100), nullable=False)
    business_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    business_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    before_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    after_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_sys_operation_log_operator", "operator_type", "operator_id"),
        Index("ix_sys_operation_log_business", "business_type", "business_id"),
        Index("ix_sys_operation_log_operation_type", "operation_type"),
    )
