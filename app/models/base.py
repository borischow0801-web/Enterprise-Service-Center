from datetime import datetime
from sqlalchemy import DateTime, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_flag: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
