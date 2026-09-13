import json

import httpx
import pytest

from app.plugin.food_ai.assistant import AssistantUnavailable, OpenAICompatiblePublicAssistant
from app.plugin.food_ai.schema import AssistantQuestionResult, AssistantServiceRecommendation
from app.plugin.food_ai.service import food_ai_service


def test_assistant_rejects_blank_question(test_client) -> None:
    response = test_client.post("/food-ai/assistant/questions", json={"question": "   "})

    assert response.status_code == 422
    assert "问题不能为空" in response.json()["msg"]


def test_assistant_returns_recommendations_and_disclaimer(test_client, monkeypatch) -> None:
    class FakeAssistant:
        async def answer(self, question: str, conversation_id: str | None = None) -> AssistantQuestionResult:
            assert question == "出口材料有哪些？"
            assert conversation_id is None
            return AssistantQuestionResult(
                answer="可先使用出口合规预检服务整理材料。",
                conversation_id="conversation-1",
                recommended_services=[
                    AssistantServiceRecommendation(name="出口合规预检", route="/portal/precheck")
                ],
                sources=[],
            )

    monkeypatch.setattr(food_ai_service, "assistant", FakeAssistant())
    response = test_client.post("/food-ai/assistant/questions", json={"question": "出口材料有哪些？"})

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["answer"] == "可先使用出口合规预检服务整理材料。"
    assert payload["conversation_id"] == "conversation-1"
    assert payload["recommended_services"] == [
        {"name": "出口合规预检", "route": "/portal/precheck"}
    ]
    assert payload["sources"] == []
    assert payload["disclaimer"] == "AI 生成，仅供辅助参考"


def test_assistant_returns_503_without_leaking_provider_details(test_client, monkeypatch) -> None:
    class UnavailableAssistant:
        async def answer(self, question: str, conversation_id: str | None = None) -> AssistantQuestionResult:
            raise AssistantUnavailable("provider response contained a private endpoint")

    monkeypatch.setattr(food_ai_service, "assistant", UnavailableAssistant())
    response = test_client.post("/food-ai/assistant/questions", json={"question": "如何办理？"})

    assert response.status_code == 503
    assert response.json()["msg"] == "问答模型服务未配置或暂不可用"
    assert "private endpoint" not in response.text


@pytest.mark.anyio
async def test_public_assistant_rejects_missing_server_configuration() -> None:
    assistant = OpenAICompatiblePublicAssistant(base_url="", model="", api_key="", timeout=30)

    with pytest.raises(AssistantUnavailable):
        await assistant.answer("如何办理？")

    await assistant.aclose()


@pytest.mark.anyio
async def test_public_assistant_retries_timeout_once() -> None:
    attempts = 0

    def timeout_handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("timed out", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(timeout_handler))
    assistant = OpenAICompatiblePublicAssistant(
        base_url="https://model.invalid",
        model="test-model",
        api_key="test-key",
        timeout=30,
        client=client,
    )

    with pytest.raises(AssistantUnavailable):
        await assistant.answer("如何办理？")

    assert attempts == 2
    await client.aclose()


@pytest.mark.anyio
async def test_public_assistant_filters_unapproved_routes_and_returns_no_unverified_sources() -> None:
    model_content = json.dumps(
        {
            "answer": "可使用平台现有服务进行辅助处理。",
            "recommended_services": [
                {"name": "出口合规预检", "route": "/portal/precheck"},
                {"name": "外部服务", "route": "https://example.invalid"},
            ],
        },
        ensure_ascii=False,
    )

    def success_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={"choices": [{"message": {"content": model_content}}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(success_handler))
    assistant = OpenAICompatiblePublicAssistant(
        base_url="https://model.invalid",
        model="test-model",
        api_key="test-key",
        timeout=30,
        client=client,
    )

    result = await assistant.answer("如何办理？", "conversation-2")

    assert result.conversation_id == "conversation-2"
    assert result.recommended_services == [
        AssistantServiceRecommendation(name="出口合规预检", route="/portal/precheck")
    ]
    assert result.sources == []
    await client.aclose()
