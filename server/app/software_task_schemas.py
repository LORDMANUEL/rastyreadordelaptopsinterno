from pydantic import BaseModel, Field


class SoftwareTaskCreate(BaseModel):
    catalog_id: str
    action: str = Field(pattern=r"^(INSTALL|UNINSTALL)$")


class SoftwareTaskResult(BaseModel):
    status: str = Field(pattern=r"^(SUCCEEDED|FAILED)$")
    detail: str | None = Field(default=None, max_length=2000)
