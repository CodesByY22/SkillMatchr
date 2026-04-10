from __future__ import annotations
from typing import Optional, List

import uuid
from datetime import datetime
from pydantic import BaseModel


class CandidateListItem(BaseModel):
    id: uuid.UUID
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    source: str
    ingestion_status: str
    confidence_score: Optional[float] = None
    created_at: datetime


class CandidateDetail(CandidateListItem):
    linkedin_url: Optional[str] = None
    skills: Optional[list] = None
    education: Optional[list] = None
    experience: Optional[list] = None
    certifications: Optional[list] = None
    projects: Optional[list] = None
    publications: Optional[list] = None
    summary: Optional[str] = None
    raw_text: Optional[str] = None
    source_ref: Optional[str] = None
    ingestion_error: Optional[str] = None
    updated_at: datetime


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    current_title: Optional[str] = None
    years_experience: Optional[float] = None
    linkedin_url: Optional[str] = None
    skills: Optional[list] = None
    education: Optional[list] = None
    experience: Optional[list] = None
    summary: Optional[str] = None
    ingestion_status: Optional[str] = None


class CandidateListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    results: List[CandidateListItem]
