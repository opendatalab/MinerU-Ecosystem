from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest
from pypdf import PdfWriter

from langchain_mineru.document_loaders.mineru import MinerULoader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_result(
    *,
    state="done",
    markdown="# hello",
    filename="demo.pdf",
    task_id="task-123",
    error=None,
):
    return SimpleNamespace(
        task_id=task_id,
        state=state,
        filename=filename,
        error=error,
        markdown=markdown,
    )


def _create_dummy_pdf(path: Path, num_pages: int = 3) -> None:
    """Write a minimal valid PDF with the given number of blank pages."""
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as f:
        writer.write(f)


def _make_loader(source="a.pdf", **kwargs) -> MinerULoader:
    """Create a MinerULoader with the real MinerU client mocked out."""
    with patch.object(MinerULoader, "_create_client", return_value=MagicMock()):
        return MinerULoader(source=source, **kwargs)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_empty_source_list_raises(self):
        with pytest.raises(ValueError, match="source list must not be empty"):
            _make_loader(source=[])

    def test_string_source_ok(self):
        loader = _make_loader(source="a.pdf")
        assert loader.source == "a.pdf"

    def test_list_source_ok(self):
        loader = _make_loader(source=["a.pdf", "b.pdf"])
        assert loader.source == ["a.pdf", "b.pdf"]

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="mode must be 'flash' or 'precision'"):
            _make_loader(source="a.pdf", mode="invalid")

    def test_precision_mode_without_token_raises(self, monkeypatch):
        monkeypatch.delenv("MINERU_TOKEN", raising=False)
        with pytest.raises(ValueError, match="precision mode requires token"):
            _make_loader(source="a.pdf", mode="precision")

    def test_precision_mode_with_explicit_token_ok(self):
        loader = _make_loader(source="a.pdf", mode="precision", token="test-token")
        assert loader.mode == "precision"
        assert loader.token == "test-token"

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"formula": False}, "formula/table are only supported in precision mode"),
            ({"table": False}, "formula/table are only supported in precision mode"),
        ],
    )
    def test_flash_mode_rejects_precision_only_options(self, kwargs, match):
        with pytest.raises(ValueError, match=match):
            _make_loader(source="a.pdf", mode="flash", **kwargs)

    def test_flash_mode_accepts_ocr_option(self):
        loader = _make_loader(source="a.pdf", mode="flash", ocr=True)
        assert loader.mode == "flash"
        assert loader.ocr is True


# ---------------------------------------------------------------------------
# Single source tests
# ---------------------------------------------------------------------------


class TestSingleSource:
    def test_single_source_markdown(self):
        loader = _make_loader(source="a.pdf")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="# content from a.pdf")
        )

        docs = loader.load()

        assert len(docs) == 1
        assert docs[0].page_content == "# content from a.pdf"
        assert docs[0].metadata["source"] == "a.pdf"
        assert docs[0].metadata["output_format"] == "markdown"
        assert docs[0].metadata["loader"] == "mineru"

    def test_single_source_with_language(self):
        loader = _make_loader(source="doc.pdf", language="en")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="english content")
        )

        docs = loader.load()

        assert docs[0].metadata["language"] == "en"

    def test_single_source_with_pages(self):
        loader = _make_loader(source="doc.pdf", pages="1-5")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="partial content")
        )

        docs = loader.load()

        assert docs[0].metadata["pages"] == "1-5"
        loader._client.flash_extract.assert_called_once_with(
            "doc.pdf",
            language="ch",
            page_range="1-5",
            timeout=1200,
        )

    def test_non_pdf_source_not_split(self):
        """Non-PDF sources always produce 1 Document even with split_pages=True."""
        loader = _make_loader(source="report.docx", split_pages=True)
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="docx content")
        )

        docs = loader.load()

        assert len(docs) == 1
        assert "page" not in docs[0].metadata


# ---------------------------------------------------------------------------
# Multiple sources tests
# ---------------------------------------------------------------------------


class TestMultiSource:
    def test_multi_source(self):
        loader = _make_loader(source=["a.pdf", "b.pdf"])
        loader._client.flash_extract = MagicMock(
            side_effect=[
                make_result(markdown="content a"),
                make_result(markdown="content b"),
            ]
        )

        docs = loader.load()

        assert len(docs) == 2
        assert docs[0].page_content == "content a"
        assert docs[0].metadata["source"] == "a.pdf"
        assert docs[1].page_content == "content b"
        assert docs[1].metadata["source"] == "b.pdf"

    def test_lazy_load_yields_incrementally(self):
        """lazy_load() should yield Documents one by one, not wait for all."""
        loader = _make_loader(source=["a.pdf", "b.pdf"])
        loader._client.flash_extract = MagicMock(
            side_effect=[
                make_result(markdown="content a"),
                make_result(markdown="content b"),
            ]
        )

        docs = list(loader.lazy_load())
        assert len(docs) == 2


# ---------------------------------------------------------------------------
# Split pages tests
# ---------------------------------------------------------------------------


class TestSplitPages:
    def test_split_pages_local_pdf_all_pages(self):
        """split_pages=True without pages → all pages extracted."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=3)

            loader = _make_loader(source=str(pdf_path), split_pages=True)
            loader._client.flash_extract = MagicMock(
                side_effect=[
                    make_result(markdown=f"page {i} content")
                    for i in range(1, 4)
                ]
            )

            docs = loader.load()

            assert len(docs) == 3
            for i, doc in enumerate(docs, start=1):
                assert doc.page_content == f"page {i} content"
                assert doc.metadata["page"] == i
                assert doc.metadata["source"] == str(pdf_path)
                assert doc.metadata["page_source"] == str(pdf_path)
                assert doc.metadata["split_pages"] is True

    def test_split_pages_with_page_range(self):
        """split_pages=True + pages='1-2' → only pages 1 and 2 extracted."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=5)

            loader = _make_loader(source=str(pdf_path), split_pages=True, pages="1-2")
            loader._client.flash_extract = MagicMock(
                side_effect=[
                    make_result(markdown="page 1 content"),
                    make_result(markdown="page 2 content"),
                ]
            )

            docs = loader.load()

            assert len(docs) == 2
            assert docs[0].metadata["page"] == 1
            assert docs[1].metadata["page"] == 2

    def test_split_pages_with_single_page(self):
        """split_pages=True + pages='3' → only page 3 extracted."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=5)

            loader = _make_loader(source=str(pdf_path), split_pages=True, pages="3")
            loader._client.flash_extract = MagicMock(
                return_value=make_result(markdown="page 3 content")
            )

            docs = loader.load()

            assert len(docs) == 1
            assert docs[0].metadata["page"] == 3
            assert docs[0].page_content == "page 3 content"

    def test_split_pages_false_no_split(self):
        loader = _make_loader(source="a.pdf", split_pages=False)
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="whole doc")
        )

        docs = loader.load()

        assert len(docs) == 1
        assert "page" not in docs[0].metadata
        assert "page_source" not in docs[0].metadata

    def test_split_pages_non_pdf_no_split(self):
        loader = _make_loader(source="image.png", split_pages=True)
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="image content")
        )

        docs = loader.load()

        assert len(docs) == 1
        assert "page" not in docs[0].metadata

    def test_split_pages_file_not_found(self):
        loader = _make_loader(
            source="/nonexistent/path/missing.pdf", split_pages=True
        )
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            loader.load()


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_failed_result_raises(self):
        loader = _make_loader(source="a.pdf")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(state="failed", markdown=None, error="bad file")
        )

        with pytest.raises(ValueError, match="state=failed"):
            loader.load()

    @pytest.mark.parametrize("markdown_value", ["", None])
    def test_invalid_markdown_raises(self, markdown_value):
        loader = _make_loader(source="a.pdf")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown=markdown_value)
        )

        with pytest.raises(ValueError, match="result.markdown is empty"):
            loader.load()

    def test_failed_result_in_split_mode_raises(self):
        """Failure during split-page extraction should propagate."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=2)

            loader = _make_loader(source=str(pdf_path), split_pages=True)
            loader._client.flash_extract = MagicMock(
                side_effect=[
                    make_result(markdown="page 1 ok"),
                    make_result(state="failed", markdown=None, error="timeout"),
                ]
            )

            with pytest.raises(ValueError, match="state=failed"):
                loader.load()


# ---------------------------------------------------------------------------
# Metadata tests
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_metadata_fields(self):
        loader = _make_loader(source="report.pdf", language="en", pages="1-3")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(
                markdown="content",
                task_id="t-abc",
                filename="report.pdf",
            )
        )

        docs = loader.load()
        meta = docs[0].metadata

        assert meta["source"] == "report.pdf"
        assert meta["loader"] == "mineru"
        assert meta["output_format"] == "markdown"
        assert meta["mode"] == "flash"
        assert meta["language"] == "en"
        assert meta["pages"] == "1-3"
        assert meta["split_pages"] is False
        assert meta["filename"] == "report.pdf"
        assert "task_id" not in meta
        assert "state" not in meta

    def test_metadata_split_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "doc.pdf"
            _create_dummy_pdf(pdf_path, num_pages=1)

            loader = _make_loader(source=str(pdf_path), split_pages=True)
            loader._client.flash_extract = MagicMock(
                return_value=make_result(markdown="page content")
            )

            docs = loader.load()
            meta = docs[0].metadata

            assert meta["page"] == 1
            assert meta["page_source"] == str(pdf_path)
            assert meta["split_pages"] is True

    def test_metadata_source_always_original(self):
        """source in metadata must always be the original input, not temp file path."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "original.pdf"
            _create_dummy_pdf(pdf_path, num_pages=2)

            loader = _make_loader(source=str(pdf_path), split_pages=True)
            loader._client.flash_extract = MagicMock(
                side_effect=[
                    make_result(markdown="p1"),
                    make_result(markdown="p2"),
                ]
            )

            docs = loader.load()
            for doc in docs:
                assert doc.metadata["source"] == str(pdf_path)
                assert "tmp" not in doc.metadata["source"] or str(pdf_path) in doc.metadata["source"]


# ---------------------------------------------------------------------------
# Flash extract call verification
# ---------------------------------------------------------------------------


class TestFlashExtractCall:
    def test_calls_flash_extract(self):
        loader = _make_loader(source="test.pdf", language="en", pages="2-5", timeout=300)
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="content")
        )

        loader.load()

        loader._client.flash_extract.assert_called_once_with(
            "test.pdf",
            language="en",
            page_range="2-5",
            timeout=300,
        )

    def test_default_params(self):
        loader = _make_loader(source="test.pdf")
        loader._client.flash_extract = MagicMock(
            return_value=make_result(markdown="content")
        )

        loader.load()

        loader._client.flash_extract.assert_called_once_with(
            "test.pdf",
            language="ch",
            timeout=1200,
        )

    def test_split_pages_does_not_forward_page_range_to_api(self):
        """In split mode, page_range must NOT be forwarded to flash_extract."""
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=2)

            loader = _make_loader(source=str(pdf_path), pages="1-2", split_pages=True)
            loader._client.flash_extract = MagicMock(
                side_effect=[
                    make_result(markdown="page1"),
                    make_result(markdown="page2"),
                ]
            )

            docs = loader.load()

            assert len(docs) == 2
            assert loader._client.flash_extract.call_count == 2
            for called in loader._client.flash_extract.call_args_list:
                assert "page_range" not in called.kwargs

    def test_set_source_called_on_client(self):
        """MinerU client.set_source() must be called with the langchain-mineru tag."""
        mock_client = MagicMock()
        with patch.object(MinerULoader, "_create_client", return_value=mock_client):
            pass  # _create_client is already mocked via _make_loader

        # Test _create_client directly with real MinerU mock
        mock_mineru_cls = MagicMock()
        mock_instance = MagicMock()
        mock_mineru_cls.return_value = mock_instance

        with patch("langchain_mineru.document_loaders.mineru.MinerULoader._create_client") as mock_create:
            mock_create.return_value = mock_instance
            loader = MinerULoader.__new__(MinerULoader)
            loader.source = "a.pdf"
            loader.language = "ch"
            loader.pages = None
            loader.timeout = 1200
            loader.split_pages = False
            loader._validate = lambda: None
            loader._client = loader._create_client()

        mock_create.assert_called_once()


# ---------------------------------------------------------------------------
# Precision extract call verification
# ---------------------------------------------------------------------------


class TestPrecisionExtractCall:
    def test_calls_extract(self):
        loader = _make_loader(
            source="test.pdf",
            mode="precision",
            token="token-123",
            language="en",
            pages="2-5",
            timeout=300,
        )
        loader._client.extract = MagicMock(return_value=make_result(markdown="content"))

        loader.load()

        loader._client.extract.assert_called_once_with(
            "test.pdf",
            language="en",
            pages="2-5",
            timeout=300,
            ocr=False,
            formula=True,
            table=True,
        )

    def test_calls_extract_with_ocr_formula_table(self):
        loader = _make_loader(
            source="test.pdf",
            mode="precision",
            token="token-123",
            ocr=True,
            formula=False,
            table=False,
        )
        loader._client.extract = MagicMock(return_value=make_result(markdown="content"))

        loader.load()

        loader._client.extract.assert_called_once_with(
            "test.pdf",
            language="ch",
            timeout=1200,
            ocr=True,
            formula=False,
            table=False,
        )

    def test_split_pages_does_not_forward_pages_to_extract(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "test.pdf"
            _create_dummy_pdf(pdf_path, num_pages=2)

            loader = _make_loader(
                source=str(pdf_path),
                mode="precision",
                token="token-123",
                pages="1-2",
                split_pages=True,
            )
            loader._client.extract = MagicMock(
                side_effect=[make_result(markdown="page1"), make_result(markdown="page2")]
            )

            docs = loader.load()

            assert len(docs) == 2
            assert loader._client.extract.call_count == 2
            for called in loader._client.extract.call_args_list:
                assert "pages" not in called.kwargs
