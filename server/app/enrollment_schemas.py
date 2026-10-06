from pydantic import BaseModel, Field


class EnrollmentCodeCreate(BaseModel):
    label: str | None = Field(default=None, max_length=160)
    branch: str | None = Field(default=None, max_length=100)
    platform: str | None = Field(default=None, max_length=32)
    expires_minutes: int = Field(default=60, ge=5, le=10080)
    max_uses: int = Field(default=1, ge=1, le=100)


class EnrollmentCodeRevoke(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
