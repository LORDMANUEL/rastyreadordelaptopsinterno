from pydantic import BaseModel, Field


class InstalledApplicationItem(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    version: str | None = Field(default=None, max_length=120)
    publisher: str | None = Field(default=None, max_length=255)
    source: str | None = Field(default=None, max_length=80)


class SoftwareInventorySync(BaseModel):
    applications: list[InstalledApplicationItem] = Field(max_length=5000)
