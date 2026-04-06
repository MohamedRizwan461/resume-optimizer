from pydantic import BaseModel
from typing import List


class OptimizeResponse(BaseModel):
    original_text: str
    optimized_text: str
    match_score: int
    missing_keywords: List[str]
    present_keywords: List[str]
    ats_issues: List[str]
    changes_made: List[str]


class HealthResponse(BaseModel):
    status: str
