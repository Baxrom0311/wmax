from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ProblemItem(BaseModel):
    param: str
    label: str
    deviation: str
    current_value: float
    baseline_range: str
    severity: Literal["mild", "moderate", "severe"]
    explanation: str


class PrognosisInfo(BaseModel):
    risk_level: Literal["low", "moderate", "high"]
    risk_probability_pct: int
    early_warning_hours: int
    summary: str
    recommendation: str
    evidence_citations: list[str] = []
    confidence_score: float = 0.92
    uncertainty_note: str | None = None


class TwinPrognosisInfo(PrognosisInfo):
    primary_concern: str | None = None
    contributing_factors: list[str] = []
    medication_considerations: str | None = None
    relative_message_key: str | None = None


class NurseChecklistItem(BaseModel):
    id: str
    task: str
    priority: Literal["low", "medium", "high", "critical"]
    category: Literal["vitals", "medication", "device", "observation"]
    completed: bool = False


class NurseHandoverSBAR(BaseModel):
    situation: str
    background: str
    assessment: str
    recommendation: str
    shift_checklist: list[NurseChecklistItem] = []
    clinical_urgency: Literal["routine", "urgent", "critical"]
    vital_flags: list[str] = []
    confidence_score: float = 0.95
    evidence_citations: list[str] = []
    generated_at: str | None = None
