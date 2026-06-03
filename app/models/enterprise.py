from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class Enterprise(TimestampMixin, Base):
    __tablename__ = "enterprise"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    enterprise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    credit_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    legal_person_name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_person_id_no: Mapped[str] = mapped_column(String(128), nullable=False)
    legal_person_mobile: Mapped[str] = mapped_column(String(64), nullable=False)
    industry_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    industry_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    region_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    auth_source: Mapped[str] = mapped_column(String(50), nullable=False, default="MOCK")
    auth_account_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    meeting_no_show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    meeting_booking_disabled: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    last_login_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_enterprise_region_code", "region_code"),
        Index("ix_enterprise_auth_account_id", "auth_account_id"),
    )
