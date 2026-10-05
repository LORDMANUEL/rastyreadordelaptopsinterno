from pydantic import BaseModel, Field


class EnrollRequest(BaseModel):
    enrollment_token: str
    hostname: str = Field(min_length=1, max_length=255)
    serial: str | None = None
    platform: str = "windows"
    os_version: str | None = None
    architecture: str | None = None
    agent_version: str | None = None


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


class DeviceUpdate(BaseModel):
    asset_tag: str | None = None
    branch: str | None = None
    assigned_to: str | None = None


class LostModeUpdate(BaseModel):
    enabled: bool
    reason: str = Field(min_length=3, max_length=500)
