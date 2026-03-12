// Package mineru provides a Go SDK for the MinerU document extraction API.
//
// One call to turn documents into Markdown:
//
//	client, _ := mineru.New("your-token")
//	result, _ := client.Extract(ctx, "https://example.com/report.pdf")
//	fmt.Println(result.Markdown)
package mineru

import (
	"context"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"strings"
	"time"
)

const (
	pollIntervalMin = 2 * time.Second
	pollIntervalMax = 30 * time.Second
)

var modelMap = map[string]string{
	"pipeline": "pipeline",
	"vlm":      "vlm",
	"html":     "MinerU-HTML",
}

// Client is the MinerU API client.
type Client struct {
	api *apiClient
}

// New creates a new MinerU [Client]. If token is empty, MINERU_TOKEN env var is used.
func New(token string, opts ...ClientOption) (*Client, error) {
	if token == "" {
		token = os.Getenv("MINERU_TOKEN")
	}
	if token == "" {
		return nil, &AuthError{APIError{Code: "NO_TOKEN", Message: "no token provided; pass token or set MINERU_TOKEN env var"}}
	}
	cfg := defaultClientConfig()
	for _, opt := range opts {
		opt(&cfg)
	}
	return &Client{
		api: &apiClient{httpClient: cfg.httpClient, baseURL: cfg.baseURL, token: token},
	}, nil
}

// ═══════════════════════════════════════════════════════════════════
//  Synchronous (blocking) methods
// ═══════════════════════════════════════════════════════════════════

// Extract parses a single document. Blocks until the result is ready.
//
//	result, err := client.Extract(ctx, "https://example.com/doc.pdf")
//	result, err := client.Extract(ctx, "./local.pdf", mineru.WithModel("vlm"))
func (c *Client) Extract(ctx context.Context, source string, opts ...ExtractOption) (*ExtractResult, error) {
	cfg := applyOpts(opts)
	modelVersion := resolveModel(cfg.model, source)
	payload := buildPayload(cfg, modelVersion)

	if isURL(source) {
		taskID, err := c.submitURL(ctx, source, payload)
		if err != nil {
			return nil, err
		}
		return c.waitSingle(ctx, taskID, cfg.timeout)
	}
	batchID, err := c.uploadAndSubmit(ctx, []string{source}, payload)
	if err != nil {
		return nil, err
	}
	results, err := c.waitBatch(ctx, batchID, cfg.timeout)
	if err != nil {
		return nil, err
	}
	return results[0], nil
}

// ExtractBatch submits all tasks at once and streams results on the returned
// channel as each task completes. The channel is closed when all tasks finish
// or the context is cancelled.
//
//	ch, err := client.ExtractBatch(ctx, urls, mineru.WithModel("pipeline"))
//	for r := range ch {
//	    fmt.Println(r.Filename, r.Markdown[:200])
//	}
func (c *Client) ExtractBatch(ctx context.Context, sources []string, opts ...ExtractOption) (<-chan *ExtractResult, error) {
	cfg := applyOpts(opts)
	first := ""
	if len(sources) > 0 {
		first = sources[0]
	}
	modelVersion := resolveModel(cfg.model, first)
	payload := buildPayload(cfg, modelVersion)

	var urls, files []string
	for _, s := range sources {
		if isURL(s) {
			urls = append(urls, s)
		} else {
			files = append(files, s)
		}
	}

	var batchIDs []string
	if len(urls) > 0 {
		bid, err := c.submitURLsBatch(ctx, urls, payload)
		if err != nil {
			return nil, err
		}
		batchIDs = append(batchIDs, bid)
	}
	if len(files) > 0 {
		bid, err := c.uploadAndSubmit(ctx, files, payload)
		if err != nil {
			return nil, err
		}
		batchIDs = append(batchIDs, bid)
	}

	ch := make(chan *ExtractResult)
	go func() {
		defer close(ch)
		c.yieldBatch(ctx, ch, batchIDs, len(sources), cfg.timeout)
	}()
	return ch, nil
}

// Crawl parses a web page to Markdown. Shorthand for Extract with model="html".
func (c *Client) Crawl(ctx context.Context, pageURL string, opts ...ExtractOption) (*ExtractResult, error) {
	return c.Extract(ctx, pageURL, append([]ExtractOption{WithModel("html")}, opts...)...)
}

// CrawlBatch crawls multiple web pages. Shorthand for ExtractBatch with model="html".
func (c *Client) CrawlBatch(ctx context.Context, urls []string, opts ...ExtractOption) (<-chan *ExtractResult, error) {
	return c.ExtractBatch(ctx, urls, append([]ExtractOption{WithModel("html")}, opts...)...)
}

// ═══════════════════════════════════════════════════════════════════
//  Async primitives (no polling, no waiting)
// ═══════════════════════════════════════════════════════════════════

// Submit submits a single task without waiting. Returns a task ID (for URLs)
// or batch ID (for local files). Use [Client.GetTask] or [Client.GetBatch] to
// check the result later.
func (c *Client) Submit(ctx context.Context, source string, opts ...ExtractOption) (string, error) {
	cfg := applyOpts(opts)
	modelVersion := resolveModel(cfg.model, source)
	payload := buildPayload(cfg, modelVersion)

	if isURL(source) {
		return c.submitURL(ctx, source, payload)
	}
	return c.uploadAndSubmit(ctx, []string{source}, payload)
}

// SubmitBatch submits multiple tasks without waiting. Returns a batch ID.
func (c *Client) SubmitBatch(ctx context.Context, sources []string, opts ...ExtractOption) (string, error) {
	cfg := applyOpts(opts)
	first := ""
	if len(sources) > 0 {
		first = sources[0]
	}
	modelVersion := resolveModel(cfg.model, first)
	payload := buildPayload(cfg, modelVersion)

	var urls, files []string
	for _, s := range sources {
		if isURL(s) {
			urls = append(urls, s)
		} else {
			files = append(files, s)
		}
	}
	if len(urls) > 0 && len(files) == 0 {
		return c.submitURLsBatch(ctx, urls, payload)
	}
	if len(files) > 0 && len(urls) == 0 {
		return c.uploadAndSubmit(ctx, files, payload)
	}
	return c.uploadAndSubmit(ctx, sources, payload)
}

// GetTask queries a single task's current state. When state is "done", the
// result zip is downloaded and parsed automatically.
func (c *Client) GetTask(ctx context.Context, taskID string) (*ExtractResult, error) {
	data, err := c.api.get(ctx, "/extract/task/"+taskID)
	if err != nil {
		return nil, err
	}
	r, err := parseTaskData(data)
	if err != nil {
		return nil, err
	}
	if r.State == "done" && r.ZipURL != "" {
		return c.downloadAndParse(ctx, r)
	}
	return r, nil
}

// GetBatch queries all tasks in a batch. Completed tasks have their content
// populated; in-progress tasks have empty Markdown.
func (c *Client) GetBatch(ctx context.Context, batchID string) ([]*ExtractResult, error) {
	data, err := c.api.get(ctx, "/extract-results/batch/"+batchID)
	if err != nil {
		return nil, err
	}
	var resp struct {
		ExtractResult []json.RawMessage `json:"extract_result"`
	}
	if err := json.Unmarshal(data, &resp); err != nil {
		return nil, fmt.Errorf("unmarshal batch: %w", err)
	}
	var results []*ExtractResult
	for _, raw := range resp.ExtractResult {
		r, err := parseTaskData(raw)
		if err != nil {
			return nil, err
		}
		if r.State == "done" && r.ZipURL != "" {
			r, err = c.downloadAndParse(ctx, r)
			if err != nil {
				return nil, err
			}
		}
		results = append(results, r)
	}
	return results, nil
}

// ═══════════════════════════════════════════════════════════════════
//  Internal helpers
// ═══════════════════════════════════════════════════════════════════

func (c *Client) submitURL(ctx context.Context, srcURL string, payload map[string]any) (string, error) {
	payload["url"] = srcURL
	data, err := c.api.post(ctx, "/extract/task", payload)
	if err != nil {
		return "", err
	}
	var resp struct {
		TaskID string `json:"task_id"`
	}
	if err := json.Unmarshal(data, &resp); err != nil {
		return "", err
	}
	return resp.TaskID, nil
}

func (c *Client) submitURLsBatch(ctx context.Context, urls []string, payload map[string]any) (string, error) {
	files := make([]map[string]string, len(urls))
	for i, u := range urls {
		files[i] = map[string]string{"url": u}
	}
	payload["files"] = files
	data, err := c.api.post(ctx, "/extract/task/batch", payload)
	if err != nil {
		return "", err
	}
	var resp struct {
		BatchID string `json:"batch_id"`
	}
	if err := json.Unmarshal(data, &resp); err != nil {
		return "", err
	}
	return resp.BatchID, nil
}

func (c *Client) uploadAndSubmit(ctx context.Context, filePaths []string, payload map[string]any) (string, error) {
	filesMeta := make([]map[string]string, len(filePaths))
	for i, p := range filePaths {
		filesMeta[i] = map[string]string{"name": filepath.Base(p)}
	}
	payload["files"] = filesMeta

	data, err := c.api.post(ctx, "/file-urls/batch", payload)
	if err != nil {
		return "", err
	}
	var resp struct {
		BatchID  string   `json:"batch_id"`
		FileURLs []string `json:"file_urls"`
	}
	if err := json.Unmarshal(data, &resp); err != nil {
		return "", err
	}

	for i, localPath := range filePaths {
		fileData, err := os.ReadFile(localPath)
		if err != nil {
			return "", fmt.Errorf("read %s: %w", localPath, err)
		}
		if err := c.api.putFile(ctx, resp.FileURLs[i], fileData); err != nil {
			return "", fmt.Errorf("upload %s: %w", localPath, err)
		}
	}
	return resp.BatchID, nil
}

func (c *Client) downloadAndParse(ctx context.Context, r *ExtractResult) (*ExtractResult, error) {
	zipBytes, err := c.api.download(ctx, r.ZipURL)
	if err != nil {
		return nil, fmt.Errorf("download zip: %w", err)
	}
	parsed, err := parseZip(zipBytes, r.TaskID, r.Filename)
	if err != nil {
		return nil, fmt.Errorf("parse zip: %w", err)
	}
	parsed.ZipURL = r.ZipURL
	return parsed, nil
}

func (c *Client) waitSingle(ctx context.Context, taskID string, timeout time.Duration) (*ExtractResult, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	interval := pollIntervalMin
	for {
		r, err := c.GetTask(ctx, taskID)
		if err != nil {
			if ctx.Err() != nil {
				return nil, newTimeoutError(timeout, taskID)
			}
			return nil, err
		}
		if r.State == "done" || r.State == "failed" {
			return r, nil
		}
		select {
		case <-ctx.Done():
			return nil, newTimeoutError(timeout, taskID)
		case <-time.After(interval):
		}
		if interval < pollIntervalMax {
			interval *= 2
		}
	}
}

func (c *Client) waitBatch(ctx context.Context, batchID string, timeout time.Duration) ([]*ExtractResult, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	interval := pollIntervalMin
	for {
		results, err := c.GetBatch(ctx, batchID)
		if err != nil {
			if ctx.Err() != nil {
				return nil, newTimeoutError(timeout, batchID)
			}
			return nil, err
		}
		allDone := true
		for _, r := range results {
			if r.State != "done" && r.State != "failed" {
				allDone = false
				break
			}
		}
		if allDone {
			return results, nil
		}
		select {
		case <-ctx.Done():
			return nil, newTimeoutError(timeout, batchID)
		case <-time.After(interval):
		}
		if interval < pollIntervalMax {
			interval *= 2
		}
	}
}

func (c *Client) yieldBatch(ctx context.Context, ch chan<- *ExtractResult, batchIDs []string, total int, timeout time.Duration) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	type key struct {
		bid string
		idx int
	}
	yielded := make(map[key]bool)
	interval := pollIntervalMin

	for len(yielded) < total {
		for _, bid := range batchIDs {
			results, err := c.GetBatch(ctx, bid)
			if err != nil {
				return
			}
			for i, r := range results {
				k := key{bid, i}
				if !yielded[k] && (r.State == "done" || r.State == "failed") {
					yielded[k] = true
					select {
					case ch <- r:
					case <-ctx.Done():
						return
					}
				}
			}
		}
		if len(yielded) >= total {
			break
		}
		select {
		case <-ctx.Done():
			return
		case <-time.After(interval):
		}
		if interval < pollIntervalMax {
			interval *= 2
		}
	}
}

// ═══════════════════════════════════════════════════════════════════
//  Pure helpers
// ═══════════════════════════════════════════════════════════════════

func parseTaskData(data json.RawMessage) (*ExtractResult, error) {
	var d struct {
		TaskID          string           `json:"task_id"`
		State           string           `json:"state"`
		FileName        string           `json:"file_name"`
		ErrMsg          string           `json:"err_msg"`
		FullZipURL      string           `json:"full_zip_url"`
		ExtractProgress *json.RawMessage `json:"extract_progress"`
	}
	if err := json.Unmarshal(data, &d); err != nil {
		return nil, fmt.Errorf("unmarshal task data: %w", err)
	}
	r := &ExtractResult{
		TaskID:   d.TaskID,
		State:    d.State,
		Filename: d.FileName,
		ZipURL:   d.FullZipURL,
	}
	if d.ErrMsg != "" {
		r.Error = d.ErrMsg
	}
	if d.ExtractProgress != nil {
		var p Progress
		if json.Unmarshal(*d.ExtractProgress, &p) == nil && p.TotalPages > 0 {
			r.Progress = &p
		}
	}
	return r, nil
}

func applyOpts(opts []ExtractOption) extractConfig {
	cfg := defaultExtractConfig()
	for _, opt := range opts {
		opt(&cfg)
	}
	return cfg
}

func buildPayload(cfg extractConfig, modelVersion string) map[string]any {
	m := map[string]any{"model_version": modelVersion}
	if cfg.ocr {
		m["is_ocr"] = true
	}
	if !cfg.formula {
		m["enable_formula"] = false
	}
	if !cfg.table {
		m["enable_table"] = false
	}
	if cfg.language != "ch" {
		m["language"] = cfg.language
	}
	if cfg.pages != nil {
		m["page_ranges"] = *cfg.pages
	}
	if len(cfg.extraFormats) > 0 {
		m["extra_formats"] = cfg.extraFormats
	}
	return m
}

func isURL(s string) bool {
	return strings.HasPrefix(s, "http://") || strings.HasPrefix(s, "https://")
}

func getExtension(source string) string {
	if isURL(source) {
		u, err := url.Parse(source)
		if err != nil {
			return ""
		}
		return strings.ToLower(path.Ext(u.Path))
	}
	return strings.ToLower(filepath.Ext(source))
}

func resolveModel(model *string, source string) string {
	if model != nil {
		if mapped, ok := modelMap[*model]; ok {
			return mapped
		}
		return *model
	}
	ext := getExtension(source)
	if ext == ".html" || ext == ".htm" {
		return "MinerU-HTML"
	}
	return "vlm"
}
