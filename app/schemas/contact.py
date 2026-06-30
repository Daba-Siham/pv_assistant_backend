from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


ContactMessageStatus = Literal["new", "read", "archived"]


class ContactMessageCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str | None = Field(default=None, max_length=255)
    message: str = Field(..., min_length=1)


class ContactMessageRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    subject: str | None = None
    message: str
    status: ContactMessageStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactMessageUpdateStatus(BaseModel):
    status: ContactMessageStatus
