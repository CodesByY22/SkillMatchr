from __future__ import annotations
from typing import List

from pydantic import BaseModel


class SourceBreakdown(BaseModel):
    source: str
    count: int


class IngestionTrend(BaseModel):
    date: str
    count: int


class StatusBreakdown(BaseModel):
    status: str
    count: int


class ExperienceBreakdown(BaseModel):
    category: str
    count: int


class AnalyticsOverview(BaseModel):
    total_candidates: int
    total_shortlists: int
    sources: List[SourceBreakdown]
    ingestion_trends: List[IngestionTrend]
    status_breakdown: List[StatusBreakdown] = []
    experience_breakdown: List[ExperienceBreakdown] = []
