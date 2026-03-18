"""Flash mode tests — unit tests (no API) + integration tests (real API)."""

import os

import pytest

from mineru import ExtractResult, MinerU, NoAuthClientError

FLASH_TEST_PDF_URL = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
FLASH_TEST_TIMEOUT = 300


# ═══════════════════════════════════════════════════════════════════
#  Unit tests — no API calls
# ═══════════════════════════════════════════════════════════════════


class TestFlashOnlyClient:
    """Creating a client without token should work for flash mode."""

    def test_no_token_creates_client(self):
        old = os.environ.pop("MINERU_TOKEN", None)
        try:
            c = MinerU()
            assert c is not None
        finally:
            if old is not None:
                os.environ["MINERU_TOKEN"] = old

    def test_extract_raises_no_auth(self):
        old = os.environ.pop("MINERU_TOKEN", None)
        try:
            c = MinerU()
            with pytest.raises(NoAuthClientError):
                c.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
        finally:
            if old is not None:
                os.environ["MINERU_TOKEN"] = old

    def test_crawl_raises_no_auth(self):
        old = os.environ.pop("MINERU_TOKEN", None)
        try:
            c = MinerU()
            with pytest.raises(NoAuthClientError):
                c.crawl("https://example.com")
        finally:
            if old is not None:
                os.environ["MINERU_TOKEN"] = old

    def test_submit_raises_no_auth(self):
        old = os.environ.pop("MINERU_TOKEN", None)
        try:
            c = MinerU()
            with pytest.raises(NoAuthClientError):
                c.submit("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
        finally:
            if old is not None:
                os.environ["MINERU_TOKEN"] = old

    def test_get_task_raises_no_auth(self):
        old = os.environ.pop("MINERU_TOKEN", None)
        try:
            c = MinerU()
            with pytest.raises(NoAuthClientError):
                c.get_task("fake-id")
        finally:
            if old is not None:
                os.environ["MINERU_TOKEN"] = old

    def test_authenticated_client_has_flash(self):
        """MinerU(token) should also have flash_extract available."""
        if not os.environ.get("MINERU_TOKEN"):
            pytest.skip("MINERU_TOKEN not set")
        c = MinerU()
        assert hasattr(c, "flash_extract")


# ═══════════════════════════════════════════════════════════════════
#  Integration tests — flash API (no token needed)
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def flash_client():
    c = MinerU()
    yield c
    c.close()


class TestFlashExtractURL:
    """Flash extract from a URL."""

    def test_returns_done_with_markdown(self, flash_client):
        result = flash_client.flash_extract(
            FLASH_TEST_PDF_URL,
            page_range="1-3",
            timeout=FLASH_TEST_TIMEOUT,
        )
        assert isinstance(result, ExtractResult)
        assert result.state == "done"
        assert result.markdown is not None
        assert len(result.markdown) > 0
        assert result.task_id != ""

    def test_with_language(self, flash_client):
        result = flash_client.flash_extract(
            FLASH_TEST_PDF_URL,
            language="en",
            page_range="1-1",
            timeout=FLASH_TEST_TIMEOUT,
        )
        assert result.state == "done"
        assert result.markdown is not None


class TestFlashExtractLocalFile:
    """Flash extract from a local file."""

    def test_local_pdf_returns_markdown(self, flash_client, tmp_path):
        pdf_bytes = (
            b"%PDF-1.0\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
            b"4 0 obj\n<< /Length 44 >>\nstream\n"
            b"BT /F1 24 Tf 100 700 Td (Hello MinerU) Tj ET\n"
            b"endstream\nendobj\n"
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            b"xref\n0 6\n"
            b"0000000000 65535 f \n"
            b"0000000009 00000 n \n"
            b"0000000058 00000 n \n"
            b"0000000115 00000 n \n"
            b"0000000266 00000 n \n"
            b"0000000360 00000 n \n"
            b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
            b"startxref\n435\n%%EOF\n"
        )
        path = tmp_path / "test_hello.pdf"
        path.write_bytes(pdf_bytes)

        result = flash_client.flash_extract(str(path), timeout=FLASH_TEST_TIMEOUT)
        assert result.state == "done"
        assert result.markdown is not None


class TestFlashExtractSave:
    """Flash results: save_markdown works, save_docx/html/latex raise."""

    def test_save_markdown(self, flash_client, tmp_path):
        result = flash_client.flash_extract(
            FLASH_TEST_PDF_URL,
            page_range="1-1",
            timeout=FLASH_TEST_TIMEOUT,
        )
        out = tmp_path / "output.md"
        result.save_markdown(str(out), with_images=False)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_no_docx_available(self, flash_client):
        result = flash_client.flash_extract(
            FLASH_TEST_PDF_URL,
            page_range="1-1",
            timeout=FLASH_TEST_TIMEOUT,
        )
        with pytest.raises(ValueError):
            result.save_docx("/tmp/out.docx")
        with pytest.raises(ValueError):
            result.save_html("/tmp/out.html")
        with pytest.raises(ValueError):
            result.save_latex("/tmp/out.tex")
