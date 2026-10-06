from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EnrollmentCode(Base):
    __tablename__ = "enrollment_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str | None] = mapped_column(String(160), nullable=True)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(32), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
