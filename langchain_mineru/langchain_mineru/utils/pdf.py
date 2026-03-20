from __future__ import annotations

import logging
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def looks_like_pdf(value: str) -> bool:
    """Check whether *value* (path or URL) appears to be a PDF.

    1. Strip query string and check the path suffix.
    2. For URLs where the suffix is inconclusive, send a HEAD request
       and inspect the Content-Type header.
    """
    parsed = urlparse(value)

    path_suffix = PurePosixPath(parsed.path).suffix.lower()
    if path_suffix == ".pdf":
        return True

    if parsed.scheme not in {"http", "https"}:
        return False

    try:
        req = Request(value, method="HEAD")
        with urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "")
            return "application/pdf" in content_type.lower()
    except Exception:
        logger.debug("HEAD request failed for %s, assuming not PDF", value)
        return False


def download_url_to_temp_pdf(url: str) -> tuple[TemporaryDirectory, Path]:
    """Download a URL to a temporary local PDF file.

    Returns:
        A tuple of (TemporaryDirectory, downloaded_pdf_path).

    Notes:
        - Caller must keep the returned TemporaryDirectory alive while using the file.
        - Caller is responsible for cleanup().
    """
    temp_dir = TemporaryDirectory()
    pdf_path = Path(temp_dir.name) / "downloaded.pdf"

    with urlopen(url) as response:
        content = response.read()

    pdf_path.write_bytes(content)
    return temp_dir, pdf_path


def split_pdf_to_single_page_files(
    pdf_path: str | Path,
    page_numbers: set[int] | None = None,
) -> tuple[TemporaryDirectory, list[tuple[int, Path]]]:
    """Split a PDF into many one-page temporary PDF files.

    Args:
        pdf_path: Path to the source PDF.
        page_numbers: If provided, only extract these 1-based page numbers.
            Pages outside this set are skipped.

    Returns:
        (temp_dir, [(page_number, page_file_path), ...])

    Notes:
        - page_number starts from 1.
        - Caller must cleanup temp_dir.
    """
    pdf_path = Path(pdf_path)
    reader = PdfReader(str(pdf_path))

    temp_dir = TemporaryDirectory()
    temp_root = Path(temp_dir.name)
    page_files: list[tuple[int, Path]] = []

    for page_number, page in enumerate(reader.pages, start=1):
        if page_numbers is not None and page_number not in page_numbers:
            continue

        writer = PdfWriter()
        writer.add_page(page)

        page_path = temp_root / f"{pdf_path.stem}_page_{page_number}.pdf"
        with page_path.open("wb") as f:
            writer.write(f)

        page_files.append((page_number, page_path))

    return temp_dir, page_files