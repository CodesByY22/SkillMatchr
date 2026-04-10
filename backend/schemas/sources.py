from __future__ import annotations
from typing import Optional, List

import uuid
from pydantic import BaseModel


class SyncResultItem(BaseModel):
    name: Optional[str] = None
    filename: Optional[str] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    candidate_id: Optional[uuid.UUID] = None
    status: str


class SyncResponse(BaseModel):
    source: str
    total: int
    results: List[SyncResultItem]
