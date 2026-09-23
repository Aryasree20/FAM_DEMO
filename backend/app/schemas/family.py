"""Family and member schemas.

TODO:
- Define create, update, and read shapes for households and family members.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FamilyCreate(BaseModel):
    name: str
    timezone: str = "Asia/Kolkata"


class FamilyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    timezone: str
    created_at: datetime
    updated_at: datetime


class FamilyMemberCreate(BaseModel):
    name: str
    relationship: str
    role: str | None = None


class FamilyMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_id: UUID
    name: str
    relationship: str
    role: str | None
    created_at: datetime