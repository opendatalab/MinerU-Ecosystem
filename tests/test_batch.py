"""Batch tests — extract_batch and crawl_batch."""

from mineru import ExtractResult
from tests.conftest import TEST_MODEL, TEST_PDF_URL, TEST_TIMEOUT


class TestExtractBatch:
    """Submit multiple documents and yield results as each completes."""

    def test_yields_all_results(self, client):
        urls = [TEST_PDF_URL, TEST_PDF_URL]
        results = list(client.extract_batch(urls, model=TEST_MODEL, timeout=TEST_TIMEOUT))

        assert len(results) == 2
        for r in results:
            assert isinstance(r, ExtractResult)
            assert r.state in ("done", "failed")

    def test_done_results_have_markdown(self, client):
        urls = [TEST_PDF_URL, TEST_PDF_URL]
        for result in client.extract_batch(urls, model=TEST_MODEL, timeout=TEST_TIMEOUT):
            if result.state == "done":
                assert result.markdown is not None
                assert len(result.markdown) > 0


class TestCrawlBatch:
    """Batch crawl web pages."""

    def test_yields_results(self, client):
        urls = ["https://www.example.com", "https://www.example.org"]
        results = list(client.crawl_batch(urls, timeout=TEST_TIMEOUT))

        assert len(results) == 2
        for r in results:
            assert r.state in ("done", "failed")
