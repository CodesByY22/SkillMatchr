from __future__ import annotations
from typing import Optional, List

import uuid
from pydantic import BaseModel, Field


class ReferralCreate(BaseModel):
    employee_id: str
    job_id: str
    candidate_name: str
    candidate_email: str
    candidate_phone: Optional[str] = None
    candidate_location: Optional[str] = None
    candidate_title: Optional[str] = None
    candidate_id: Optional[str] = None  # If candidate already exists
    notes: Optional[str] = None


class ReferralResponse(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    candidate_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    notes: Optional[str]
    referred_at: str
    employee_name: Optional[str] = None
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None

    model_config = {"from_attributes": True}


class ReferralListResponse(BaseModel):
    total: int
    results: List[ReferralResponse]


class ReferralAnalytics(BaseModel):
    total_referrals: int
    total_hires: int
    success_rate: float
    top_referrers: List[dict]
    department_breakdown: List[dict]
    status_breakdown: List[dict]
