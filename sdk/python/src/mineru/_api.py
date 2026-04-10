"""Low-level HTTP wrapper around the MinerU v4 API."""

from __future__ import annotations

from typing import Any

import httpx

from ._constants import REQUEST_TIMEOUT, UPLOAD_TIMEOUT
from .exceptions import raise_for_code


class ApiClient:
    """Thin wrapper that handles auth headers, base URL, and error mapping."""

    def __init__(self, token: str, base_url: str, source: str = "") -> None:
        self._source = source
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=REQUEST_TIMEOUT,
        )

    @property
    def source(self) -> str:
        return self._source

    @source.setter
    def source(self, value: str) -> None:
        self._source = value

    def close(self) -> None:
        self._client.close()

    # ── requests ──

    def post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        headers = {"source": self._source} if self._source else {}
        resp = self._client.post(path, json=json, headers=headers)
        return self._handle(resp)

    def get(self, path: str) -> dict[str, Any]:
        resp = self._client.get(path)
        return self._handle(resp)

    def put_file(self, url: str, data: bytes) -> None:
        """Upload file bytes to a pre-signed URL (no auth headers needed)."""
        resp = httpx.put(url, content=data, timeout=UPLOAD_TIMEOUT)
        resp.raise_for_status()

    def download(self, url: str) -> bytes:
        """Download a file from a URL and return raw bytes."""
        resp = httpx.get(url, timeout=httpx.Timeout(30.0, read=300.0), follow_redirects=True)
        resp.raise_for_status()
        return resp.content

    # ── internal ──

    @staticmethod
    def _handle(resp: httpx.Response) -> dict[str, Any]:
        resp.raise_for_status()
        body: dict[str, Any] = resp.json()
        code = body.get("code", 0)
        if code != 0:
            raise_for_code(code, body.get("msg", "unknown error"), body.get("trace_id", ""))
        return body
