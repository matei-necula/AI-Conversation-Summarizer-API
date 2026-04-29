import json
from unittest.mock import MagicMock

import pytest
from openai import OpenAIError

from app.exceptions import AiServiceError
from app.services.aiService import OpenAiAnalysisService


def makeOpenAiResponse(content: str | None) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message = MagicMock()
    response.choices[0].message.content = content
    return response


def test_analyzeReturnsParsedAnalysis():
    payload = {
        "summary": "Customer requested a refund.",
        "sentimentLabel": "negative",
        "sentimentScore": -0.4,
        "keyTopics": ["refund", "billing"],
    }
    fakeClient = MagicMock()
    fakeClient.chat.completions.create.return_value = makeOpenAiResponse(json.dumps(payload))

    svc = OpenAiAnalysisService(fakeClient, model="gpt-test")
    result = svc.analyze("Hello, I want a refund.")

    assert result.summary == "Customer requested a refund."
    assert result.sentimentLabel == "negative"
    assert result.sentimentScore == -0.4
    assert result.keyTopics == ["refund", "billing"]


def test_analyzeRaisesOnOpenAiError():
    fakeClient = MagicMock()
    fakeClient.chat.completions.create.side_effect = OpenAIError("boom")
    svc = OpenAiAnalysisService(fakeClient)
    with pytest.raises(AiServiceError):
        svc.analyze("transcript")


def test_analyzeRaisesOnMalformedJson():
    fakeClient = MagicMock()
    fakeClient.chat.completions.create.return_value = makeOpenAiResponse("not-json")
    svc = OpenAiAnalysisService(fakeClient)
    with pytest.raises(AiServiceError):
        svc.analyze("transcript")


def test_analyzeRaisesOnEmptyContent():
    fakeClient = MagicMock()
    fakeClient.chat.completions.create.return_value = makeOpenAiResponse(None)
    svc = OpenAiAnalysisService(fakeClient)
    with pytest.raises(AiServiceError):
        svc.analyze("transcript")


def test_analyzeRaisesOnSchemaMismatch():
    fakeClient = MagicMock()
    fakeClient.chat.completions.create.return_value = makeOpenAiResponse(
        json.dumps({"summary": "ok"})
    )
    svc = OpenAiAnalysisService(fakeClient)
    with pytest.raises(AiServiceError):
        svc.analyze("transcript")
