from __future__ import annotations
from typing import Optional, List

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ShortlistCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class ShortlistCandidateAdd(BaseModel):
    candidate_id: uuid.UUID
    notes: Optional[str] = None


class ShortlistCandidateItem(BaseModel):
    id: uuid.UUID
    candidate_id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    current_title: Optional[str] = None
    notes: Optional[str] = None
    added_at: datetime


class ShortlistResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    created_by: uuid.UUID
    candidate_count: int = 0
    created_at: datetime
    updated_at: datetime


class ShortlistDetailResponse(ShortlistResponse):
    candidates: List[ShortlistCandidateItem] = []
