import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import getDb
from app.schemas import ConversationCreate, ConversationList, ConversationOut
from app.services import conversationService
from app.services.aiService import AiClient, buildAiService

router = APIRouter(prefix="/conversations", tags=["conversations"])


def getAiService() -> AiClient:
    return buildAiService()


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def submitConversation(
    payload: ConversationCreate,
    db: Session = Depends(getDb),
    aiService: AiClient = Depends(getAiService),
) -> ConversationOut:
    analysis = aiService.analyze(payload.rawTranscript)
    convo = conversationService.createConversation(db, payload.rawTranscript, analysis)
    return ConversationOut.model_validate(convo)


@router.get("", response_model=ConversationList)
def listAll(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(getDb),
) -> ConversationList:
    items, total = conversationService.listConversations(db, limit=limit, offset=offset)
    return ConversationList(
        items=[ConversationOut.model_validate(c) for c in items],
        total=total,
    )


@router.get("/search", response_model=ConversationList)
def searchAll(
    q: str = Query(..., min_length=1),
    db: Session = Depends(getDb),
) -> ConversationList:
    items, total = conversationService.searchConversations(db, q)
    return ConversationList(
        items=[ConversationOut.model_validate(c) for c in items],
        total=total,
    )


@router.get("/{convoId}", response_model=ConversationOut)
def getOne(
    convoId: uuid.UUID,
    db: Session = Depends(getDb),
) -> ConversationOut:
    convo = conversationService.getConversation(db, convoId)
    return ConversationOut.model_validate(convo)
