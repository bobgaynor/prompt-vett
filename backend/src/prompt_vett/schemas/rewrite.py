from pydantic import BaseModel, Field


class RewriteResult(BaseModel):
    improved_prompt: str = Field(min_length=1)
    change_summary: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)
