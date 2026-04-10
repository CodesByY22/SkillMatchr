from __future__ import annotations
from typing import Optional, List

import uuid
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class SearchResultItem(BaseModel):
    candidate_id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    skills: Optional[list] = None
    summary: Optional[str] = None
    source: Optional[str] = None
    confidence_score: Optional[float] = None
    similarity_score: float


class SearchResponse(BaseModel):
    query: str
    intent: dict
    total: int
    results: List[SearchResultItem]
