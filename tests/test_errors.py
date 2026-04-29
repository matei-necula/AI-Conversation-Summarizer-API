import uuid

from app.exceptions import AiServiceError
from tests.conftest import StubAiService


def test_postEmptyBody(client):
    response = client.post("/conversations", json={})
    assert response.status_code == 422


def test_postWhitespaceTranscript(client):
    response = client.post("/conversations", json={"rawTranscript": "   "})
    assert response.status_code == 422


def test_postEmptyTranscript(client):
    response = client.post("/conversations", json={"rawTranscript": ""})
    assert response.status_code == 422


def test_getUnknownIdReturns404(client):
    response = client.get(f"/conversations/{uuid.uuid4()}")
    assert response.status_code == 404


def test_getMalformedIdReturns422(client):
    response = client.get("/conversations/not-a-uuid")
    assert response.status_code == 422


def test_postReturns502WhenAiFails(clientFactory):
    failing = StubAiService(raises=AiServiceError("upstream down"))
    client = clientFactory(failing)
    response = client.post("/conversations", json={"rawTranscript": "hello"})
    assert response.status_code == 502
    assert "AI service error" in response.json()["detail"]


def test_searchMissingQReturns422(client):
    response = client.get("/conversations/search")
    assert response.status_code == 422


def test_searchEmptyQReturns422(client):
    response = client.get("/conversations/search?q=")
    assert response.status_code == 422


def test_listRejectsBadPagination(client):
    assert client.get("/conversations?limit=0").status_code == 422
    assert client.get("/conversations?offset=-1").status_code == 422
