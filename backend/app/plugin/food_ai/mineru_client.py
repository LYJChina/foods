from collections.abc import Mapping
from math import isfinite
from typing import Any

import httpx


class MinerUUnavailable(Exception):
    """The MinerU service cannot be reached or cannot complete a request."""

    def __init__(self) -> None:
        super().__init__("文档解析服务暂不可用，请稍后重试。")


class MinerUInvalidResponse(Exception):
    """The MinerU service returned a response outside the expected contract."""

    def __init__(self) -> None:
        super().__init__("文档解析服务返回的数据无效。")


class MinerUClient:
    """Small, isolated HTTP boundary for the separately-running MinerU service."""

    _MIN_TIMEOUT_SECONDS = 1.0
    _MAX_TIMEOUT_SECONDS = 120.0

    def __init__(
        self,
        base_url: str,
        service_token: str | None,
        timeout: float,
        *,
        client: httpx.AsyncClient | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token or ""
        self.timeout = self._bounded_timeout(timeout)
        self._owned_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(
                self.timeout,
                connect=self.timeout,
                read=self.timeout,
                write=self.timeout,
                pool=self.timeout,
            ),
            transport=transport,
        )

    async def __aenter__(self) -> "MinerUClient":
        return self

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owned_client:
            await self._client.aclose()
            self._owned_client = False

    async def health(self) -> dict[str, Any]:
        payload = await self._request("GET", "/health")
        self._require_nonempty_string(payload, "status")
        return payload

    async def submit(self, file_name: str, content: bytes, content_type: str) -> dict[str, Any]:
        payload = await self._request(
            "POST",
            "/tasks",
            data={
                "lang_list": "ch",
                "backend": "pipeline",
                "parse_method": "auto",
                "return_md": "true",
                "return_content_list": "true",
            },
            files={"files": (file_name, content, content_type)},
        )
        self._validate_task_payload(payload)
        return payload

    async def get_status(self, task_id: str) -> dict[str, Any]:
        payload = await self._request("GET", f"/tasks/{task_id}")
        self._validate_task_payload(payload)
        return payload

    async def get_result(self, task_id: str) -> dict[str, Any]:
        response, payload = await self._request_with_response("GET", f"/tasks/{task_id}/result")
        if response.status_code == 202:
            self._validate_task_payload(payload)
            return payload
        if not isinstance(payload.get("results"), Mapping):
            raise MinerUInvalidResponse()
        return payload

    async def _request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> dict[str, Any]:
        _, payload = await self._request_with_response(method, path, data=data, files=files)
        return payload

    async def _request_with_response(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> tuple[httpx.Response, dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self.service_token}"} if self.service_token else None
        try:
            response = await self._client.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                data=data,
                files=files,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            raise MinerUUnavailable() from None
        try:
            payload = response.json()
        except (ValueError, TypeError):
            raise MinerUInvalidResponse() from None
        if not isinstance(payload, Mapping):
            raise MinerUInvalidResponse()
        return response, dict(payload)

    @classmethod
    def _bounded_timeout(cls, timeout: float) -> float:
        try:
            numeric_timeout = float(timeout)
        except (TypeError, ValueError):
            return cls._MIN_TIMEOUT_SECONDS
        if not isfinite(numeric_timeout):
            return cls._MIN_TIMEOUT_SECONDS
        return min(max(numeric_timeout, cls._MIN_TIMEOUT_SECONDS), cls._MAX_TIMEOUT_SECONDS)

    @staticmethod
    def _require_nonempty_string(payload: Mapping[str, Any], field: str) -> None:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise MinerUInvalidResponse()

    def _validate_task_payload(self, payload: Mapping[str, Any]) -> None:
        self._require_nonempty_string(payload, "task_id")
        self._require_nonempty_string(payload, "status")
