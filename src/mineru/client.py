"""MinerU SDK client — 8 public methods, one runtime dependency."""

from __future__ import annotations

import os
import time
from pathlib import Path, PurePosixPath
from typing import Iterator

from ._api import ApiClient
from ._zip import parse_zip
from .exceptions import AuthError, TimeoutError
from .models import ExtractResult, Progress

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


def _build_options(
    model_version: str,
    ocr: bool,
    formula: bool,
    table: bool,
    language: str,
    pages: str | None,
    extra_formats: list[str] | None,
) -> dict:
    opts: dict = {"model_version": model_version}
    if ocr:
        opts["is_ocr"] = True
    if not formula:
        opts["enable_formula"] = False
    if not table:
        opts["enable_table"] = False
    if language != "ch":
        opts["language"] = language
    if pages is not None:
        opts["page_ranges"] = pages
    if extra_formats:
        opts["extra_formats"] = extra_formats
    return opts


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
    return ExtractResult(
        task_id=data.get("task_id", ""),
        state=data.get("state", "unknown"),
        filename=data.get("file_name"),
        error=data.get("err_msg") or None,
        zip_url=data.get("full_zip_url"),
        progress=progress,
    )


class MinerU:
    """MinerU API client.

    Args:
        token: API token. Falls back to the ``MINERU_TOKEN`` environment variable.
        base_url: API base URL. Override for private deployments.
    """

    def __init__(
        self,
        token: str | None = None,
        base_url: str = "https://mineru.net/api/v4",
    ) -> None:
        resolved_token = token or os.environ.get("MINERU_TOKEN")
        if not resolved_token:
            raise AuthError("NO_TOKEN", "No token provided. Pass token= or set MINERU_TOKEN env var.")
        self._api = ApiClient(resolved_token, base_url)

    def close(self) -> None:
        self._api.close()

    def __enter__(self) -> MinerU:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ══════════════════════════════════════════════════════════════════
    #  Synchronous (blocking) methods
    # ══════════════════════════════════════════════════════════════════

    def extract(
        self,
        source: str,
        *,
        model: str | None = None,
        ocr: bool = False,
        formula: bool = True,
        table: bool = True,
        language: str = "ch",
        pages: str | None = None,
        extra_formats: list[str] | None = None,
        timeout: int = 300,
    ) -> ExtractResult:
        """Parse a single document. Blocks until the result is ready.

        *source* can be a URL or a local file path. Local files are uploaded
        automatically. The ``model`` is inferred from the file extension when
        not specified (``.html`` → ``MinerU-HTML``, everything else → ``vlm``).
        """
        model_version = _resolve_model(model, source)
        opts = _build_options(model_version, ocr, formula, table, language, pages, extra_formats)

        if _is_url(source):
            task_id = self._submit_url(source, opts)
            return self._wait_single(task_id, timeout)
        else:
            batch_id = self._upload_and_submit([source], opts)
            results = self._wait_batch(batch_id, timeout)
            return results[0]

    def extract_batch(
        self,
        sources: list[str],
        *,
        model: str | None = None,
        ocr: bool = False,
        formula: bool = True,
        table: bool = True,
        language: str = "ch",
        extra_formats: list[str] | None = None,
        timeout: int = 600,
    ) -> Iterator[ExtractResult]:
        """Parse multiple documents. Yields each result as it completes.

        All tasks are submitted at once via the batch API. Results are yielded
        in completion order (first done, first yielded).
        """
        first_source = sources[0] if sources else ""
        model_version = _resolve_model(model, first_source)
        opts = _build_options(model_version, ocr, formula, table, language, None, extra_formats)

        urls = [s for s in sources if _is_url(s)]
        files = [s for s in sources if not _is_url(s)]

        batch_ids: list[str] = []
        if urls:
            batch_ids.append(self._submit_urls_batch(urls, opts))
        if files:
            batch_ids.append(self._upload_and_submit(files, opts))

        yield from self._yield_batch(batch_ids, len(sources), timeout)

    def crawl(
        self,
        url: str,
        *,
        extra_formats: list[str] | None = None,
        timeout: int = 300,
    ) -> ExtractResult:
        """Crawl a web page and parse it to Markdown."""
        return self.extract(url, model="html", extra_formats=extra_formats, timeout=timeout)

    def crawl_batch(
        self,
        urls: list[str],
        *,
        extra_formats: list[str] | None = None,
        timeout: int = 600,
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
        ocr: bool = False,
        formula: bool = True,
        table: bool = True,
        language: str = "ch",
        pages: str | None = None,
        extra_formats: list[str] | None = None,
    ) -> str:
        """Submit a single task. Returns a ``task_id`` string immediately."""
        model_version = _resolve_model(model, source)
        opts = _build_options(model_version, ocr, formula, table, language, pages, extra_formats)

        if _is_url(source):
            return self._submit_url(source, opts)
        else:
            return self._upload_and_submit([source], opts)

    def submit_batch(
        self,
        sources: list[str],
        *,
        model: str | None = None,
        ocr: bool = False,
        formula: bool = True,
        table: bool = True,
        language: str = "ch",
        extra_formats: list[str] | None = None,
    ) -> str:
        """Submit multiple tasks. Returns a ``batch_id`` string immediately."""
        first_source = sources[0] if sources else ""
        model_version = _resolve_model(model, first_source)
        opts = _build_options(model_version, ocr, formula, table, language, None, extra_formats)

        urls = [s for s in sources if _is_url(s)]
        files = [s for s in sources if not _is_url(s)]

        if urls and not files:
            return self._submit_urls_batch(urls, opts)
        if files and not urls:
            return self._upload_and_submit(files, opts)
        # Mixed: prefer file upload batch (simpler to track with one batch_id).
        # Upload everything via file-urls endpoint.
        return self._upload_and_submit(sources, opts)

    def get_task(self, task_id: str) -> ExtractResult:
        """Query a single task. Downloads and parses the zip when done."""
        body = self._api.get(f"/extract/task/{task_id}")
        result = _parse_task_result(body["data"])
        if result.state == "done" and result.zip_url:
            return self._download_and_parse(result)
        return result

    def get_batch(self, batch_id: str) -> list[ExtractResult]:
        """Query all tasks in a batch."""
        body = self._api.get(f"/extract-results/batch/{batch_id}")
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

    def _submit_url(self, url: str, opts: dict) -> str:
        payload = {"url": url, **opts}
        body = self._api.post("/extract/task", payload)
        return body["data"]["task_id"]

    def _submit_urls_batch(self, urls: list[str], opts: dict) -> str:
        files = [{"url": u} for u in urls]
        payload = {"files": files, **opts}
        body = self._api.post("/extract/task/batch", payload)
        return body["data"]["batch_id"]

    def _upload_and_submit(self, file_paths: list[str], opts: dict) -> str:
        files_meta = [{"name": Path(p).name} for p in file_paths]
        payload = {"files": files_meta, **opts}
        body = self._api.post("/file-urls/batch", payload)
        batch_id: str = body["data"]["batch_id"]
        upload_urls: list[str] = body["data"]["file_urls"]

        for local_path, upload_url in zip(file_paths, upload_urls):
            data = Path(local_path).read_bytes()
            self._api.put_file(upload_url, data)

        return batch_id

    def _download_and_parse(self, result: ExtractResult) -> ExtractResult:
        assert result.zip_url is not None
        zip_bytes = self._api.download(result.zip_url)
        parsed = parse_zip(zip_bytes, task_id=result.task_id, filename=result.filename)
        parsed.zip_url = result.zip_url
        return parsed

    def _wait_single(self, task_id: str, timeout: int) -> ExtractResult:
        """Poll a single task until it reaches a terminal state."""
        deadline = time.monotonic() + timeout
        interval = 2.0
        while True:
            result = self.get_task(task_id)
            if result.state in ("done", "failed"):
                return result
            if time.monotonic() > deadline:
                raise TimeoutError(timeout, task_id)
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            interval = min(interval * 2, 30.0)

    def _wait_batch(self, batch_id: str, timeout: int) -> list[ExtractResult]:
        """Poll a batch until all tasks reach a terminal state."""
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
        """Poll batch(es) and yield each result as it becomes done."""
        deadline = time.monotonic() + timeout
        yielded: set[str] = set()  # track by filename or task_id
        interval = 2.0

        while len(yielded) < total:
            for bid in batch_ids:
                results = self.get_batch(bid)
                for r in results:
                    key = r.filename or r.task_id
                    if key not in yielded and r.state in ("done", "failed"):
                        yielded.add(key)
                        yield r

            if len(yielded) >= total:
                break
            if time.monotonic() > deadline:
                raise TimeoutError(timeout, ",".join(batch_ids))
            time.sleep(min(interval, max(0, deadline - time.monotonic())))
            interval = min(interval * 2, 30.0)
