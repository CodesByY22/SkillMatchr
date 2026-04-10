from __future__ import annotations
"""Pydantic schemas for v1 API endpoints."""


import uuid
from pydantic import BaseModel, Field
from typing import Any, Optional, List


# ── Error Response ────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None


# ── Parse Endpoints ───────────────────────────────────────────────────

class ParseResponse(BaseModel):
    candidate_id: str
    status: str
    parsed_data: dict
    skill_profile: Optional[dict] = None
    pipeline_run_id: Optional[str] = None
    latency_ms: Optional[int] = None

    model_config = {"json_schema_extra": {
        "example": {
            "candidate_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "completed",
            "parsed_data": {
                "full_name": "John Doe",
                "email": "john@example.com",
                "skills": ["Python", "React", "PostgreSQL"],
            },
            "skill_profile": {
                "total_canonical": 3,
                "total_inferred": 2,
            },
            "pipeline_run_id": "run-abc123",
            "latency_ms": 4500,
        }
    }}


class BatchParseRequest(BaseModel):
    webhook_url: Optional[str] = Field(
        default=None,
        description="URL to receive callback when batch processing completes",
    )


class BatchJobStatus(BaseModel):
    job_id: str
    status: str  # queued | processing | completed | failed
    total: int
    processed: int
    succeeded: int
    failed: int
    results: Optional[List[dict]] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class BatchParseResponse(BaseModel):
    job_id: str
    status: str
    total: int
    message: str


# ── Skill Profile ────────────────────────────────────────────────────

class SkillEntry(BaseModel):
    canonical_name: str
    original_name: Optional[str] = None
    match_type: Optional[str] = None  # exact | synonym | fuzzy | unknown
    proficiency: Optional[str] = None  # expert | advanced | intermediate | beginner
    estimated_years: Optional[float] = None
    category: Optional[str] = None

class InferredSkill(BaseModel):
    canonical_name: str
    inferred_from: str
    confidence: float

class SkillProfileResponse(BaseModel):
    candidate_id: str
    candidate_name: str
    skills: List[SkillEntry]
    inferred_skills: List[InferredSkill]
    emerging_skills: List[str]
    total_canonical: int
    total_inferred: int
    total_emerging: int


# ── Match Endpoints ──────────────────────────────────────────────────

class MatchRequestBody(BaseModel):
    candidate_id: str = Field(..., description="UUID of the candidate to match")
    job_description: str = Field(..., description="Full text of the job description")
    job_title: str = Field(..., description="Job title")
    skills_required: List[str] = Field(default_factory=list)
    skills_nice_to_have: List[str] = Field(default_factory=list)
    experience_required: Optional[float] = None
    match_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Minimum match score threshold (0=broad, 1=strict)",
    )


class SkillGap(BaseModel):
    skill: str
    importance: str  # required | nice_to_have
    upskilling_suggestions: List[str]


class MatchResultDetail(BaseModel):
    candidate_id: str
    candidate_name: str
    overall_score: float
    breakdown: dict
    matched_skills: List[str]
    missing_skills: List[str]
    gap_analysis: List[SkillGap]
    recommendation: str  # strong_match | good_match | partial_match | weak_match


class MatchResponse(BaseModel):
    job_title: str
    candidate: MatchResultDetail


# ── Taxonomy Endpoints ───────────────────────────────────────────────

class TaxonomyCategoryResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    parent_id: Optional[str]
    skill_count: int = 0
    children: List[TaxonomyCategoryResponse] = []

    model_config = {"from_attributes": True}


class TaxonomySkillResponse(BaseModel):
    id: str
    canonical_name: str
    category: Optional[str]
    subcategory: Optional[str]
    skill_type: str
    synonyms: List[str] = []


class TaxonomySearchResponse(BaseModel):
    query: str
    total: int
    categories: List[TaxonomyCategoryResponse]
    skills: List[TaxonomySkillResponse]


# ── Webhook ──────────────────────────────────────────────────────────

class WebhookSubscriptionCreate(BaseModel):
    url: str
    events: List[str] = Field(
        default=["parse.completed", "batch.completed", "match.completed"],
        description="Events to subscribe to",
    )
    secret: Optional[str] = Field(
        default=None,
        description="Secret to sign webhook payloads for verification",
    )


class WebhookSubscriptionResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: str


# ── API Key Management ───────────────────────────────────────────────

class ApiKeyCreateRequest(BaseModel):
    name: str = Field(..., description="Friendly name for the API key")
    rate_limit: int = Field(default=100, ge=10, le=1000)


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    api_key: str  # Only shown once at creation time
    rate_limit: int
    message: str = "Store this API key securely. It will not be shown again."


class ApiKeyListItem(BaseModel):
    id: str
    name: str
    rate_limit: int
    is_active: bool
    last_used_at: Optional[str]
    created_at: str


# ── Pipeline Observability ───────────────────────────────────────────

class AgentTraceResponse(BaseModel):
    agent_name: str
    status: str
    latency_ms: Optional[int]
    quality_score: Optional[float]
    error_message: Optional[str]
    retry_count: Optional[int]


class PipelineRunResponse(BaseModel):
    run_id: str
    status: str
    total_latency_ms: int
    candidate_id: Optional[str]
    traces: List[AgentTraceResponse]


# ── Evaluation Metrics ───────────────────────────────────────────────

class EvaluationMetrics(BaseModel):
    parsing_accuracy: dict = Field(
        default_factory=dict,
        description="Field-level F1-scores for resume parsing",
    )
    normalization_precision: dict = Field(
        default_factory=dict,
        description="Correct canonical mapping rates",
    )
    matching_quality: dict = Field(
        default_factory=dict,
        description="NDCG and correlation with expert rankings",
    )
    api_completeness: dict = Field(
        default_factory=dict,
        description="Endpoint coverage and error handling metrics",
    )
    orchestration_reliability: dict = Field(
        default_factory=dict,
        description="Success rate under concurrent load",
    )
    latency: dict = Field(
        default_factory=dict,
        description="End-to-end processing time metrics",
    )
