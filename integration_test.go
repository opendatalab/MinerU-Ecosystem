//go:build integration

package main

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

var binaryPath string

func TestMain(m *testing.M) {
	tmp, err := os.MkdirTemp("", "mineru-cli-test-*")
	if err != nil {
		fmt.Fprintf(os.Stderr, "create temp dir: %v\n", err)
		os.Exit(1)
	}
	defer os.RemoveAll(tmp)

	binaryPath = filepath.Join(tmp, "mineru.exe")
	cmd := exec.Command("go", "build", "-o", binaryPath, ".")
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "build failed: %v\n", err)
		os.Exit(1)
	}

	os.Exit(m.Run())
}

// testURL is a small, publicly accessible PDF for testing.
// Replace with your own stable URL if this one breaks.
const testURL = "https://arxiv.org/pdf/2310.06825"

type runResult struct {
	stdout   string
	stderr   string
	exitCode int
}

func run(t *testing.T, args ...string) runResult {
	t.Helper()
	cmd := exec.Command(binaryPath, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	cmd.Env = os.Environ()

	err := cmd.Run()
	code := 0
	if exitErr, ok := err.(*exec.ExitError); ok {
		code = exitErr.ExitCode()
	} else if err != nil {
		t.Fatalf("exec error: %v", err)
	}

	return runResult{
		stdout:   stdout.String(),
		stderr:   stderr.String(),
		exitCode: code,
	}
}

// ── basic commands (no API) ──

func TestVersion(t *testing.T) {
	r := run(t, "version")
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d, stderr: %s", r.exitCode, r.stderr)
	}
	if !strings.Contains(r.stdout, "mineru version") {
		t.Errorf("unexpected output: %s", r.stdout)
	}
}

func TestHelpOutput(t *testing.T) {
	r := run(t, "--help")
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d", r.exitCode)
	}
	if !strings.Contains(r.stdout, "extract") || !strings.Contains(r.stdout, "crawl") {
		t.Errorf("help missing expected commands: %s", r.stdout)
	}
}

func TestExtractNoArgs(t *testing.T) {
	r := run(t, "extract", "--token", "fake")
	if r.exitCode == 0 {
		t.Fatal("expected non-zero exit code")
	}
	if !strings.Contains(r.stderr, "no input files") {
		t.Errorf("expected 'no input files' error, got stderr: %s", r.stderr)
	}
}

func TestExtractDocxToStdout(t *testing.T) {
	r := run(t, "extract", "report.pdf", "-f", "docx", "--token", "fake")
	if r.exitCode == 0 {
		t.Fatal("expected non-zero exit code")
	}
	if !strings.Contains(r.stderr, "binary format") {
		t.Errorf("expected 'binary format' error, got stderr: %s", r.stderr)
	}
}

func TestExtractMultiFormatToStdout(t *testing.T) {
	r := run(t, "extract", "report.pdf", "-f", "md,html", "--token", "fake")
	if r.exitCode == 0 {
		t.Fatal("expected non-zero exit code")
	}
	if !strings.Contains(r.stderr, "multiple formats") {
		t.Errorf("expected 'multiple formats' error, got stderr: %s", r.stderr)
	}
}

func TestExtractBatchWithoutOutput(t *testing.T) {
	r := run(t, "extract", "a.pdf", "b.pdf", "--token", "fake")
	if r.exitCode == 0 {
		t.Fatal("expected non-zero exit code")
	}
	if !strings.Contains(r.stderr, "batch mode requires -o") {
		t.Errorf("expected 'batch mode requires -o' error, got stderr: %s", r.stderr)
	}
}

func TestExtractNoToken(t *testing.T) {
	fakeHome := t.TempDir()
	cmd := exec.Command(binaryPath, "extract", "report.pdf")
	env := filterEnv(os.Environ(), "MINERU_TOKEN")
	env = setEnv(env, "USERPROFILE", fakeHome)
	env = setEnv(env, "HOME", fakeHome)
	cmd.Env = env
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	err := cmd.Run()
	if err == nil {
		t.Fatal("expected non-zero exit code")
	}
	if !strings.Contains(stderr.String(), "no API token") {
		t.Errorf("expected token error, got stderr: %s", stderr.String())
	}
}

// ── real API tests ──

func requireToken(t *testing.T) string {
	t.Helper()
	token := os.Getenv("MINERU_TOKEN")
	if token == "" {
		t.Skip("MINERU_TOKEN not set, skipping API test")
	}
	return token
}

func TestExtractURLToStdout(t *testing.T) {
	token := requireToken(t)
	r := run(t, "extract", testURL, "--token", token)
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d, stderr:\n%s", r.exitCode, r.stderr)
	}
	if len(r.stdout) == 0 {
		t.Fatal("stdout is empty, expected markdown content")
	}
	if !strings.Contains(r.stdout, "#") {
		t.Errorf("stdout doesn't look like markdown (no '#' headers)")
	}
	if strings.Contains(r.stdout, "Uploading") || strings.Contains(r.stdout, "Parsing") {
		t.Error("status messages leaked into stdout")
	}
	if !strings.Contains(r.stderr, "Done") {
		t.Errorf("stderr missing 'Done' status, got:\n%s", r.stderr)
	}
}

func TestExtractURLToDir(t *testing.T) {
	token := requireToken(t)
	outDir := t.TempDir()

	r := run(t, "extract", testURL, "-o", outDir, "--token", token)
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d, stderr:\n%s", r.exitCode, r.stderr)
	}
	if len(r.stdout) > 0 {
		t.Errorf("expected no stdout in file mode, got: %s", r.stdout[:min(len(r.stdout), 200)])
	}

	files, _ := filepath.Glob(filepath.Join(outDir, "*.md"))
	if len(files) == 0 {
		t.Fatal("no .md files found in output directory")
	}

	content, err := os.ReadFile(files[0])
	if err != nil {
		t.Fatalf("read output file: %v", err)
	}
	if len(content) == 0 {
		t.Error("output file is empty")
	}
}

func TestExtractURLHtmlFormat(t *testing.T) {
	token := requireToken(t)
	r := run(t, "extract", testURL, "-f", "html", "--token", token)
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d, stderr:\n%s", r.exitCode, r.stderr)
	}
	if len(r.stdout) == 0 {
		t.Fatal("stdout is empty")
	}
	lower := strings.ToLower(r.stdout)
	if !strings.Contains(lower, "<") {
		t.Errorf("stdout doesn't look like HTML")
	}
}

func TestCrawlToStdout(t *testing.T) {
	token := requireToken(t)
	crawlURL := "https://mineru.net"

	r := run(t, "crawl", crawlURL, "--token", token)
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d, stderr:\n%s", r.exitCode, r.stderr)
	}
	if len(r.stdout) == 0 {
		t.Fatal("stdout is empty, expected markdown content")
	}
	if strings.Contains(r.stdout, "Crawling") {
		t.Error("status messages leaked into stdout")
	}
}

func TestCrawlToDir(t *testing.T) {
	token := requireToken(t)
	crawlURL := "https://mineru.net"
	outDir := t.TempDir()

	r := run(t, "crawl", crawlURL, "-o", outDir, "--token", token)
	if r.exitCode != 0 {
		t.Fatalf("exit code = %d, stderr:\n%s", r.exitCode, r.stderr)
	}

	files, _ := filepath.Glob(filepath.Join(outDir, "*.md"))
	if len(files) == 0 {
		t.Fatal("no .md files found in output directory")
	}
}

// ── helpers ──

func filterEnv(env []string, exclude string) []string {
	var filtered []string
	prefix := strings.ToUpper(exclude) + "="
	for _, e := range env {
		if !strings.HasPrefix(strings.ToUpper(e), prefix) {
			filtered = append(filtered, e)
		}
	}
	return filtered
}

func setEnv(env []string, key, value string) []string {
	env = filterEnv(env, key)
	return append(env, key+"="+value)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
