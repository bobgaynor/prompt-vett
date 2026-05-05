from typing import Literal

from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    test_messages: list[str] = Field(min_length=1, max_length=20)
    byok_key: str | None = None
    model: Literal["gemini-2.5-flash", "gemini-2.5-pro"]
