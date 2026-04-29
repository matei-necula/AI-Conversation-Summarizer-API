from fastapi import FastAPI

from app.exceptions import registerExceptionHandlers
from app.routers import conversations


def createApp() -> FastAPI:
    app = FastAPI(title="AI Conversation Summarizer", version="0.1.0")
    app.include_router(conversations.router)
    registerExceptionHandlers(app)

    @app.get("/health", tags=["meta"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = createApp()
