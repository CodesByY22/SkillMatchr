from __future__ import annotations
from typing import Optional, List

import uuid
from datetime import datetime
from pydantic import BaseModel


class ActivityLogItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    action: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    metadata: Optional[dict] = None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    total: int
    results: List[ActivityLogItem]
