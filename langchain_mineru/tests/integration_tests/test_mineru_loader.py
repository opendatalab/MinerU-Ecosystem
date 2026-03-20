"""Integration tests for MinerULoader.

These tests make REAL network calls to the MinerU flash API.
They require network access and may take tens of seconds each.

Run with:
    pytest tests/integration_tests/ -v

Or a single test:
    pytest tests/integration_tests/test_mineru_loader.py::TestMinerULoaderIntegration::test_load_pdf
"""
from __future__ import annotations

import pytest

from langchain_mineru import MinerULoader

# ---------------------------------------------------------------------------
# Fixtures directory (place a small PDF here for testing)
# ---------------------------------------------------------------------------
FIXTURE_PDF = "tests/integration_tests/fixtures/sample.pdf"
FIXTURE_URL = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestMinerULoaderIntegration:
    """End-to-end tests requiring access to MinerU flash API."""

    def test_load_local_pdf_returns_documents(self):
        """Loading a local PDF returns at least one Document with content."""
        loader = MinerULoader(source=FIXTURE_PDF)
        docs = loader.load()

        assert len(docs) >= 1
        assert docs[0].page_content.strip()
        assert docs[0].metadata["loader"] == "mineru"
        assert docs[0].metadata["source"] == FIXTURE_PDF
        assert docs[0].metadata["output_format"] == "markdown"

    def test_load_local_pdf_split_pages(self):
        """split_pages=True yields one Document per page, each with metadata['page']."""
        loader = MinerULoader(source=FIXTURE_PDF, split_pages=True)
        docs = loader.load()

        assert len(docs) >= 1
        for doc in docs:
            assert "page" in doc.metadata
            assert doc.metadata["page"] >= 1
            assert doc.metadata["source"] == FIXTURE_PDF
            assert doc.page_content.strip()

    def test_load_local_pdf_with_page_range(self):
        """pages='1-2' limits extraction to the first 2 pages (non-split mode)."""
        loader = MinerULoader(source=FIXTURE_PDF, pages="1-2")
        docs = loader.load()

        assert len(docs) == 1
        assert docs[0].metadata["pages"] == "1-2"
        assert docs[0].page_content.strip()

    def test_load_local_pdf_split_pages_with_range(self):
        """split_pages=True + pages='1-2' → exactly 2 Documents."""
        loader = MinerULoader(source=FIXTURE_PDF, split_pages=True, pages="1-2")
        docs = loader.load()

        assert len(docs) == 2
        assert docs[0].metadata["page"] == 1
        assert docs[1].metadata["page"] == 2

    def test_load_url_pdf(self):
        """Loading a PDF from a URL returns a Document with Markdown content."""
        loader = MinerULoader(source=FIXTURE_URL, language="en")
        docs = loader.load()

        assert len(docs) >= 1
        assert docs[0].page_content.strip()
        assert docs[0].metadata["source"] == FIXTURE_URL

    def test_lazy_load_yields_documents(self):
        """lazy_load() is a generator that yields Documents one at a time."""
        loader = MinerULoader(source=FIXTURE_PDF)
        docs = list(loader.lazy_load())

        assert len(docs) >= 1
        assert all(doc.page_content for doc in docs)

    def test_multi_source(self):
        """Multiple sources in a list produce one Document per source."""
        loader = MinerULoader(source=[FIXTURE_PDF, FIXTURE_PDF])
        docs = loader.load()

        assert len(docs) == 2
        for doc in docs:
            assert doc.metadata["source"] == FIXTURE_PDF

    def test_metadata_no_task_id_or_state(self):
        """task_id and state must NOT appear in returned Document metadata."""
        loader = MinerULoader(source=FIXTURE_PDF)
        docs = loader.load()

        meta = docs[0].metadata
        assert "task_id" not in meta
        assert "state" not in meta

    def test_language_en(self):
        """language='en' param is accepted and reflected in metadata."""
        loader = MinerULoader(source=FIXTURE_PDF, language="en")
        docs = loader.load()

        assert docs[0].metadata["language"] == "en"
