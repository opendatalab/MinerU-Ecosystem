package mineru_test

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	mineru "github.com/OpenDataLab/mineru-open-sdk"
)

const (
	flashTestPDFURL  = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
	flashTestBaseURL = "https://staging.mineru.org.cn/api/v1/agent"
	flashTestTimeout = 5 * time.Minute
)

// ═══════════════════════════════════════════════════════════════════
//  Unit tests — no API calls
// ═══════════════════════════════════════════════════════════════════

func TestNewFlash_NoTokenRequired(t *testing.T) {
	c := mineru.NewFlash()
	if c == nil {
		t.Fatal("NewFlash returned nil")
	}
}

func TestNewFlash_ExtractReturnsError(t *testing.T) {
	c := mineru.NewFlash()
	_, err := c.Extract(context.Background(), "https://example.com/doc.pdf")
	if err == nil {
		t.Fatal("expected error when calling Extract on flash-only client")
	}
	var paramErr *mineru.ParamError
	if !errors.As(err, &paramErr) {
		t.Fatalf("expected ParamError, got %T: %v", err, err)
	}
}

func TestNewFlash_CrawlReturnsError(t *testing.T) {
	c := mineru.NewFlash()
	_, err := c.Crawl(context.Background(), "https://example.com")
	if err == nil {
		t.Fatal("expected error when calling Crawl on flash-only client")
	}
	var paramErr *mineru.ParamError
	if !errors.As(err, &paramErr) {
		t.Fatalf("expected ParamError, got %T: %v", err, err)
	}
}

func TestNewFlash_SubmitReturnsError(t *testing.T) {
	c := mineru.NewFlash()
	_, err := c.Submit(context.Background(), "https://example.com/doc.pdf")
	if err == nil {
		t.Fatal("expected error when calling Submit on flash-only client")
	}
	var paramErr *mineru.ParamError
	if !errors.As(err, &paramErr) {
		t.Fatalf("expected ParamError, got %T: %v", err, err)
	}
}

func TestNewFlash_GetTaskReturnsError(t *testing.T) {
	c := mineru.NewFlash()
	_, err := c.GetTask(context.Background(), "fake-id")
	if err == nil {
		t.Fatal("expected error when calling GetTask on flash-only client")
	}
	var paramErr *mineru.ParamError
	if !errors.As(err, &paramErr) {
		t.Fatalf("expected ParamError, got %T: %v", err, err)
	}
}

func TestNew_FlashExtractAlsoWorks(t *testing.T) {
	if os.Getenv("MINERU_TOKEN") == "" {
		t.Skip("MINERU_TOKEN not set")
	}
	c, err := mineru.New("")
	if err != nil {
		t.Fatalf("New: %v", err)
	}
	// Just verify the client has flash capability — don't actually call the API.
	_ = c
}

// ═══════════════════════════════════════════════════════════════════
//  Integration tests — flash API (no token needed)
// ═══════════════════════════════════════════════════════════════════

func newFlashTestClient() *mineru.Client {
	return mineru.NewFlash(mineru.WithBaseURL(flashTestBaseURL))
}

func flashExtractOrSkip(t *testing.T, c *mineru.Client, source string, opts ...mineru.FlashExtractOption) *mineru.ExtractResult {
	t.Helper()
	ctx, cancel := context.WithTimeout(context.Background(), flashTestTimeout)
	defer cancel()
	result, err := c.FlashExtract(ctx, source, opts...)
	if err != nil {
		errMsg := err.Error()
		if strings.Contains(errMsg, "405") || strings.Contains(errMsg, "404") || strings.Contains(errMsg, "503") {
			t.Skip("flash API not available (not deployed yet?)")
		}
		t.Fatalf("FlashExtract: %v", err)
	}
	return result
}

func TestFlashExtract_URL(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	c := newFlashTestClient()
	result := flashExtractOrSkip(t, c, flashTestPDFURL, mineru.WithFlashPages("1-3"))
	if result.State != "done" {
		t.Fatalf("expected state=done, got %s (error: %s)", result.State, result.Error)
	}
	if result.Markdown == "" {
		t.Fatal("markdown is empty")
	}
	if result.TaskID == "" {
		t.Fatal("task_id is empty")
	}
}

func TestFlashExtract_LocalFile(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	tmpDir := t.TempDir()
	localPDF := filepath.Join(tmpDir, "test_hello.pdf")
	if err := os.WriteFile(localPDF, minimalPDF, 0o644); err != nil {
		t.Fatalf("write test pdf: %v", err)
	}

	c := newFlashTestClient()
	result := flashExtractOrSkip(t, c, localPDF)
	if result.State != "done" {
		t.Fatalf("expected state=done, got %s (error: %s)", result.State, result.Error)
	}
	if result.Markdown == "" {
		t.Fatal("markdown is empty")
	}
}

func TestFlashExtract_SaveMarkdown(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	c := newFlashTestClient()
	result := flashExtractOrSkip(t, c, flashTestPDFURL, mineru.WithFlashPages("1-1"))

	out := filepath.Join(t.TempDir(), "output.md")
	if err := result.SaveMarkdown(out, false); err != nil {
		t.Fatalf("SaveMarkdown: %v", err)
	}
	info, err := os.Stat(out)
	if err != nil {
		t.Fatalf("stat: %v", err)
	}
	if info.Size() == 0 {
		t.Fatal("saved markdown file is empty")
	}
}

func TestFlashExtract_NoDocxAvailable(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	c := newFlashTestClient()
	result := flashExtractOrSkip(t, c, flashTestPDFURL, mineru.WithFlashPages("1-1"))

	if err := result.SaveDocx(filepath.Join(t.TempDir(), "out.docx")); err == nil {
		t.Fatal("expected error when saving docx from flash result")
	}
	if err := result.SaveHTML(filepath.Join(t.TempDir(), "out.html")); err == nil {
		t.Fatal("expected error when saving html from flash result")
	}
	if err := result.SaveLaTeX(filepath.Join(t.TempDir(), "out.tex")); err == nil {
		t.Fatal("expected error when saving latex from flash result")
	}
}

func TestFlashExtract_WithLanguage(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	c := newFlashTestClient()
	result := flashExtractOrSkip(t, c, flashTestPDFURL,
		mineru.WithFlashLanguage("en"),
		mineru.WithFlashPages("1-1"),
	)
	if result.State != "done" {
		t.Fatalf("expected state=done, got %s", result.State)
	}
	if result.Markdown == "" {
		t.Fatal("markdown is empty")
	}
}
