"""Extract tests — single PDF, local file, extra formats."""

from mineru import ExtractResult


class TestExtractSinglePDF:
    """Parse a single PDF from URL and get markdown."""

    def test_returns_done_with_markdown(self, pdf_result):
        assert isinstance(pdf_result, ExtractResult)
        assert pdf_result.state == "done"
        assert pdf_result.markdown is not None
        assert len(pdf_result.markdown) > 0

    def test_has_content_list(self, pdf_result):
        assert pdf_result.content_list is not None
        assert isinstance(pdf_result.content_list, list)

    def test_has_metadata(self, pdf_result):
        assert pdf_result.task_id
        assert pdf_result.zip_url is not None
        assert pdf_result.error is None


class TestExtractLocalFile:
    """Parse a local file — SDK handles upload automatically."""

    def test_local_pdf_returns_markdown(self, local_pdf_result):
        assert local_pdf_result.state == "done"
        assert local_pdf_result.markdown is not None


class TestExtractWithExtraFormats:
    """Request extra_formats and access the exported content."""

    def test_docx_export(self, pdf_result):
        assert pdf_result.state == "done"
        assert pdf_result.docx is not None
        assert len(pdf_result.docx) > 0

    def test_save_docx_to_file(self, pdf_result, tmp_path):
        out = tmp_path / "report.docx"
        pdf_result.save_docx(str(out))
        assert out.exists()
        assert out.stat().st_size > 0
