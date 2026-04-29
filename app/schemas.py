import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SentimentLabel = Literal["positive", "neutral", "negative"]


class ConversationCreate(BaseModel):
    rawTranscript: str = Field(..., min_length=1)

    @field_validator("rawTranscript")
    @classmethod
    def notWhitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("rawTranscript must not be empty or whitespace")
        return value


class AiAnalysis(BaseModel):
    summary: str
    sentimentLabel: SentimentLabel
    sentimentScore: float = Field(..., ge=-1.0, le=1.0)
    keyTopics: list[str]


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rawTranscript: str
    summary: str
    sentimentLabel: SentimentLabel
    sentimentScore: float
    keyTopics: list[str]
    createdAt: datetime


class ConversationList(BaseModel):
    items: list[ConversationOut]
    total: int
