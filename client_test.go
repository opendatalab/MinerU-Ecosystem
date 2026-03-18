package mineru_test

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	mineru "github.com/OpenDataLab/mineru-open-sdk"
)

// Test constants — mirrors the Python SDK test suite.
const (
	testPDFURL  = "https://bitcoin.org/bitcoin.pdf"
	testModel   = "pipeline"
	testHTMLURL = "https://opendatalab.com"
	testTimeout = 10 * time.Minute
)

// Shared results — populated once in TestMain, reused by all tests.
var (
	client         *mineru.Client
	pdfResult      *mineru.ExtractResult
	localPDFResult *mineru.ExtractResult
)

func TestMain(m *testing.M) {
	var err error
	client, err = mineru.New("")
	if err != nil {
		// No token — skip standard API setup, flash tests can still run.
		os.Exit(m.Run())
	}

	ctx := context.Background()

	// One extract call with docx export — shared across all PDF tests.
	pdfResult, err = client.Extract(ctx, testPDFURL,
		mineru.WithModel(testModel),
		mineru.WithExtraFormats("docx"),
		mineru.WithPollTimeout(testTimeout),
	)
	if err != nil {
		panic("failed to extract test PDF: " + err.Error())
	}

	// Local file upload test — minimal 1-page PDF.
	tmpDir, _ := os.MkdirTemp("", "mineru-test-*")
	defer os.RemoveAll(tmpDir)
	localPDF := filepath.Join(tmpDir, "test_hello.pdf")
	os.WriteFile(localPDF, minimalPDF, 0o644)

	localPDFResult, err = client.Extract(ctx, localPDF,
		mineru.WithModel(testModel),
		mineru.WithPollTimeout(testTimeout),
	)
	if err != nil {
		panic("failed to extract local PDF: " + err.Error())
	}

	os.Exit(m.Run())
}

// Minimal valid PDF (1 page, "Hello MinerU").
var minimalPDF = []byte(
	"%PDF-1.0\n" +
		"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n" +
		"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n" +
		"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] " +
		"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n" +
		"4 0 obj\n<< /Length 44 >>\nstream\n" +
		"BT /F1 24 Tf 100 700 Td (Hello MinerU) Tj ET\n" +
		"endstream\nendobj\n" +
		"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n" +
		"xref\n0 6\n" +
		"0000000000 65535 f \n" +
		"0000000009 00000 n \n" +
		"0000000058 00000 n \n" +
		"0000000115 00000 n \n" +
		"0000000266 00000 n \n" +
		"0000000360 00000 n \n" +
		"trailer\n<< /Size 6 /Root 1 0 R >>\n" +
		"startxref\n435\n%%EOF\n",
)

// ═══════════════════════════════════════════════════════════════════
//  Extract — single PDF
// ═══════════════════════════════════════════════════════════════════

func requireStandardClient(t *testing.T) {
	t.Helper()
	if client == nil {
		t.Skip("MINERU_TOKEN not set, skipping standard API test")
	}
}

func requirePDFResult(t *testing.T) {
	t.Helper()
	requireStandardClient(t)
	if pdfResult == nil {
		t.Skip("pdfResult not available")
	}
}

func requireLocalPDFResult(t *testing.T) {
	t.Helper()
	requireStandardClient(t)
	if localPDFResult == nil {
		t.Skip("localPDFResult not available")
	}
}

func TestExtract_ReturnsDoneWithMarkdown(t *testing.T) {
	requirePDFResult(t)
	if pdfResult.State != "done" {
		t.Fatalf("expected state=done, got %s", pdfResult.State)
	}
	if pdfResult.Markdown == "" {
		t.Fatal("markdown is empty")
	}
}

func TestExtract_HasContentList(t *testing.T) {
	requirePDFResult(t)
	if pdfResult.ContentList == nil {
		t.Fatal("content_list is nil")
	}
	if len(pdfResult.ContentList) == 0 {
		t.Fatal("content_list is empty")
	}
}

func TestExtract_HasMetadata(t *testing.T) {
	requirePDFResult(t)
	if pdfResult.TaskID == "" {
		t.Fatal("task_id is empty")
	}
	if pdfResult.ZipURL == "" {
		t.Fatal("zip_url is empty")
	}
	if pdfResult.Error != "" {
		t.Fatalf("unexpected error: %s", pdfResult.Error)
	}
}

// ═══════════════════════════════════════════════════════════════════
//  Extract — local file
// ═══════════════════════════════════════════════════════════════════

func TestExtractLocal_ReturnsMarkdown(t *testing.T) {
	requireLocalPDFResult(t)
	if localPDFResult.State != "done" {
		t.Fatalf("expected state=done, got %s", localPDFResult.State)
	}
	if localPDFResult.Markdown == "" {
		t.Fatal("markdown is empty")
	}
}

// ═══════════════════════════════════════════════════════════════════
//  Extract — extra formats (docx)
// ═══════════════════════════════════════════════════════════════════

func TestExtract_DocxExport(t *testing.T) {
	requirePDFResult(t)
	if pdfResult.Docx == nil {
		t.Fatal("docx is nil")
	}
	if len(pdfResult.Docx) == 0 {
		t.Fatal("docx is empty")
	}
}

func TestExtract_SaveDocxToFile(t *testing.T) {
	requirePDFResult(t)
	out := filepath.Join(t.TempDir(), "report.docx")
	if err := pdfResult.SaveDocx(out); err != nil {
		t.Fatalf("SaveDocx: %v", err)
	}
	info, err := os.Stat(out)
	if err != nil {
		t.Fatalf("stat: %v", err)
	}
	if info.Size() == 0 {
		t.Fatal("docx file is empty")
	}
}

// ═══════════════════════════════════════════════════════════════════
//  Crawl — single web page
// ═══════════════════════════════════════════════════════════════════

func TestCrawl_ReturnsMarkdown(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	result, err := client.Crawl(ctx, testHTMLURL, mineru.WithPollTimeout(testTimeout))
	if err != nil {
		t.Fatalf("Crawl: %v", err)
	}
	if result.State != "done" {
		t.Fatalf("expected state=done, got %s", result.State)
	}
	if result.Markdown == "" {
		t.Fatal("markdown is empty")
	}
}

func TestCrawl_EquivalentToExtractHTML(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	result, err := client.Extract(ctx, testHTMLURL,
		mineru.WithModel("html"),
		mineru.WithPollTimeout(testTimeout),
	)
	if err != nil {
		t.Fatalf("Extract with html model: %v", err)
	}
	if result.State != "done" {
		t.Fatalf("expected state=done, got %s", result.State)
	}
	if result.Markdown == "" {
		t.Fatal("markdown is empty")
	}
}

// ═══════════════════════════════════════════════════════════════════
//  Async — submit + get_task
// ═══════════════════════════════════════════════════════════════════

func TestSubmit_ReturnsTaskID(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	taskID, err := client.Submit(ctx, testPDFURL, mineru.WithModel(testModel))
	if err != nil {
		t.Fatalf("Submit: %v", err)
	}
	if taskID == "" {
		t.Fatal("task_id is empty")
	}
}

func TestGetTask_ReturnsResult(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	taskID, err := client.Submit(ctx, testPDFURL, mineru.WithModel(testModel))
	if err != nil {
		t.Fatalf("Submit: %v", err)
	}
	result, err := client.GetTask(ctx, taskID)
	if err != nil {
		t.Fatalf("GetTask: %v", err)
	}
	validStates := map[string]bool{"done": true, "pending": true, "running": true, "failed": true, "converting": true}
	if !validStates[result.State] {
		t.Fatalf("unexpected state: %s", result.State)
	}
}

func TestGetTask_EventuallyDone(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	// Use HTML crawl for speed — tests the submit+poll workflow, not the model.
	taskID, err := client.Submit(ctx, testHTMLURL, mineru.WithModel("html"))
	if err != nil {
		t.Fatalf("Submit: %v", err)
	}
	deadline := time.Now().Add(testTimeout)
	for time.Now().Before(deadline) {
		result, err := client.GetTask(ctx, taskID)
		if err != nil {
			t.Fatalf("GetTask: %v", err)
		}
		if result.State == "done" {
			if result.Markdown == "" {
				t.Fatal("done but markdown is empty")
			}
			return
		}
		if result.State == "failed" {
			t.Fatalf("task failed: %s", result.Error)
		}
		time.Sleep(5 * time.Second)
	}
	t.Fatal("task did not complete within timeout")
}

// ═══════════════════════════════════════════════════════════════════
//  Async — submit_batch + get_batch
// ═══════════════════════════════════════════════════════════════════

func TestSubmitBatch_ReturnsBatchID(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	batchID, err := client.SubmitBatch(ctx, []string{testPDFURL, testPDFURL},
		mineru.WithModel(testModel),
	)
	if err != nil {
		t.Fatalf("SubmitBatch: %v", err)
	}
	if batchID == "" {
		t.Fatal("batch_id is empty")
	}
}

func TestGetBatch_ReturnsList(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	batchID, err := client.SubmitBatch(ctx, []string{testPDFURL},
		mineru.WithModel(testModel),
	)
	if err != nil {
		t.Fatalf("SubmitBatch: %v", err)
	}
	results, err := client.GetBatch(ctx, batchID)
	if err != nil {
		t.Fatalf("GetBatch: %v", err)
	}
	if len(results) < 1 {
		t.Fatal("expected at least 1 result")
	}
}

// ═══════════════════════════════════════════════════════════════════
//  Batch — extract_batch + crawl_batch
// ═══════════════════════════════════════════════════════════════════

func TestExtractBatch_YieldsAllResults(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	ch, err := client.ExtractBatch(ctx, []string{testPDFURL, testPDFURL},
		mineru.WithModel(testModel),
		mineru.WithPollTimeout(testTimeout),
	)
	if err != nil {
		t.Fatalf("ExtractBatch: %v", err)
	}
	var results []*mineru.ExtractResult
	for r := range ch {
		results = append(results, r)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	for _, r := range results {
		if r.State != "done" && r.State != "failed" {
			t.Fatalf("expected done/failed, got %s", r.State)
		}
	}
}

func TestExtractBatch_DoneResultsHaveMarkdown(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	ch, err := client.ExtractBatch(ctx, []string{testPDFURL, testPDFURL},
		mineru.WithModel(testModel),
		mineru.WithPollTimeout(testTimeout),
	)
	if err != nil {
		t.Fatalf("ExtractBatch: %v", err)
	}
	for r := range ch {
		if r.State == "done" && r.Markdown == "" {
			t.Fatal("done result has empty markdown")
		}
	}
}

func TestCrawlBatch_YieldsResults(t *testing.T) {
	requireStandardClient(t)
	ctx := context.Background()
	ch, err := client.CrawlBatch(ctx,
		[]string{"https://opendatalab.com", "https://www.example.org"},
		mineru.WithPollTimeout(testTimeout),
	)
	if err != nil {
		t.Fatalf("CrawlBatch: %v", err)
	}
	var results []*mineru.ExtractResult
	for r := range ch {
		results = append(results, r)
	}
	if len(results) != 2 {
		t.Fatalf("expected 2 results, got %d", len(results))
	}
	for _, r := range results {
		if r.State != "done" && r.State != "failed" {
			t.Fatalf("expected done/failed, got %s", r.State)
		}
	}
}
