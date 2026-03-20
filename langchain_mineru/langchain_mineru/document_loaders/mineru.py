from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

from langchain_mineru.utils.pdf import (
    download_url_to_temp_pdf,
    is_url,
    looks_like_pdf,
    split_pdf_to_single_page_files,
)

_SOURCE_TAG = "langchain-mineru"


def _parse_page_range(page_range: str) -> set[int]:
    """Parse a page range string into a set of 1-based page numbers.

    Supports "N-M" (e.g. "1-5") and single page "N" (e.g. "3").
    """
    page_range = page_range.strip()
    if "-" in page_range:
        start_s, end_s = page_range.split("-", 1)
        start, end = int(start_s), int(end_s)
        return set(range(start, end + 1))
    return {int(page_range)}


class MinerULoader(BaseLoader):
    """LangChain Document Loader for MinerU.

    Supports two parsing modes:
    - fast: uses MinerU flash API (no token required)
    - accurate: uses MinerU standard extract API (token required)

    Design:
    - Only implement lazy_load(); BaseLoader.load() will consume it.
    - One source -> one Document by default.
    - split_pages=True:
        * local PDF  -> split into one-page temp PDFs, one page one Document
        * URL PDF    -> download to temp PDF, split, one page one Document
        * non-PDF    -> still one source one Document
    - page_content is always Markdown.
    """

    def __init__(
        self,
        source: str | list[str],
        language: str = "ch",
        pages: str | None = None,
        timeout: int = 1200,
        split_pages: bool = False,
        mode: str = "fast",
        token: str | None = None,
        ocr: bool = False,
        formula: bool = True,
        table: bool = True,
    ) -> None:
        self.source = source
        self.language = language
        self.pages = pages
        self.timeout = timeout
        self.split_pages = split_pages
        self.mode = mode
        self.token = token
        self.ocr = ocr
        self.formula = formula
        self.table = table

        self._validate()
        self._client = self._create_client()

    def _create_client(self):
        try:
            from mineru import MinerU
        except ImportError as exc:
            raise ImportError(
                "MinerU SDK is required to use MinerULoader. "
                "Install with: pip install mineru-open-sdk"
            ) from exc

        client = MinerU(token=self.token)
        client.set_source(_SOURCE_TAG)
        return client

    def _validate(self) -> None:
        if isinstance(self.source, list) and len(self.source) == 0:
            raise ValueError("source list must not be empty")
        if self.mode not in {"fast", "accurate"}:
            raise ValueError("mode must be 'fast' or 'accurate'")
        if self.mode == "fast":
            if self.formula is not True or self.table is not True:
                raise ValueError(
                    "formula/table are only supported in accurate mode. "
                    "Use mode='accurate' to enable them."
                )
        if self.mode == "accurate" and not (self.token or os.environ.get("MINERU_TOKEN")):
            raise ValueError(
                "accurate mode requires token. "
                "Pass token=... or set MINERU_TOKEN in environment."
            )

    def lazy_load(self) -> Iterator[Document]:
        """Yield Document objects lazily.

        BaseLoader.load() will internally consume this iterator and return list[Document].
        """
        sources = [self.source] if isinstance(self.source, str) else self.source

        for src in sources:
            yield from self._lazy_load_single_source(src)

    def _lazy_load_single_source(self, src: str) -> Iterator[Document]:
        if self.split_pages and self._should_split_pdf(src):
            yield from self._lazy_load_split_pdf(src)
            return

        result = self._extract(src)
        self._raise_if_not_done(result, source=src, page=None)

        yield Document(
            page_content=self._result_to_page_content(result),
            metadata=self._build_metadata(
                original_source=src,
                result=result,
                page=None,
                page_source=None,
            ),
        )

    def _should_split_pdf(self, src: str) -> bool:
        """Whether this input should enter split_pages flow."""
        return looks_like_pdf(src)

    def _lazy_load_split_pdf(self, src: str) -> Iterator[Document]:
        """Split one PDF source into one-page temporary PDFs, then parse each page."""
        download_temp_dir: TemporaryDirectory | None = None
        split_temp_dir: TemporaryDirectory | None = None

        try:
            if is_url(src):
                download_temp_dir, local_pdf_path = download_url_to_temp_pdf(src)
            else:
                local_pdf_path = Path(src)
                if not local_pdf_path.exists():
                    raise FileNotFoundError(f"PDF file not found: {src}")

            target_pages = _parse_page_range(self.pages) if self.pages else None
            split_temp_dir, page_files = split_pdf_to_single_page_files(
                local_pdf_path, page_numbers=target_pages,
            )

            for page_number, page_path in page_files:
                result = self._extract(str(page_path), use_page_range=False)
                self._raise_if_not_done(result, source=src, page=page_number)

                yield Document(
                    page_content=self._result_to_page_content(result),
                    metadata=self._build_metadata(
                        original_source=src,
                        result=result,
                        page=page_number,
                        page_source=src,
                    ),
                )
        finally:
            if split_temp_dir is not None:
                split_temp_dir.cleanup()
            if download_temp_dir is not None:
                download_temp_dir.cleanup()

    def _extract(self, src: str, use_page_range: bool = True):
        """Call MinerU API synchronously.

        Args:
            src: File path or URL.
            use_page_range: Whether to forward self.pages to the API.
                Set to False when the file is already a single-page PDF
                produced by local splitting.
        """
        kwargs: dict = {"language": self.language, "timeout": self.timeout}

        if self.mode == "fast":
            if use_page_range and self.pages:
                kwargs["page_range"] = self.pages
            return self._client.flash_extract(src, **kwargs)

        kwargs.update(
            {
                "ocr": self.ocr,
                "formula": self.formula,
                "table": self.table,
            }
        )
        if use_page_range and self.pages:
            kwargs["pages"] = self.pages
        return self._client.extract(src, **kwargs)

    def _result_to_page_content(self, result) -> str:
        """Convert ExtractResult into Document.page_content (Markdown)."""
        content = getattr(result, "markdown", None)
        if not content:
            raise ValueError("MinerU result.markdown is empty")
        return content

    def _build_metadata(
        self,
        original_source: str,
        result,
        page: int | None,
        page_source: str | None,
    ) -> dict:
        metadata = {
            "source": original_source,
            "loader": "mineru",
            "output_format": "markdown",
            "mode": self.mode,
            "language": self.language,
            "pages": self.pages,
            "split_pages": self.split_pages,
            "filename": getattr(result, "filename", None),
        }

        if page is not None:
            metadata["page"] = page

        if page_source is not None:
            metadata["page_source"] = page_source

        return metadata

    def _raise_if_not_done(self, result, source: str, page: int | None) -> None:
        state = getattr(result, "state", None)
        if state == "done":
            return

        error = getattr(result, "error", None)
        location = f", page={page}" if page is not None else ""
        raise ValueError(
            f"MinerU extraction failed: source={source}{location}, state={state}, error={error}"
        )
