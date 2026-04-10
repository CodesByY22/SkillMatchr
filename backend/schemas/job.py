from __future__ import annotations
from typing import Optional, List

import uuid
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str
    company: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: str = "full_time"
    experience_required: Optional[float] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    skills_required: List[str] = Field(default_factory=list)
    job_description: Optional[str] = None


class JobResponse(BaseModel):
    id: uuid.UUID
    title: str
    company: Optional[str]
    department: Optional[str]
    location: Optional[str]
    employment_type: Optional[str]
    experience_required: Optional[float]
    salary_min: Optional[float]
    salary_max: Optional[float]
    skills_required: Optional[List[str]]
    job_description: Optional[str]
    status: str
    created_by: Optional[uuid.UUID]
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MatchRequest(BaseModel):
    top_k: int = Field(default=20, ge=1, le=500)
    threshold: float = Field(default=0.20, ge=0.0, le=1.0, description="Configurable matching threshold")


class MatchScoreBreakdown(BaseModel):
    semantic_similarity: float
    skill_match: float
    experience_match: float
    title_relevance: float


class MatchResultItem(BaseModel):
    candidate_id: str
    full_name: str
    email: Optional[str]
    location: Optional[str]
    current_title: Optional[str]
    years_experience: Optional[float]
    skills: Optional[List[str]]
    missing_skills: List[str] = Field(default_factory=list)
    upskill_suggestions: List[str] = Field(default_factory=list)
    composite_score: float
    breakdown: MatchScoreBreakdown


class MatchResponse(BaseModel):
    job_id: str
    job_title: str
    total: int
    results: List[MatchResultItem]


class CompareRequest(BaseModel):
    candidate_ids: List[str]


class CompareCandidate(BaseModel):
    candidate_id: str
    full_name: str
    email: Optional[str]
    location: Optional[str]
    current_title: Optional[str]
    years_experience: Optional[float]
    skills: Optional[List[str]]
    education: Optional[List[dict]]
    experience: Optional[List[dict]]
    semantic_match: float
    skill_overlap: float
    experience_score: float
    overall_score: float


class CompareResponse(BaseModel):
    job_id: str
    job_title: str
    candidates: List[CompareCandidate]
