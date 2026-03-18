"""Async submit + query tests — submit task_id / batch_id, query later."""

import time

from mineru import ExtractResult
from tests.conftest import TEST_HTML_URL, TEST_MODEL, TEST_PDF_URL


class TestSubmitAndGetTask:
    """Submit a task, get back a batch_id, query it later."""

    def test_submit_returns_batch_id(self, client):
        batch_id = client.submit(TEST_PDF_URL, model=TEST_MODEL)
        assert isinstance(batch_id, str)
        assert len(batch_id) > 0

    def test_get_task_returns_result(self, client):
        batch_id = client.submit(TEST_PDF_URL, model=TEST_MODEL)
        
        results = client.get_batch(batch_id)
        assert len(results) > 0
        assert isinstance(results[0], ExtractResult)
        assert results[0].state in ("done", "pending", "running", "failed", "converting")

    def test_get_task_eventually_done(self, client):
        """Submit, then poll get_task until done (uses HTML for speed)."""
        batch_id = client.submit(TEST_HTML_URL, model="html")
        results = client.get_batch(batch_id)

        for _ in range(120):
            results = client.get_batch(batch_id)
            if results[0].state in ("done", "failed"):
                break
            time.sleep(5)

        assert results[0].state == "done", f"Expected done, got {results[0].state}"
        assert results[0].markdown is not None


class TestSubmitBatchAndGetBatch:
    """Submit a batch, get back a batch_id, query it later."""

    def test_submit_batch_returns_batch_id(self, client):
        batch_id = client.submit_batch([TEST_PDF_URL, TEST_PDF_URL], model=TEST_MODEL)
        assert isinstance(batch_id, str)
        assert len(batch_id) > 0

    def test_get_batch_returns_list(self, client):
        batch_id = client.submit_batch([TEST_PDF_URL], model=TEST_MODEL)
        result = client.get_batch(batch_id)
        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(r, ExtractResult) for r in result)
