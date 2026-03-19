"""Low-level HTTP wrapper for the Flash (agent) API."""

from __future__ import annotations

from typing import Any

import httpx

from ._constants import DEFAULT_FLASH_BASE_URL
from .exceptions import raise_for_code

_TIMEOUT = httpx.Timeout(30.0, read=120.0)


class FlashApiClient:
    """No-auth HTTP client for the Flash API."""

    def __init__(self, base_url: str = DEFAULT_FLASH_BASE_URL, source: str = "") -> None:
        self._source = source
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Content-Type": "application/json"},
            timeout=_TIMEOUT,
        )

    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, value: str) -> None:
        self._source = value

    def close(self) -> None:
        self._client.close()

    def post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        headers = {"source": self._source} if self._source else {}
        resp = self._client.post(path, json=json, headers=headers)
        return self._handle(resp)

    def get(self, path: str) -> dict[str, Any]:
        resp = self._client.get(path)
        return self._handle(resp)

    def put_file(self, url: str, data: bytes) -> None:
        resp = httpx.put(url, content=data, timeout=_TIMEOUT)
        resp.raise_for_status()

    def download_text(self, url: str) -> str:
        resp = httpx.get(url, timeout=httpx.Timeout(30.0, read=300.0), follow_redirects=True)
        resp.raise_for_status()
        return resp.text

    @staticmethod
    def _handle(resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code == 429:
            raise_for_code("RATE_LIMITED", "flash API rate limit exceeded; try again later")
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        code = body.get("code", 0)
        if code != 0:
            raise_for_code(code, body.get("msg", "unknown error"), body.get("trace_id", ""))
        return body
