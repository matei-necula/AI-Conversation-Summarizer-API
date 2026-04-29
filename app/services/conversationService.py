import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.exceptions import ConversationNotFound
from app.models import Conversation
from app.schemas import AiAnalysis


def createConversation(db: Session, transcript: str, analysis: AiAnalysis) -> Conversation:
    convo = Conversation(
        rawTranscript=transcript,
        summary=analysis.summary,
        sentimentLabel=analysis.sentimentLabel,
        sentimentScore=analysis.sentimentScore,
        keyTopics=analysis.keyTopics,
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def getConversation(db: Session, convoId: uuid.UUID) -> Conversation:
    convo = db.get(Conversation, convoId)
    if convo is None:
        raise ConversationNotFound(f"No conversation with id {convoId}")
    return convo


def listConversations(
    db: Session, limit: int = 50, offset: int = 0
) -> tuple[list[Conversation], int]:
    total = db.scalar(select(func.count()).select_from(Conversation)) or 0
    stmt = (
        select(Conversation)
        .order_by(Conversation.createdAt.desc(), Conversation.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(db.execute(stmt).scalars())
    return items, total


def searchConversations(db: Session, query: str) -> tuple[list[Conversation], int]:
    pattern = f"%{query}%"
    stmt = (
        select(Conversation)
        .where(
            or_(
                Conversation.rawTranscript.ilike(pattern),
                Conversation.summary.ilike(pattern),
            )
        )
        .order_by(Conversation.createdAt.desc(), Conversation.id.desc())
    )
    items = list(db.execute(stmt).scalars())
    return items, len(items)
