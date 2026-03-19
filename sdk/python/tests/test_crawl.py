"""Crawl tests — crawl a web page and parse to Markdown."""

from mineru import ExtractResult
from tests.conftest import TEST_HTML_URL, TEST_TIMEOUT


class TestCrawlSinglePage:
    """Crawl a web page and parse it to Markdown."""

    def test_returns_markdown(self, client):
        result = client.crawl(TEST_HTML_URL, timeout=TEST_TIMEOUT)

        assert isinstance(result, ExtractResult)
        assert result.state == "done"
        assert result.markdown is not None
        assert len(result.markdown) > 0

    def test_equivalent_to_extract_with_html_model(self, client):
        result = client.extract(TEST_HTML_URL, model="html", timeout=TEST_TIMEOUT)

        assert result.state == "done"
        assert result.markdown is not None
