import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ.setdefault(
    "databaseUrl",
    os.environ.get(
        "databaseUrl",
        "postgresql+psycopg://postgres:postgres@localhost:5432/convsummarizer_test",
    ),
)
os.environ.setdefault("openaiApiKey", "test-key")

from app.database import Base, getDb  # noqa: E402
from app.main import app  # noqa: E402
from app.routers.conversations import getAiService  # noqa: E402
from app.schemas import AiAnalysis  # noqa: E402


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(os.environ["databaseUrl"], future=True)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture()
def dbSession(engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    TestingSession = sessionmaker(bind=connection, autoflush=False, autocommit=False, future=True)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


class StubAiService:
    def __init__(self, analysis: AiAnalysis | None = None, raises: Exception | None = None):
        self._analysis = analysis or AiAnalysis(
            summary="Customer asked about a refund and was helped by the agent.",
            sentimentLabel="neutral",
            sentimentScore=0.1,
            keyTopics=["refund", "billing"],
        )
        self._raises = raises

    def analyze(self, transcript: str) -> AiAnalysis:
        if self._raises is not None:
            raise self._raises
        return self._analysis


@pytest.fixture()
def stubAi() -> StubAiService:
    return StubAiService()


@pytest.fixture()
def client(dbSession, stubAi) -> Iterator[TestClient]:
    def overrideDb():
        yield dbSession

    def overrideAi():
        return stubAi

    app.dependency_overrides[getDb] = overrideDb
    app.dependency_overrides[getAiService] = overrideAi
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def clientFactory(dbSession):
    def make(aiService) -> TestClient:
        def overrideDb():
            yield dbSession

        def overrideAi():
            return aiService

        app.dependency_overrides[getDb] = overrideDb
        app.dependency_overrides[getAiService] = overrideAi
        return TestClient(app)

    yield make
    app.dependency_overrides.clear()
