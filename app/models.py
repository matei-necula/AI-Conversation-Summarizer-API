import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcNow() -> datetime:
    return datetime.now(timezone.utc)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    rawTranscript: Mapped[str] = mapped_column("rawTranscript", Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    sentimentLabel: Mapped[str] = mapped_column("sentimentLabel", String(16), nullable=False)
    sentimentScore: Mapped[float] = mapped_column("sentimentScore", Float, nullable=False)
    keyTopics: Mapped[list[str]] = mapped_column("keyTopics", JSONB, nullable=False)
    createdAt: Mapped[datetime] = mapped_column(
        "createdAt",
        DateTime(timezone=True),
        nullable=False,
        default=utcNow,
    )
