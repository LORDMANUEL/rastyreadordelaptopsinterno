from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SoftwareCatalogItem(Base):
    __tablename__ = "software_catalog"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), index=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    policy: Mapped[str] = mapped_column(String(24), index=True)
    created_by: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeviceSoftwareAssignment(Base):
    __tablename__ = "device_software_assignments"
    __table_args__ = (
        UniqueConstraint("device_id", "catalog_id", name="uq_device_software_assignment"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    device_id: Mapped[str] = mapped_column(String(36), index=True)
    catalog_id: Mapped[str] = mapped_column(String(36), index=True)
    desired_state: Mapped[str] = mapped_column(String(24), index=True)
    assigned_by: Mapped[str] = mapped_column(String(120))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
