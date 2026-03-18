"""MinerU SDK client — 8 public methods, one runtime dependency."""

from __future__ import annotations

import os
import time
from pathlib import Path, PurePosixPath
from typing import Iterator

from ._api import ApiClient
from ._flash_api import DEFAULT_FLASH_BASE_URL, FlashApiClient
from ._zip import parse_zip
from .exceptions import NoAuthClientError, TimeoutError
from .models import ExtractResult, Progress

_DEFAULT_SOURCE = "open-api-sdk-python"

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

    Example::

        from mineru import MinerU

        client = MinerU()  # reads MINERU_TOKEN env var
        md = client.extract("https://example.com/doc.pdf").markdown

    When no token is provided and ``MINERU_TOKEN`` is not set, a flash-only
    client is created. Only :meth:`flash_extract` is available; calling
    standard methods raises :class:`NoAuthClientError`.

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
        base_url: str = "https://mineru.net/api/v4",
        flash_base_url: str | None = None,
    ) -> None:
        resolved_token = token or os.environ.get("MINERU_TOKEN")
        if resolved_token:
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
        ocr: bool = False,
        formula: bool = True,
        table: bool = True,
        language: str = "ch",
        pages: str | None = None,
        extra_formats: list[str] | None = None,
        timeout: int = 300,
    ) -> ExtractResult:
        """Parse a single document. Blocks until the result is ready.

        Example::

            result = MinerU().extract("https://example.com/doc.pdf")
            print(result.markdown)

            # Local file with options
            result = MinerU().extract(
                "./paper.pdf",
                model="vlm",
                ocr=True,
                extra_formats=["docx"],
                timeout=600,
            )
            result.save_docx("paper.docx")

        Args:
            source: URL (``http://`` or ``https://``) or local file path.
                Local files are uploaded automatically.
            model: ``"pipeline"``, ``"vlm"``, or ``"html"``. When ``None``
                (default), inferred from file extension — ``.html`` uses
                ``"html"``, everything else uses ``"vlm"``.
            ocr: Enable OCR. Only effective with ``pipeline`` or ``vlm`` models.
            formula: Enable formula recognition. Defaults to ``True``.
            table: Enable table recognition. Defaults to ``True``.
            language: Document language code. Defaults to ``"ch"`` (Chinese).
            pages: Page range string, e.g. ``"1-10,15"`` or ``"2--2"``.
            extra_formats: Additional export formats. Accepts any combination
                of ``"docx"``, ``"html"``, and ``"latex"``. Markdown and JSON
                are always included.
            timeout: Maximum seconds to wait for completion.

        Returns:
            An :class:`ExtractResult` with ``state="done"`` and content fields
            populated (``markdown``, ``images``, etc.).

        Raises:
            TimeoutError: If the task does not complete within *timeout* seconds.
            ExtractFailedError: If the server reports extraction failure.
        """
        model_version = _resolve_model(model, source)
        self._require_auth()
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
        in completion order — the first document to finish is yielded first.

        Example::

            for result in MinerU().extract_batch(["a.pdf", "b.pdf", "c.pdf"]):
                print(f"{result.filename}: {result.markdown[:200]}")

        Args:
            sources: List of URLs or local file paths (can be mixed).
            model: Model version. See :meth:`extract` for details.
            ocr: Enable OCR.
            formula: Enable formula recognition.
            table: Enable table recognition.
            language: Document language code.
            extra_formats: Additional export formats (``"docx"``/``"html"``/``"latex"``).
            timeout: Maximum seconds to wait for *all* tasks to complete.

        Yields:
            :class:`ExtractResult` for each completed document.

        Raises:
            TimeoutError: If not all tasks complete within *timeout* seconds.
        """
        first_source = sources[0] if sources else ""
        model_version = _resolve_model(model, first_source)
        self._require_auth()
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
        """Crawl a web page and parse it to Markdown.

        Equivalent to ``extract(url, model="html", ...)``.

        Example::

            result = MinerU().crawl("https://opendatalab.com")
            print(result.markdown)

        Args:
            url: Web page URL.
            extra_formats: Additional export formats.
            timeout: Maximum seconds to wait.

        Returns:
            An :class:`ExtractResult` with the parsed content.
        """
        return self.extract(url, model="html", extra_formats=extra_formats, timeout=timeout)

    def crawl_batch(
        self,
        urls: list[str],
        *,
        extra_formats: list[str] | None = None,
        timeout: int = 600,
    ) -> Iterator[ExtractResult]:
        """Crawl multiple web pages. Yields results as each completes.

        Equivalent to ``extract_batch(urls, model="html", ...)``.

        Example::

            for result in MinerU().crawl_batch(["https://a.com", "https://b.com"]):
                print(result.markdown[:200])

        Args:
            urls: List of web page URLs.
            extra_formats: Additional export formats.
            timeout: Maximum seconds to wait for all pages.

        Yields:
            :class:`ExtractResult` for each completed page.
        """
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
        """Submit a single task without waiting. Always returns a batch ID.

        Use :meth:`get_batch` later to check the result.

        Example::

            batch_id = MinerU().submit("https://example.com/doc.pdf")
            # or local file:
            batch_id = MinerU().submit("./report.pdf")

            # Later, check the result:
            results = MinerU().get_batch(batch_id)
            print(results[0].state)

        Args:
            source: URL or local file path.
            model: Model version. See :meth:`extract` for details.
            ocr: Enable OCR.
            formula: Enable formula recognition.
            table: Enable table recognition.
            language: Document language code.
            pages: Page range string.
            extra_formats: Additional export formats.

        Returns:
            A ``batch_id`` string. Use :meth:`get_batch` to poll for results.
        """
        model_version = _resolve_model(model, source)
        self._require_auth()
        opts = _build_options(model_version, ocr, formula, table, language, pages, extra_formats)

        if _is_url(source):
            return self._submit_urls_batch([source], opts)
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
        """Submit multiple tasks without waiting. Returns a batch ID string.

        Use :meth:`get_batch` later to check results.

        Example::

            batch_id = MinerU().submit_batch(["a.pdf", "b.pdf"])
            print(batch_id)

            # Later:
            results = MinerU().get_batch(batch_id)
            for r in results:
                print(r.filename, r.state)

        Args:
            sources: List of URLs or local file paths.
            model: Model version. See :meth:`extract` for details.
            ocr: Enable OCR.
            formula: Enable formula recognition.
            table: Enable table recognition.
            language: Document language code.
            extra_formats: Additional export formats.

        Returns:
            A ``batch_id`` string.
        """
        first_source = sources[0] if sources else ""
        model_version = _resolve_model(model, first_source)
        self._require_auth()
        opts = _build_options(model_version, ocr, formula, table, language, None, extra_formats)

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
            return self._submit_urls_batch(urls, opts)
        return self._upload_and_submit(files, opts)

    def get_task(self, task_id: str) -> ExtractResult:
        """Query a single task by task ID.

        This is a low-level method for querying tasks by their task ID
        (as returned by the ``/extract/task`` API endpoint). For results
        from :meth:`submit`, use :meth:`get_batch` instead — ``submit``
        always returns a batch ID.

        When ``state == "done"``, the result zip is downloaded and parsed
        automatically — ``markdown``, ``images``, etc. are populated.
        When the task is still running, ``markdown`` is ``None`` and
        ``progress`` contains page-level progress.

        Args:
            task_id: A task ID from the ``/extract/task`` endpoint.

        Returns:
            An :class:`ExtractResult` reflecting the current state.
        """
        body = self._require_auth().get(f"/extract/task/{task_id}")
        result = _parse_task_result(body["data"])
        if result.state == "done" and result.zip_url:
            return self._download_and_parse(result)
        return result

    def get_batch(self, batch_id: str) -> list[ExtractResult]:
        """Query all tasks in a batch.

        Use this to check results from :meth:`submit` (single file) or
        :meth:`submit_batch` (multiple files) — both return a batch ID.

        Each sub-task has its own state. Completed tasks have their content
        populated; in-progress tasks have ``markdown=None``.

        Example::

            # Single file
            batch_id = client.submit("report.pdf")
            results = client.get_batch(batch_id)
            print(results[0].markdown[:200])

            # Multiple files
            batch_id = client.submit_batch(["a.pdf", "b.pdf"])
            results = client.get_batch(batch_id)

        Args:
            batch_id: The batch ID returned by :meth:`submit` or
                :meth:`submit_batch`.

        Returns:
            A list of :class:`ExtractResult`, one per file in the batch.
        """
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

    def _submit_url(self, url: str, opts: dict) -> str:
        payload = {"url": url, **opts}
        body = self._require_auth().post("/extract/task", payload)
        return body["data"]["task_id"]

    def _submit_urls_batch(self, urls: list[str], opts: dict) -> str:
        files = [{"url": u} for u in urls]
        payload = {"files": files, **opts}
        body = self._require_auth().post("/extract/task/batch", payload)
        return body["data"]["batch_id"]

    def _upload_and_submit(self, file_paths: list[str], opts: dict) -> str:
        api = self._require_auth()
        files_meta = [{"name": Path(p).name} for p in file_paths]
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

    def _wait_single(self, task_id: str, timeout: int) -> ExtractResult:
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
        timeout: int = 300,
    ) -> ExtractResult:
        """Parse a document using the flash (agent) API.

        Flash mode requires no API token, only outputs Markdown, and is
        optimised for speed. No model selection, no extra formats.

        Example::

            client = MinerU()  # no token needed for flash mode
            result = client.flash_extract("report.pdf")
            print(result.markdown)

        Args:
            source: URL or local file path.
            language: Document language code. Default ``"ch"``.
            page_range: Page range, e.g. ``"1-10"``.
            timeout: Maximum seconds to wait.

        Returns:
            :class:`ExtractResult` with ``markdown`` populated. Other fields
            (``images``, ``docx``, ``html``, ``latex``) are always ``None``.

        Raises:
            TimeoutError: If the task does not complete within *timeout* seconds.
            FlashPageLimitError: If the document exceeds 50 pages.
            FlashFileTooLargeError: If the file exceeds 10 MB.
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
