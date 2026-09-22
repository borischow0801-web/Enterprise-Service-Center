from datetime import date as date_type, datetime
from typing import Optional
from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class SysDailySerial(Base):
    """按日流水号计数器：每个 (business_type, business_date) 对应一行，
    current_value 通过原子 UPDATE 自增，作为 app/utils/serial_no.py 生成
    Appeal/MeetingRoomBooking/GovMeetingApply 编号的并发安全计数源。
    不参与任何业务归属查询，只用作互斥计数，因此不使用 TimestampMixin。"""

    __tablename__ = "sys_daily_serial"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    business_type: Mapped[str] = mapped_column(String(30), nullable=False)
    business_date: Mapped[date_type] = mapped_column(Date, nullable=False)
    current_value: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("business_type", "business_date", name="uq_sys_daily_serial_type_date"),
    )


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
    """仅供 admin_mock_login（开发/测试模拟登录）使用的身份快照表。

    字段全部由调用方自报、零校验——这是它作为"mock 登录"存在的本意，不是缺陷。
    正式的、经统一身份认证（BSPPLUS）核实身份后签发的管理端账号，一律使用
    SysAdminUser，两张表互不混用、互不参照，避免自报数据污染正式 RBAC 数据。
    """

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


class AdminUserStatus:
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class SysAdminUser(TimestampMixin, Base):
    """正式管理端账号——统一身份认证（BSPPLUS）登录的匹配/角色分配来源。

    与 SysUserSnapshot 的关键区别：本表的 role_codes/data_scope/region_code/
    department_id 只能由本系统的管理员管理界面（或运维预置）写入，BSP 登录流程
    只读取这些字段用于签发 JWT，绝不会在登录时被请求体或 BSP 返回值覆盖——
    这是"BSP 只管认证、本系统管授权"这条原则在数据层的落地。
    """

    __tablename__ = "sys_admin_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # BSP 侧稳定用户内码（对应文档 user.id）。首次通过 username 安全绑定前为空。
    bsp_user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    # BSP 登录账号（对应文档 user.username/account），本系统内也保持唯一，
    # 用于 bsp_user_id 尚未绑定时的首次安全绑定匹配。
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    real_name: Mapped[str] = mapped_column(String(100), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=AdminUserStatus.ACTIVE)
    # 角色/数据权限：只能由管理员管理界面写入，登录流程只读不写。
    role_codes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    data_scope: Mapped[str] = mapped_column(String(50), nullable=False, default="SELF")
    region_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    region_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    department_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
    # 索引通过下方 __table_args__ 的显式 Index() 声明，此处不再重复加 index=True
    enterprise_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
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
    # 索引通过下方 __table_args__ 的显式 Index() 声明，此处不再重复加 index=True
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
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
