import json
from typing import Protocol

from openai import OpenAI, OpenAIError

from app.config import settings
from app.exceptions import AiServiceError
from app.schemas import AiAnalysis

SYSTEM_PROMPT = """You analyze customer-service conversation transcripts.
Return JSON matching the schema:
- summary: 2-3 sentence neutral summary
- sentimentLabel: one of positive|neutral|negative (overall customer sentiment)
- sentimentScore: float in [-1.0, 1.0]
- keyTopics: 3-6 short topic tags, lowercase"""

RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "sentimentLabel", "sentimentScore", "keyTopics"],
    "properties": {
        "summary": {"type": "string"},
        "sentimentLabel": {"type": "string", "enum": ["positive", "neutral", "negative"]},
        "sentimentScore": {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "keyTopics": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        },
    },
}


class AiClient(Protocol):
    def analyze(self, transcript: str) -> AiAnalysis: ...


class OpenAiAnalysisService:
    def __init__(self, client: OpenAI, model: str = settings.openaiModel) -> None:
        self._client = client
        self._model = model

    def analyze(self, transcript: str) -> AiAnalysis:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": transcript},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "ConversationAnalysis",
                        "schema": RESPONSE_SCHEMA,
                        "strict": True,
                    },
                },
                temperature=0,
            )
            content = response.choices[0].message.content
            if not content:
                raise AiServiceError("Empty response from model")
            payload = json.loads(content)
            return AiAnalysis.model_validate(payload)
        except OpenAIError as exc:
            raise AiServiceError(str(exc)) from exc
        except (json.JSONDecodeError, ValueError) as exc:
            raise AiServiceError(f"Malformed model response: {exc}") from exc


def buildAiService() -> OpenAiAnalysisService:
    client = OpenAI(api_key=settings.openaiApiKey)
    return OpenAiAnalysisService(client)
