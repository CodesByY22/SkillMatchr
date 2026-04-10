from __future__ import annotations
from typing import Optional, List

import uuid
from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None
    field_of_study: Optional[str] = None


class ExperienceEntry(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class ProjectEntry(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class CertificationEntry(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[str] = None


class PublicationEntry(BaseModel):
    title: Optional[str] = None
    publisher_or_conference: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None


class ParsedResume(BaseModel):
    """Schema for structured data extracted from a resume by Gemini."""

    full_name: Optional[str] = Field(default=None, description="Candidate's full name")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="City, State or Country")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    current_title: Optional[str] = Field(default=None, description="Most recent job title")
    years_experience: Optional[float] = Field(
        default=None,
        description="Total years of professional experience as a number",
    )
    summary: Optional[str] = Field(
        default=None,
        description="A 2-3 sentence professional summary of the candidate",
    )
    skills: List[str] = Field(
        default_factory=list,
        description="List of technical and professional skills",
    )
    education: List[EducationEntry] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    publications: List[PublicationEntry] = Field(default_factory=list)
    confidence_score: float = Field(
        default=0.0,
        description="Confidence in extraction quality from 0.0 to 1.0",
    )


class UploadResponse(BaseModel):
    candidate_id: uuid.UUID
    status: str
    parsed_data: ParsedResume
