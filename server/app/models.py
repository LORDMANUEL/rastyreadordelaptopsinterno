from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    serial: Mapped[str | None] = mapped_column(String(255), index=True, nullable=True)
    platform: Mapped[str] = mapped_column(String(32), default="windows")
    os_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    architecture: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    auth_issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auth_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auth_revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auth_generation: Mapped[int] = mapped_column(Integer, default=0)

    asset_tag: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(255), nullable=True)

    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lan_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    public_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wifi_ssid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geo_country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    geo_country_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    geo_region_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    geo_city_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    geo_accuracy_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geo_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    manufacturer: Mapped[str | None] = mapped_column(String(120), nullable=True)
    model: Mapped[str | None] = mapped_column(String(160), nullable=True)
    hardware_uuid: Mapped[str | None] = mapped_column(String(120), nullable=True)
    battery_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bitlocker_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    tpm_status: Mapped[str | None] = mapped_column(String(120), nullable=True)
    antivirus_status: Mapped[str | None] = mapped_column(Text, nullable=True)

    lost_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    device_id: Mapped[str | None] = mapped_column(String(36), index=True, nullable=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DeviceObservation(Base):
    __tablename__ = "device_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    device_id: Mapped[str] = mapped_column(String(36), index=True)
    reason: Mapped[str] = mapped_column(String(48), index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lan_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    public_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    wifi_ssid: Mapped[str | None] = mapped_column(String(255), nullable=True)
    geo_country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    geo_region_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    geo_city_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    geo_accuracy_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    battery_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
