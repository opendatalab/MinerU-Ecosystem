"""Reproduce: uploading files > 50 MB times out on PUT.

The default httpx timeout in _api.py has write=30s, which is too short
for large file uploads.  This test uses a real 53 MB PDF to trigger it.

Run:
    cd sdk/python
    pytest tests/test_large_file_upload.py -v -s
"""

import os

import pytest
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))

from mineru import MinerU

# Path to the large test PDF (53 MB)
LARGE_PDF_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "mingzu.pdf")
)

TEST_MODEL = "pipeline"
TEST_TIMEOUT = 600


@pytest.fixture(scope="module")
def client():
    c = MinerU()
    yield c
    c.close()


class TestLargeFileUpload:
    """Upload a 53 MB PDF — expected to timeout with current 30s write timeout."""

    def test_upload_large_pdf(self, client):
        assert os.path.exists(LARGE_PDF_PATH), f"Test file not found: {LARGE_PDF_PATH}"

        size_mb = os.path.getsize(LARGE_PDF_PATH) / (1024 * 1024)
        print(f"\nUploading {LARGE_PDF_PATH} ({size_mb:.1f} MB) ...")

        # This should timeout with the current _TIMEOUT setting (write=30s)
        result = client.extract(LARGE_PDF_PATH, model=TEST_MODEL, timeout=TEST_TIMEOUT)
        assert result.state == "done"
        assert result.markdown is not None
        print(f"Extract done, markdown length: {len(result.markdown)}")
