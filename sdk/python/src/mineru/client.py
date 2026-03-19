"""MinerU SDK client — 8 public methods, one runtime dependency."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterator

from ._api import ApiClient
from ._constants import DEFAULT_BASE_URL, DEFAULT_FLASH_BASE_URL
from ._flash_api import FlashApiClient
from ._zip import parse_zip
from .exceptions import NoAuthClientError, TimeoutError
from .models import ExtractResult, Progress

_DEFAULT_SOURCE = "open-api-sdk-python"

# Default timeout for a single HTTP request (in seconds)
_DEFAULT_TIMEOUT_REQUEST = 60

# Default total business timeouts for extraction tasks (in seconds)
_DEFAULT_TIMEOUT_POLL_SINGLE = 300
_DEFAULT_TIMEOUT_POLL_BATCH = 1800

_MODEL_MAP = {
    "pipeline": "pipeline",
    "vlm": "vlm",
    "html": "MinerU-HTML",
}

_HTML_EXTENSIONS = {".html", ".htm"}


def _is_url(source: str) -> bool:
    return source.startswith("http://") or source.startswith("https://")


def _get_extension(source: str) -> str:
    if _is_url(source):
        path = source.split("?")[0].split("#")[0]
        return PurePosixPath(path).suffix.lower()
    return Path(source).suffix.lower()


def _infer_model(source: str) -> str:
    return "MinerU-HTML" if _get_extension(source) in _HTML_EXTENSIONS else "vlm"


def _resolve_model(model: str | None, source: str) -> str:
    if model is not None:
        return _MODEL_MAP.get(model, model)
    return _infer_model(source)


_SENTINEL = object()  # distinguishes "not passed" from any real value


@dataclass
class FileParam:
    """Per-file parameter overrides for batch methods.

    Fields left at their default (``None`` / ``""``) inherit global options.

    Example::

        client.submit_batch(
            ["a.pdf", "b.pdf"],
            file_params={
                "a.pdf": FileParam(pages="1-5"),
                "b.pdf": FileParam(pages="10-20", ocr=True),
            },
        )
    """
    pages: str = ""
    ocr: bool | None = None
    data_id: str = ""


def _build_options(
    model_version: str,
    formula: object,
    table: object,
    language: object,
    extra_formats: list[str] | None,
) -> dict:
    """Build top-level payload fields. Only includes explicitly-set values."""
    opts: dict = {"model_version": model_version}
    if formula is not _SENTINEL:
        opts["enable_formula"] = formula
    if table is not _SENTINEL:
        opts["enable_table"] = table
    if language is not _SENTINEL:
        opts["language"] = language
    if extra_formats:
        opts["extra_formats"] = extra_formats
    return opts


def _apply_file_fields(
    file_entry: dict,
    key: str,
    ocr: bool | None,
    pages: str | None,
    file_params: dict[str, FileParam] | None,
) -> None:
    """Add per-file fields (is_ocr, page_ranges, data_id) to a file entry dict."""
    fp = file_params.get(key) if file_params else None

    # OCR: per-file overrides global
    effective_ocr = fp.ocr if (fp and fp.ocr is not None) else ocr
    if effective_ocr is not None:
        file_entry["is_ocr"] = effective_ocr

    # Pages: per-file overrides global
    effective_pages = fp.pages if (fp and fp.pages) else pages
    if effective_pages:
        file_entry["page_ranges"] = effective_pages

    # DataID: per-file only
    if fp and fp.data_id:
        file_entry["data_id"] = fp.data_id


def _parse_task_result(data: dict) -> ExtractResult:
    """Build an ExtractResult from a task query response ``data`` dict."""
    progress = None
    ep = data.get("extract_progress")
    if ep:
        progress = Progress(
            extracted_pages=ep.get("extracted_pages", 0),
            total_pages=ep.get("total_pages", 0),
            start_time=ep.get("start_time", ""),
        )

    err_code_raw = data.get("err_code")
    err_code = "" if err_code_raw is None else str(err_code_raw)

    return ExtractResult(
        task_id=data.get("task_id", ""),
        state=data.get("state", "unknown"),
        filename=data.get("file_name"),
        err_code=err_code,
        error=data.get("err_msg") or None,
        zip_url=data.get("full_zip_url"),
        progress=progress,
    )


class MinerU:
    """MinerU API client. Turn documents into Markdown with one method call.

    Args:
        token: API token. If not provided, reads from the ``MINERU_TOKEN``
            environment variable.
        base_url: API base URL. Override for private deployments.
        flash_base_url: Flash API base URL. Override for testing or
            private deployments.
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        flash_base_url: str | None = None,
    ) -> None:
        resolved_token = token or os.environ.get("MINERU_TOKEN")
        if resolved_token:
            # Note: ApiClient should ideally respect _DEFAULT_TIMEOUT_REQUEST
            self._api: ApiClient | None = ApiClient(resolved_token, base_url, source=_DEFAULT_SOURCE)
        else:
            self._api = None  # flash-only mode

        flash_url = flash_base_url or DEFAULT_FLASH_BASE_URL
        self._flash_api = FlashApiClient(flash_url, source=_DEFAULT_SOURCE)

    def close(self) -> None:
        """Release the underlying HTTP clients."""
        if self._api is not None:
            self._api.close()
        self._flash_api.close()

    def set_source(self, source: str) -> None:
        """Override the source identifier sent with API requests.

        Used to track which application or integration is making the call.
        """
        if self._api is not None:
            self._api.source = source
        self._flash_api.source = source

    def __enter__(self) -> MinerU:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ══════════════════════════════════════════════════════════════════
    #  Auth guard
    # ══════════════════════════════════════════════════════════════════

    def _require_auth(self) -> ApiClient:
        """Guard: raise if this is a flash-only client."""
        if self._api is None:
            raise NoAuthClientError()
        return self._api

    # ══════════════════════════════════════════════════════════════════
    #  Synchronous (blocking) methods
    # ══════════════════════════════════════════════════════════════════

    def extract(
        self,
        source: str,
        *,
        model: str | None = None,
        ocr: bool | None = None,
        formula: object = _SENTINEL,
        table: object = _SENTINEL,
        language: object = _SENTINEL,
        pages: str | None = None,
        extra_formats: list[str] | None = None,
        file_params: dict[str, FileParam] | None = None,
        timeout: int = _DEFAULT_TIMEOUT_POLL_SINGLE,
    ) -> ExtractResult:
        """Parse a single document. Blocks until the result is ready.

        Args:
            source: URL (``http://`` or ``https://``) or local file path.
            model: ``"pipeline"``, ``"vlm"``, or ``"html"``.
            ocr: Enable OCR. Only sent when explicitly set.
            formula: Enable formula recognition. Only sent when explicitly set.
            table: Enable table recognition. Only sent when explicitly set.
            language: Document language code. Only sent when explicitly set.
            pages: Page range string, e.g. ``"1-10,15"``.
            extra_formats: Additional export formats.
            file_params: Per-file overrides keyed by path/URL.
            timeout: Maximum seconds to wait for task completion (polling).

        Returns:
            An :class:`ExtractResult` with ``state="done"`` and content fields
            populated (``markdown``, ``images``, etc.).
        """
        model_version = _resolve_model(model, source)
        self._require_auth()
        opts = _build_options(model_version, formula, table, language, extra_formats)

        if _is_url(source):
            batch_id = self._submit_urls_batch([source], opts, ocr, pages, file_params)
        else:
            batch_id = self._upload_and_submit([source], opts, ocr, pages, file_params)
        results = self._wait_batch(batch_id, timeout)
        return results[0]

    def extract_batch(
        self,
        sources: list[str],
        *,
        model: str | None = None,
        ocr: bool | None = None,
        formula: object = _SENTINEL,
        table: object = _SENTINEL,
        language: object = _SENTINEL,
        extra_formats: list[str] | None = None,
        file_params: dict[str, FileParam] | None = None,
        timeout: int = _DEFAULT_TIMEOUT_POLL_BATCH,
    ) -> Iterator[ExtractResult]:
        """Parse multiple documents. Yields each result as it completes."""
        first_source = sources[0] if sources else ""
        model_version = _resolve_model(model, first_source)
        self._require_auth()
        opts = _build_options(model_version, formula, table, language, extra_formats)

        urls = [s for s in sources if _is_url(s)]
        files = [s for s in sources if not _is_url(s)]

        batch_ids: list[str] = []
        if urls:
            batch_ids.append(self._submit_urls_batch(urls, opts, ocr, None, file_params))
        if files:
            batch_ids.append(self._upload_and_submit(files, opts, ocr, None, file_params))

        yield from self._yield_batch(batch_ids, len(sources), timeout)

    def crawl(
        self,
        url: str,
        *,
        extra_formats: list[str] | None = None,
        timeout: int = _DEFAULT_TIMEOUT_POLL_SINGLE,
    ) -> ExtractResult:
        """Crawl a web page and parse it to Markdown."""
        return self.extract(url, model="html", extra_formats=extra_formats, timeout=timeout)

    def crawl_batch(
        self,
        urls: list[str],
        *,
        extra_formats: list[str] | None = None,
        timeout: int = _DEFAULT_TIMEOUT_POLL_BATCH,
    ) -> Iterator[ExtractResult]:
        """Crawl multiple web pages. Yields results as each completes."""
        return self.extract_batch(urls, model="html", extra_formats=extra_formats, timeout=timeout)

    # ══════════════════════════════════════════════════════════════════
    #  Async primitives (no polling, no waiting)
    # ══════════════════════════════════════════════════════════════════

    def submit(
        self,
        source: str,
        *,
        model: str | None = None,
        ocr: bool | None = None,
        formula: object = _SENTINEL,
        table: object = _SENTINEL,
        language: object = _SENTINEL,
        pages: str | None = None,
        extra_formats: list[str] | None = None,
        file_params: dict[str, FileParam] | None = None,
    ) -> str:
        """Submit a single task without waiting. Always returns a batch ID."""
        model_version = _resolve_model(model, source)
        self._require_auth()
        opts = _build_options(model_version, formula, table, language, extra_formats)

        if _is_url(source):
            return self._submit_urls_batch([source], opts, ocr, pages, file_params)
        else:
            return self._upload_and_submit([source], opts, ocr, pages, file_params)

    def submit_batch(
        self,
        sources: list[str],
        *,
        model: str | None = None,
        ocr: bool | None = None,
        formula: object = _SENTINEL,
        table: object = _SENTINEL,
        language: object = _SENTINEL,
        extra_formats: list[str] | None = None,
        file_params: dict[str, FileParam] | None = None,
    ) -> str:
        """Submit multiple tasks without waiting. Returns a batch ID string."""
        first_source = sources[0] if sources else ""
        model_version = _resolve_model(model, first_source)
        self._require_auth()
        opts = _build_options(model_version, formula, table, language, extra_formats)

        urls = [s for s in sources if _is_url(s)]
        files = [s for s in sources if not _is_url(s)]

        if not urls and not files:
            raise ValueError("No sources provided.")

        if urls and files:
            raise ValueError(
                "submit_batch() does not support mixing URLs and local files in one call. "
                "Please submit them separately or use extract_batch() instead."
            )

        if urls:
            return self._submit_urls_batch(urls, opts, ocr, None, file_params)
        return self._upload_and_submit(files, opts, ocr, None, file_params)

    def get_task(self, task_id: str) -> ExtractResult:
        """Query a single task by task ID."""
        body = self._require_auth().get(f"/extract/task/{task_id}")
        result = _parse_task_result(body["data"])
        if result.state == "done" and result.zip_url:
            return self._download_and_parse(result)
        return result

    def get_batch(self, batch_id: str) -> list[ExtractResult]:
        """Query all tasks in a batch."""
        body = self._require_auth().get(f"/extract-results/batch/{batch_id}")
        results: list[ExtractResult] = []
        for item in body["data"].get("extract_result", []):
            r = _parse_task_result(item)
            if r.state == "done" and r.zip_url:
                r = self._download_and_parse(r)
            results.append(r)
        return results

    # ══════════════════════════════════════════════════════════════════
    #  Internal helpers
    # ══════════════════════════════════════════════════════════════════

    def _submit_urls_batch(
        self,
        urls: list[str],
        opts: dict,
        ocr: bool | None,
        pages: str | None,
        file_params: dict[str, FileParam] | None,
    ) -> str:
        files = []
        for u in urls:
            entry: dict = {"url": u}
            _apply_file_fields(entry, u, ocr, pages, file_params)
            files.append(entry)
        payload = {"files": files, **opts}
        body = self._require_auth().post("/extract/task/batch", payload)
        return body["data"]["batch_id"]

    def _upload_and_submit(
        self,
        file_paths: list[str],
        opts: dict,
        ocr: bool | None,
        pages: str | None,
        file_params: dict[str, FileParam] | None,
    ) -> str:
        api = self._require_auth()
        files_meta = []
        for p in file_paths:
            entry: dict = {"name": Path(p).name}
            _apply_file_fields(entry, p, ocr, pages, file_params)
            files_meta.append(entry)
        payload = {"files": files_meta, **opts}
        body = api.post("/file-urls/batch", payload)
        batch_id: str = body["data"]["batch_id"]
        upload_urls: list[str] = body["data"]["file_urls"]

        for local_path, upload_url in zip(file_paths, upload_urls):
            data = Path(local_path).read_bytes()
            api.put_file(upload_url, data)

        return batch_id

    def _download_and_parse(self, result: ExtractResult) -> ExtractResult:
        assert result.zip_url is not None
        zip_bytes = self._require_auth().download(result.zip_url)
        parsed = parse_zip(zip_bytes, task_id=result.task_id, filename=result.filename)
        parsed.zip_url = result.zip_url
        return parsed

    def _wait_batch(self, batch_id: str, timeout: int) -> list[ExtractResult]:
        deadline = time.monotonic() + timeout
        interval = 2.0
        while True:
            results = self.get_batch(batch_id)
            if all(r.state in ("done", "failed") for r in results):
                return results
            if time.monotonic() > deadline:
                raise TimeoutError(timeout, batch_id)
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            interval = min(interval * 2, 30.0)

    def _yield_batch(
        self,
        batch_ids: list[str],
        total: int,
        timeout: int,
    ) -> Iterator[ExtractResult]:
        deadline = time.monotonic() + timeout
        yielded: set[tuple[str, int]] = set()
        interval = 2.0

        while len(yielded) < total:
            for bid in batch_ids:
                results = self.get_batch(bid)
                for idx, r in enumerate(results):
                    key = (bid, idx)
                    if key not in yielded and r.state in ("done", "failed"):
                        yielded.add(key)
                        yield r

            if len(yielded) >= total:
                break
            if time.monotonic() > deadline:
                raise TimeoutError(timeout, ",".join(batch_ids))
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            interval = min(interval * 2, 30.0)

    # ══════════════════════════════════════════════════════════════════
    #  Flash (agent) mode
    # ══════════════════════════════════════════════════════════════════

    def flash_extract(
        self,
        source: str,
        *,
        language: str = "ch",
        page_range: str | None = None,
        timeout: int = _DEFAULT_TIMEOUT_POLL_SINGLE,
    ) -> ExtractResult:
        """Parse a document using the flash (agent) API.

        Flash mode requires no API token, only outputs Markdown, and is
        optimised for speed. No model selection, no extra formats.

        Args:
            source: URL or local file path.
            language: Document language code. Default ``"ch"``.
            page_range: Page range, e.g. ``"1-10"``.
            timeout: Maximum seconds to wait for task completion (polling).

        Returns:
            :class:`ExtractResult` with ``markdown`` populated.

        Raises:
            TimeoutError: If the task does not complete within *timeout* seconds.
        """
        if _is_url(source):
            task_id = self._flash_submit_url(source, language, page_range)
        else:
            task_id = self._flash_submit_file(source, language, page_range)

        return self._flash_wait(task_id, timeout)

    # ── Flash internal helpers ──

    def _flash_submit_url(self, url: str, language: str, page_range: str | None) -> str:
        payload: dict = {"url": url, "language": language}
        if page_range is not None:
            payload["page_range"] = page_range
        body = self._flash_api.post("/parse/url", payload)
        return body["data"]["task_id"]

    def _flash_submit_file(self, file_path: str, language: str, page_range: str | None) -> str:
        file_name = Path(file_path).name
        payload: dict = {"file_name": file_name, "language": language}
        if page_range is not None:
            payload["page_range"] = page_range
        body = self._flash_api.post("/parse/file", payload)
        task_id: str = body["data"]["task_id"]
        file_url: str = body["data"]["file_url"]

        data = Path(file_path).read_bytes()
        self._flash_api.put_file(file_url, data)
        return task_id

    def _flash_wait(self, task_id: str, timeout: int) -> ExtractResult:
        deadline = time.monotonic() + timeout
        interval = 2.0
        while True:
            result = self._flash_get_task(task_id)
            if result.state in ("done", "failed"):
                return result
            if time.monotonic() > deadline:
                raise TimeoutError(timeout, task_id)
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            interval = min(interval * 2, 30.0)

    def _flash_get_task(self, task_id: str) -> ExtractResult:
        body = self._flash_api.get(f"/parse/{task_id}")
        return self._parse_flash_task(body["data"])

    def _parse_flash_task(self, data: dict) -> ExtractResult:
        progress = None
        ep = data.get("extract_progress")
        if ep:
            progress = Progress(
                extracted_pages=ep.get("extracted_pages", 0),
                total_pages=ep.get("total_pages", 0),
                start_time=ep.get("start_time", ""),
            )

        err_code_raw = data.get("err_code")
        err_code = "" if err_code_raw is None else str(err_code_raw)

        result = ExtractResult(
            task_id=data.get("task_id", ""),
            state=data.get("state", "unknown"),
            err_code=err_code,
            error=data.get("err_msg") or None,
            progress=progress,
        )

        if result.state == "done" and data.get("markdown_url"):
            result.markdown = self._flash_api.download_text(data["markdown_url"])

        return result
