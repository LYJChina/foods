import httpx
import pytest

from app.plugin.food_ai.mineru_client import MinerUClient, MinerUInvalidResponse, MinerUUnavailable


@pytest.mark.asyncio
async def test_submit_sends_required_multipart_fields_and_optional_service_token() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(202, json={"task_id": "task-001", "status": "pending", "progress": 0}, request=request)

    client = MinerUClient(
        "http://mineru.internal/",
        "service-token-value",
        15,
        transport=httpx.MockTransport(handler),
    )
    try:
        result = await client.submit("食品标签.pdf", b"%PDF-1.7", "application/pdf")
    finally:
        await client.aclose()

    assert result == {"task_id": "task-001", "status": "pending", "progress": 0}
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "POST"
    assert request.url == "http://mineru.internal/tasks"
    assert request.headers["authorization"] == "Bearer service-token-value"
    body = request.content.decode("utf-8")
    assert 'name="return_md"' in body
    assert "true" in body
    assert 'name="return_content_list"' in body
    assert 'name="files"; filename="食品标签.pdf"' in body


@pytest.mark.asyncio
async def test_client_does_not_send_authorization_when_service_token_is_empty() -> None:
    seen_headers: list[httpx.Headers] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return httpx.Response(200, json={"status": "healthy"}, request=request)

    client = MinerUClient("http://mineru.internal", "", 15, transport=httpx.MockTransport(handler))
    try:
        assert await client.health() == {"status": "healthy"}
    finally:
        await client.aclose()

    assert "authorization" not in seen_headers[0]


@pytest.mark.asyncio
async def test_get_status_and_pending_result_preserve_progress_status() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/tasks/task-001":
            return httpx.Response(200, json={"task_id": "task-001", "status": "processing", "progress": 42}, request=request)
        return httpx.Response(202, json={"task_id": "task-001", "status": "processing", "progress": 42}, request=request)

    client = MinerUClient("http://mineru.internal", None, 15, transport=httpx.MockTransport(handler))
    try:
        assert await client.get_status("task-001") == {"task_id": "task-001", "status": "processing", "progress": 42}
        assert await client.get_result("task-001") == {"task_id": "task-001", "status": "processing", "progress": 42}
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_get_result_returns_complete_mineru_results_fixture() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "backend": "pipeline",
                "results": {
                    "食品标签.pdf": {
                        "md_content": "# 食品标签\n过敏原应明确标示。",
                        "content_list": [{"type": "text", "text": "过敏原应明确标示。", "page_idx": 0}],
                    }
                },
            },
            request=request,
        )

    client = MinerUClient("http://mineru.internal", None, 15, transport=httpx.MockTransport(handler))
    try:
        result = await client.get_result("task-001")
    finally:
        await client.aclose()

    assert result["results"]["食品标签.pdf"]["md_content"] == "# 食品标签\n过敏原应明确标示。"


@pytest.mark.asyncio
async def test_get_result_requires_results_object_and_rejects_malformed_json() -> None:
    responses = iter(
        [
            httpx.Response(200, json={"backend": "pipeline"}),
            httpx.Response(200, content=b"not json", headers={"content-type": "application/json"}),
        ]
    )

    async def handler(request: httpx.Request) -> httpx.Response:
        response = next(responses)
        response.request = request
        return response

    client = MinerUClient("http://mineru.internal", None, 15, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(MinerUInvalidResponse, match="文档解析服务返回的数据无效"):
            await client.get_result("task-001")
        with pytest.raises(MinerUInvalidResponse, match="文档解析服务返回的数据无效"):
            await client.health()
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_network_failure_is_safe_and_does_not_leak_upstream_details() -> None:
    secret_url = "http://mineru.internal:8002/hidden"
    secret_token = "service-token-value"

    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = MinerUClient(secret_url, secret_token, 15, transport=httpx.MockTransport(handler))
    try:
        with pytest.raises(MinerUUnavailable) as exc_info:
            await client.health()
    finally:
        await client.aclose()

    message = str(exc_info.value)
    assert message == "文档解析服务暂不可用，请稍后重试。"
    assert secret_url not in message
    assert secret_token not in message
