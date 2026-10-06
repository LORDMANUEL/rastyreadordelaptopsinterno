from pydantic import BaseModel, Field


class SoftwareCatalogCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    approved_version: str | None = Field(default=None, max_length=120)
    policy: str = Field(pattern=r"^(ALLOWED|REQUIRED|BLOCKED)$")


class SoftwareCatalogUpdate(BaseModel):
    publisher: str | None = Field(default=None, max_length=255)
    approved_version: str | None = Field(default=None, max_length=120)
    policy: str | None = Field(default=None, pattern=r"^(ALLOWED|REQUIRED|BLOCKED)$")


class DeviceSoftwareAssignmentCreate(BaseModel):
    catalog_id: str
    desired_state: str = Field(pattern=r"^(REQUIRED|ABSENT)$")
