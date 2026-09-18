from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Enterprise(TimestampMixin, Base):
    """企业主体/业务档案。与登录身份（EnterpriseIdentity）解耦：本表只承载企业的业务数据，
    不关心该企业当前有哪些登录方式（本地账号密码 / 省统一身份认证 / ...）。"""

    __tablename__ = "enterprise"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    # 法人三要素仅由权威来源（省统一身份认证 / 管理端核实登记）确认后才会有值；
    # 企业自主注册（LOCAL）阶段收集的是"联系人"，不等同于法人，因此这里必须允许为空。
    legal_person_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    legal_person_id_no: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    legal_person_mobile: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    industry_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    industry_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # 索引通过下方 __table_args__ 中的显式 Index() 声明，此处不再重复加 index=True
    # （原代码两处重复声明会在 SQLite create_all/测试环境下报 "index already exists"；
    # 对已用 Alembic 管理的 MySQL 无影响，因为实际索引一直只由迁移脚本创建）。
    region_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    region_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    auth_source: Mapped[str] = mapped_column(String(50), nullable=False, default="MOCK")
    auth_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meeting_no_show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meeting_booking_disabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_enterprise_region_code", "region_code"),
        Index("ix_enterprise_auth_account_id", "auth_account_id"),
    )


class EnterpriseIdentityType:
    """登录身份类型。本期只真正实现 LOCAL；PROVINCIAL_SSO 为省统一身份认证预留。"""

    LOCAL = "LOCAL"
    PROVINCIAL_SSO = "PROVINCIAL_SSO"


class EnterpriseIdentityStatus:
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class EnterpriseIdentity(TimestampMixin, Base):
    """企业登录身份。一个 Enterprise 可以对应多个 EnterpriseIdentity（1:N），
    每种认证来源（LOCAL 本地账号密码 / PROVINCIAL_SSO 省统一身份认证）各自一条记录，
    互不假设对方存在，也互不覆盖。业务模块永远只通过 enterprise_id 识别企业，
    不关心也不应该关心当前请求是通过哪种 identity_type 登录得到的。"""

    __tablename__ = "enterprise_identity"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enterprise_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("enterprise.id"), nullable=False
    )
    identity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # LOCAL: 取值为统一社会信用代码；PROVINCIAL_SSO: 取值为省认证平台返回的账号唯一标识。
    identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    # 仅 LOCAL 使用；bcrypt hash，绝不存明文/可逆加密。
    credential_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_mobile: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EnterpriseIdentityStatus.ACTIVE
    )
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("identity_type", "identifier", name="uq_enterprise_identity_type_identifier"),
        Index("ix_enterprise_identity_enterprise_id", "enterprise_id"),
    )
