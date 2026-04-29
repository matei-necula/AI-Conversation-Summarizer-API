from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ConversationNotFound(Exception):
    pass


class AiServiceError(Exception):
    pass


def registerExceptionHandlers(app: FastAPI) -> None:
    @app.exception_handler(ConversationNotFound)
    async def conversationNotFoundHandler(_: Request, exc: ConversationNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Conversation not found"})

    @app.exception_handler(AiServiceError)
    async def aiServiceErrorHandler(_: Request, exc: AiServiceError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": f"AI service error: {exc}"})
