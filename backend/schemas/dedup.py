from __future__ import annotations
from typing import Optional

import uuid
from datetime import datetime

from pydantic import BaseModel


class CandidateSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: Optional[str]
    phone: Optional[str]
    linkedin_url: Optional[str]
    location: Optional[str]
    current_title: Optional[str]
    years_experience: Optional[float]
    skills: Optional[list]
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DedupQueueItem(BaseModel):
    id: uuid.UUID
    candidate_a: CandidateSummary
    candidate_b: CandidateSummary
    composite_score: float
    score_breakdown: Optional[dict]
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DedupQueueListItem(BaseModel):
    id: uuid.UUID
    candidate_a_id: uuid.UUID
    candidate_a_name: str
    candidate_b_id: uuid.UUID
    candidate_b_name: str
    composite_score: float
    status: str
    created_at: datetime


class MergeRequest(BaseModel):
    field_overrides: Optional[dict] = None


class DedupActionResponse(BaseModel):
    status: str
    message: str
    candidate_id: Optional[uuid.UUID] = None
