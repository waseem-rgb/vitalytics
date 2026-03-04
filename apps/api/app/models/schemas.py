"""Pydantic schemas for API request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PatientInfo(BaseModel):
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., pattern="^(male|female)$")


class AnalysisRequest(BaseModel):
    patient: PatientInfo
    lab_results: dict[str, float]
    previous_results: dict[str, float] | None = None
    use_rag: bool = False


class TrendResult(BaseModel):
    direction: str
    delta: float
    percent_change: float
    rate_per_day: float
    projected_days_to_critical: float | None = None


class InterpretationResult(BaseModel):
    status: str
    value: float
    unit: str
    reference_range: dict | None = None
    plain_text: str
    severity_score: int
    flag_color: str
    trend: TrendResult | None = None
    previous_value: float | None = None


class MatchedPattern(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    interpretation: str
    harrison_ref: str
    confidence: float
    matched_criteria: str


class StagingResult(BaseModel):
    stage: str
    label: str
    color: str | None = None
    description: str


class FurtherTest(BaseModel):
    test_name: str
    rationale: str


class FurtherTestGroup(BaseModel):
    pattern_id: str
    tests: list[FurtherTest]


class ReferralResult(BaseModel):
    pattern_id: str
    specialist: str
    urgency: str
    reason: str
    when_to_refer: str | None = None


class LifestylePlan(BaseModel):
    diet: list[str] = []
    exercise: list = []
    sleep: list[str] = []
    stress: list[str] = []
    weight: list[str] | None = None
    smoking: list[str] | None = None


class Tier2Result(BaseModel):
    patterns: list[MatchedPattern]
    staging: dict[str, StagingResult] = {}


class Tier3Result(BaseModel):
    further_tests: list[FurtherTestGroup] = []
    referrals: list[ReferralResult] = []
    lifestyle: LifestylePlan | dict = {}


class RAGNarrative(BaseModel):
    narrative: str = ""
    differentials: list[str] = []
    confidence: float = 0.0
    harrison_citations: list[str] = []
    caveats: list[str] = []


class AnalysisResponse(BaseModel):
    id: str
    timestamp: str
    patient: PatientInfo
    tier1: dict[str, InterpretationResult]
    tier2: Tier2Result
    tier3: Tier3Result
    rag_narrative: RAGNarrative | None = None


class UploadResponse(BaseModel):
    parsed_results: dict[str, float]
    confidence: float
    unmatched: list[str] = []


class HealthResponse(BaseModel):
    status: str
    rag_ready: bool
