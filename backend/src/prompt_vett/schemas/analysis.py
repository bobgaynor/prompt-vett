from typing import Literal

from pydantic import BaseModel, Field


class DimensionAnalysis(BaseModel):
    score: int = Field(ge=0, le=10)
    findings: list[str]
    severity: Literal["low", "medium", "high"]


class AnalysisReport(BaseModel):
    quality: DimensionAnalysis
    consistency: DimensionAnalysis
    injection_resistance: DimensionAnalysis
    edge_cases: DimensionAnalysis
