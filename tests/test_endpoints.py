def test_postCreatesConversation(client):
    response = client.post(
        "/conversations",
        json={"rawTranscript": "Customer: I want a refund.\nAgent: Sure."},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["rawTranscript"].startswith("Customer:")
    assert body["summary"]
    assert body["sentimentLabel"] in ("positive", "neutral", "negative")
    assert -1.0 <= body["sentimentScore"] <= 1.0
    assert isinstance(body["keyTopics"], list)
    assert body["createdAt"]


def test_getByIdReturnsConversation(client):
    created = client.post(
        "/conversations", json={"rawTranscript": "Hello there"}
    ).json()
    response = client.get(f"/conversations/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_listReturnsOrderedByCreatedAtDesc(client):
    import time

    first = client.post("/conversations", json={"rawTranscript": "first call"}).json()
    time.sleep(0.01)
    second = client.post("/conversations", json={"rawTranscript": "second call"}).json()

    response = client.get("/conversations")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 2
    ids = [item["id"] for item in body["items"]]
    assert ids.index(second["id"]) < ids.index(first["id"])


def test_listPagination(client):
    for i in range(3):
        client.post("/conversations", json={"rawTranscript": f"call number {i}"})

    response = client.get("/conversations?limit=2&offset=0")
    body = response.json()
    assert len(body["items"]) == 2


def test_searchMatchesTranscript(client):
    client.post("/conversations", json={"rawTranscript": "I lost my password"})
    client.post("/conversations", json={"rawTranscript": "delivery question"})

    response = client.get("/conversations/search?q=password")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert "password" in body["items"][0]["rawTranscript"].lower()


def test_searchIsCaseInsensitive(client):
    client.post("/conversations", json={"rawTranscript": "Refund Request"})
    response = client.get("/conversations/search?q=REFUND")
    assert response.json()["total"] == 1


def test_searchRouteDoesNotCollideWithIdRoute(client):
    response = client.get("/conversations/search?q=anything")
    assert response.status_code == 200
