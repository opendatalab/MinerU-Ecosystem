"""Shared fixtures for integration tests.

These tests hit the real MinerU API. Requires MINERU_TOKEN env var.
"""

import pytest

from mineru import MinerU

TEST_PDF_URL = "https://bitcoin.org/bitcoin.pdf"

TEST_MODEL = "pipeline"

TEST_HTML_URL = "https://opendatalab.com"

TEST_TIMEOUT = 600


@pytest.fixture(scope="session")
def client():
    """A shared MinerU client for the entire test session."""
    c = MinerU()
    yield c
    c.close()


@pytest.fixture(scope="session")
def pdf_result(client):
    """Extract the demo PDF once with docx export, shared across all tests."""
    return client.extract(
        TEST_PDF_URL,
        model=TEST_MODEL,
        extra_formats=["docx"],
        timeout=TEST_TIMEOUT,
    )


@pytest.fixture(scope="session")
def local_pdf_result(client, tmp_path_factory):
    """Upload and extract a minimal local PDF, shared across tests."""
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
    path = tmp_path_factory.mktemp("data") / "test_hello.pdf"
    path.write_bytes(pdf_bytes)
    return client.extract(str(path), model=TEST_MODEL, timeout=TEST_TIMEOUT)
