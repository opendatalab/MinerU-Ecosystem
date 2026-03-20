from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfWriter

from langchain_mineru.document_loaders.mineru import _parse_page_range
from langchain_mineru.utils.pdf import (
    is_url,
    looks_like_pdf,
    split_pdf_to_single_page_files,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_dummy_pdf(path: Path, num_pages: int) -> None:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as f:
        writer.write(f)


# ---------------------------------------------------------------------------
# _parse_page_range
# ---------------------------------------------------------------------------


class TestParsePageRange:
    def test_range(self):
        assert _parse_page_range("1-5") == {1, 2, 3, 4, 5}

    def test_single_page(self):
        assert _parse_page_range("3") == {3}

    def test_single_page_range(self):
        assert _parse_page_range("2-2") == {2}

    def test_strips_whitespace(self):
        assert _parse_page_range("  2-4  ") == {2, 3, 4}

    def test_large_range(self):
        result = _parse_page_range("10-15")
        assert result == {10, 11, 12, 13, 14, 15}


# ---------------------------------------------------------------------------
# is_url
# ---------------------------------------------------------------------------


class TestIsUrl:
    @pytest.mark.parametrize("value", [
        "https://example.com/file.pdf",
        "http://example.com/file.pdf",
        "https://arxiv.org/pdf/2301.00001",
    ])
    def test_url_returns_true(self, value):
        assert is_url(value) is True

    @pytest.mark.parametrize("value", [
        "report.pdf",
        "/absolute/path/file.pdf",
        "./relative/file.pdf",
        "ftp://example.com/file.pdf",
    ])
    def test_non_url_returns_false(self, value):
        assert is_url(value) is False


# ---------------------------------------------------------------------------
# looks_like_pdf
# ---------------------------------------------------------------------------


class TestLooksLikePdf:
    def test_local_pdf_suffix(self):
        assert looks_like_pdf("report.pdf") is True

    def test_local_pdf_uppercase_suffix(self):
        assert looks_like_pdf("REPORT.PDF") is True

    def test_local_non_pdf(self):
        assert looks_like_pdf("report.docx") is False

    def test_url_with_pdf_suffix(self):
        assert looks_like_pdf("https://example.com/file.pdf") is True

    def test_url_with_pdf_suffix_and_query(self):
        assert looks_like_pdf("https://example.com/file.pdf?token=abc") is True

    def test_url_without_pdf_suffix_content_type_pdf(self):
        """URL without .pdf suffix should be detected via HEAD Content-Type."""
        mock_resp = MagicMock()
        mock_resp.headers.get.return_value = "application/pdf"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("langchain_mineru.utils.pdf.urlopen", return_value=mock_resp):
            result = looks_like_pdf("https://arxiv.org/pdf/2301.00001")
        assert result is True

    def test_url_without_pdf_suffix_content_type_html(self):
        """URL returning text/html should not be treated as PDF."""
        mock_resp = MagicMock()
        mock_resp.headers.get.return_value = "text/html; charset=utf-8"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("langchain_mineru.utils.pdf.urlopen", return_value=mock_resp):
            result = looks_like_pdf("https://example.com/page")
        assert result is False

    def test_url_head_request_fails_returns_false(self):
        """If HEAD request fails, conservatively return False."""
        with patch("langchain_mineru.utils.pdf.urlopen", side_effect=Exception("timeout")):
            result = looks_like_pdf("https://example.com/unknown")
        assert result is False


# ---------------------------------------------------------------------------
# split_pdf_to_single_page_files
# ---------------------------------------------------------------------------


class TestSplitPdfToSinglePageFiles:
    def test_splits_all_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=3)

            temp_dir, page_files = split_pdf_to_single_page_files(pdf_path)
            try:
                assert len(page_files) == 3
                page_numbers = [p for p, _ in page_files]
                assert page_numbers == [1, 2, 3]
                for _, path in page_files:
                    assert path.exists()
                    assert path.suffix == ".pdf"
            finally:
                temp_dir.cleanup()

    def test_splits_subset_of_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=5)

            temp_dir, page_files = split_pdf_to_single_page_files(
                pdf_path, page_numbers={1, 3, 5}
            )
            try:
                assert len(page_files) == 3
                page_numbers = [p for p, _ in page_files]
                assert page_numbers == [1, 3, 5]
            finally:
                temp_dir.cleanup()

    def test_page_numbers_none_returns_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=4)

            temp_dir, page_files = split_pdf_to_single_page_files(
                pdf_path, page_numbers=None
            )
            try:
                assert len(page_files) == 4
            finally:
                temp_dir.cleanup()

    def test_out_of_range_page_numbers_ignored(self):
        """Page numbers beyond total pages should be silently skipped."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=3)

            temp_dir, page_files = split_pdf_to_single_page_files(
                pdf_path, page_numbers={1, 2, 99}
            )
            try:
                assert len(page_files) == 2
                page_numbers = [p for p, _ in page_files]
                assert 99 not in page_numbers
            finally:
                temp_dir.cleanup()

    def test_each_split_file_is_single_page(self):
        """Each output file must be a valid single-page PDF."""
        from pypdf import PdfReader

        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=3)

            temp_dir, page_files = split_pdf_to_single_page_files(pdf_path)
            try:
                for _, page_path in page_files:
                    reader = PdfReader(str(page_path))
                    assert len(reader.pages) == 1
            finally:
                temp_dir.cleanup()
