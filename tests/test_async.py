"""Async submit + query tests — submit task_id / batch_id, query later."""

import time

from mineru import ExtractResult
from tests.conftest import TEST_HTML_URL, TEST_MODEL, TEST_PDF_URL


class TestSubmitAndGetTask:
    """Submit a task, get back a task_id, query it later."""

    def test_submit_returns_task_id(self, client):
        task_id = client.submit(TEST_PDF_URL, model=TEST_MODEL)
        assert isinstance(task_id, str)
        assert len(task_id) > 0

    def test_get_task_returns_result(self, client):
        task_id = client.submit(TEST_PDF_URL, model=TEST_MODEL)
        result = client.get_task(task_id)
        assert isinstance(result, ExtractResult)
        assert result.state in ("done", "pending", "running", "failed", "converting")

    def test_get_task_eventually_done(self, client):
        """Submit, then poll get_task until done (uses HTML for speed)."""
        task_id = client.submit(TEST_HTML_URL, model="html")

        for _ in range(120):
            result = client.get_task(task_id)
            if result.state in ("done", "failed"):
                break
            time.sleep(5)

        assert result.state == "done", f"Expected done, got {result.state}"
        assert result.markdown is not None


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
