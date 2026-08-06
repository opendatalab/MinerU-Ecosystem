"""Local upload streaming tests with no MinerU API calls."""

from unittest.mock import Mock

import pytest
from mineru import MinerU
from mineru._api import ApiClient
from mineru._constants import UPLOAD_TIMEOUT
from mineru._flash_api import FlashApiClient
from mineru.client import _UPLOAD_CHUNK_SIZE


@pytest.fixture
def upload_file(tmp_path):
    payload = bytes(range(256)) * (2 * _UPLOAD_CHUNK_SIZE // 256) + b"tail"
    path = tmp_path / "synthetic.pdf"
    path.write_bytes(payload)
    return path, payload


def assert_streamed_upload(call, payload):
    upload_url, content = call.args
    chunks = list(content)

    assert upload_url == "https://upload.example/file"
    assert not isinstance(content, bytes)
    assert len(chunks) > 2
    assert all(0 < len(chunk) <= _UPLOAD_CHUNK_SIZE for chunk in chunks)
    assert b"".join(chunks) == payload
    assert call.kwargs == {"content_length": len(payload)}


def test_precision_submit_streams_local_file(upload_file):
    path, payload = upload_file
    client = MinerU(token="test-token")
    api = Mock()
    api.post.return_value = {
        "data": {
            "batch_id": "batch-id",
            "file_urls": ["https://upload.example/file"],
        }
    }
    client._api = api

    assert client.submit(str(path)) == "batch-id"

    assert_streamed_upload(api.put_file.call_args, payload)


def test_flash_submit_streams_local_file(upload_file):
    path, payload = upload_file
    client = MinerU(token="test-token")
    flash_api = Mock()
    flash_api.post.return_value = {
        "data": {
            "task_id": "task-id",
            "file_url": "https://upload.example/file",
        }
    }
    client._flash_api = flash_api

    assert (
        client._flash_submit_file(str(path), "ch", None, None, None, None) == "task-id"
    )

    assert_streamed_upload(flash_api.put_file.call_args, payload)


@pytest.mark.parametrize("client_class", [ApiClient, FlashApiClient])
def test_put_file_sets_content_length_for_stream(monkeypatch, client_class):
    response = Mock()
    put = Mock(return_value=response)
    monkeypatch.setattr(f"{client_class.__module__}.httpx.put", put)
    client = (
        client_class("test-token", "https://api.example")
        if client_class is ApiClient
        else client_class()
    )
    chunks = iter([b"abc", b"def"])

    client.put_file("https://upload.example/file", chunks, content_length=6)

    put.assert_called_once_with(
        "https://upload.example/file",
        content=chunks,
        headers={"Content-Length": "6"},
        timeout=UPLOAD_TIMEOUT,
    )
    response.raise_for_status.assert_called_once_with()
    client.close()


@pytest.mark.parametrize("client_class", [ApiClient, FlashApiClient])
def test_put_file_keeps_bytes_compatible(monkeypatch, client_class):
    response = Mock()
    put = Mock(return_value=response)
    monkeypatch.setattr(f"{client_class.__module__}.httpx.put", put)
    client = (
        client_class("test-token", "https://api.example")
        if client_class is ApiClient
        else client_class()
    )

    client.put_file("https://upload.example/file", b"content")

    assert put.call_args.kwargs["content"] == b"content"
    assert put.call_args.kwargs["headers"] is None
    response.raise_for_status.assert_called_once_with()
    client.close()
