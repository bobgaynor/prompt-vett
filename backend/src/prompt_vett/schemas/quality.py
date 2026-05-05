from typing import Annotated, Literal

from pydantic import BaseModel, Field

BoundedInt = Annotated[int, Field(ge=0, le=10)]


class QualityScore(BaseModel):
    overall: BoundedInt
    dimensions: dict[str, BoundedInt]
    verdict: Literal["accept", "revise"]
    reasoning: str = Field(min_length=1)
