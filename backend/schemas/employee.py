from __future__ import annotations
from typing import Optional

import uuid
from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    name: str
    email: str
    department: Optional[str] = None
    company: Optional[str] = None


class EmployeeResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    department: Optional[str]
    company: Optional[str]
    created_at: str

    model_config = {"from_attributes": True}
