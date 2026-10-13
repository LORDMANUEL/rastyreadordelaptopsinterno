from datetime import date, datetime
from decimal import Decimal

class EnrollRequest(BaseModel):
    enrollment_token: str
    hostname: str = Field(min_length=1, max_length=255)
    serial: str | None = None
    platform: str = "windows"
    os_version: str | None = None
    architecture: str | None = None
    agent_version: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    hardware_uuid: str | None = None


class EnrollResponse(BaseModel):
    device_id: str
    device_token: str
    heartbeat_seconds: int = 300


class HeartbeatRequest(BaseModel):
    username: str | None = None
    lan_ip: str | None = None
    hostname: str | None = None
    serial: str | None = None
    os_version: str | None = None
    architecture: str | None = None
    agent_version: str | None = None
    wifi_ssid: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    hardware_uuid: str | None = None
    battery_percent: int | None = Field(default=None, ge=0, le=100)
    bitlocker_status: str | None = None
    tpm_status: str | None = None
    antivirus_status: str | None = None


class DeviceUpdate(BaseModel):
    asset_tag: str | None = Field(default=None, max_length=100)
    branch: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=120)
    assigned_to: str | None = Field(default=None, max_length=255)
    asset_status: str | None = Field(
        default=None,
        pattern=r"^(ACTIVE|IN_REPAIR|STORAGE|RETURNED|RETIRED)$",
    )
    physical_condition: str | None = Field(
        default=None,
        pattern=r"^(GOOD|FAIR|POOR|DAMAGED)$",
    )
    ownership_type: str | None = Field(
        default=None,
        pattern=r"^(OWNED|LEASED|OTHER)$",
    )
    lease_contract: str | None = Field(default=None, max_length=160)
    provider: str | None = Field(default=None, max_length=180)
    acquisition_date: date | None = None
    assignment_date: date | None = None
    acquisition_cost: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    notes: str | None = Field(default=None, max_length=4000)
    last_audit_at: datetime | None = None


class LostModeUpdate(BaseModel):
    enabled: bool
    reason: str = Field(min_length=3, max_length=500)


class DeviceAuthRevoke(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
