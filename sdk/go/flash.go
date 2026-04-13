package mineru

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// NewFlash creates a [Client] for flash (agent) mode only. No API token is
// required. The returned client supports [Client.FlashExtract]; calling
// standard methods like [Client.Extract] will return an error.
func NewFlash(opts ...ClientOption) *Client {
	cfg := defaultClientConfig()
	for _, opt := range opts {
		opt(&cfg)
	}
	return &Client{
		flashApi: &flashApiClient{httpClient: cfg.httpClient, baseURL: cfg.flashBaseURL, source: defaultSource},
		source:   defaultSource,
	}
}

// FlashExtract parses a single document using the flash (agent) API.
// Flash mode requires no authentication, only outputs Markdown, and is
// optimised for speed. Blocks until the result is ready.
//
//	client := mineru.NewFlash()
//	result, err := client.FlashExtract(ctx, "report.pdf")
//	fmt.Println(result.Markdown)
func (c *Client) FlashExtract(ctx context.Context, source string, opts ...FlashExtractOption) (*ExtractResult, error) {
	cfg := defaultFlashExtractConfig()
	for _, opt := range opts {
		opt(&cfg)
	}

	var taskID string
	var err error

	if isURL(source) {
		taskID, err = c.flashSubmitURL(ctx, source, cfg)
	} else {
		taskID, err = c.flashSubmitFile(ctx, source, cfg)
	}
	if err != nil {
		return nil, err
	}

	return c.flashWait(ctx, taskID, cfg.timeout)
}

// ═══════════════════════════════════════════════════════════════════
//  Flash internal helpers
// ═══════════════════════════════════════════════════════════════════

func (c *Client) flashSubmitURL(ctx context.Context, srcURL string, cfg flashExtractConfig) (string, error) {
	payload := map[string]any{
		"url":      srcURL,
		"language": cfg.language,
	}
	if cfg.pages != nil {
		payload["page_range"] = *cfg.pages
	}
	if cfg.ocr != nil {
		payload["is_ocr"] = *cfg.ocr
	}
	if cfg.formula != nil {
		payload["enable_formula"] = *cfg.formula
	}
	if cfg.table != nil {
		payload["enable_table"] = *cfg.table
	}

	data, err := c.flashApi.post(ctx, "/parse/url", payload)
	if err != nil {
		return "", err
	}
	var resp struct {
		TaskID string `json:"task_id"`
	}
	if err := json.Unmarshal(data, &resp); err != nil {
		return "", fmt.Errorf("unmarshal flash url response: %w", err)
	}
	return resp.TaskID, nil
}

func (c *Client) flashSubmitFile(ctx context.Context, filePath string, cfg flashExtractConfig) (string, error) {
	fileName := filepath.Base(filePath)

	payload := map[string]any{
		"file_name": fileName,
		"language":  cfg.language,
	}
	if cfg.pages != nil {
		payload["page_range"] = *cfg.pages
	}
	if cfg.ocr != nil {
		payload["is_ocr"] = *cfg.ocr
	}
	if cfg.formula != nil {
		payload["enable_formula"] = *cfg.formula
	}
	if cfg.table != nil {
		payload["enable_table"] = *cfg.table
	}

	data, err := c.flashApi.post(ctx, "/parse/file", payload)
	if err != nil {
		return "", err
	}
	var resp struct {
		TaskID  string `json:"task_id"`
		FileURL string `json:"file_url"`
	}
	if err := json.Unmarshal(data, &resp); err != nil {
		return "", fmt.Errorf("unmarshal flash file response: %w", err)
	}

	fileData, err := os.ReadFile(filePath)
	if err != nil {
		return "", fmt.Errorf("read %s: %w", filePath, err)
	}
	if err := c.flashApi.putFile(ctx, resp.FileURL, fileData); err != nil {
		return "", fmt.Errorf("upload %s: %w", filePath, err)
	}

	return resp.TaskID, nil
}

func (c *Client) flashWait(ctx context.Context, taskID string, timeout time.Duration) (*ExtractResult, error) {
	pollCtx, pollCancel := context.WithTimeout(ctx, timeout)
	defer pollCancel()

	interval := pollIntervalMin
	for {
		reqCtx, reqCancel := context.WithTimeout(pollCtx, requestTimeout)
		r, err := c.flashGetTask(reqCtx, taskID)
		reqCancel()
		if err != nil {
			if pollCtx.Err() != nil {
				return nil, newTimeoutError(timeout, taskID)
			}
			return nil, err
		}
		switch r.State {
		case "done":
			return r, nil
		case "failed":
			return r, nil
		}
		select {
		case <-pollCtx.Done():
			return nil, newTimeoutError(timeout, taskID)
		case <-time.After(interval):
		}
		if interval < pollIntervalMax {
			interval *= 2
		}
	}
}

func (c *Client) flashGetTask(ctx context.Context, taskID string) (*ExtractResult, error) {
	data, err := c.flashApi.get(ctx, "/parse/"+taskID)
	if err != nil {
		return nil, err
	}
	return c.parseFlashTaskData(ctx, data)
}

func (c *Client) parseFlashTaskData(ctx context.Context, data json.RawMessage) (*ExtractResult, error) {
	var d struct {
		TaskID          string `json:"task_id"`
		State           string `json:"state"`
		MarkdownURL     string `json:"markdown_url"`
		ErrMsg          string `json:"err_msg"`
		ErrCode         any    `json:"err_code"`
		ExtractProgress *struct {
			ExtractedPages int    `json:"extracted_pages"`
			TotalPages     int    `json:"total_pages"`
			StartTime      string `json:"start_time"`
		} `json:"extract_progress"`
		Meta *struct {
			Pages    int `json:"pages"`
			FileSize int `json:"file_size"`
		} `json:"meta"`
	}
	if err := json.Unmarshal(data, &d); err != nil {
		return nil, fmt.Errorf("unmarshal flash task data: %w", err)
	}

	r := &ExtractResult{
		TaskID:  d.TaskID,
		State:   d.State,
		ErrCode: codeToString(d.ErrCode),
		Error:   d.ErrMsg,
	}
	if d.State == "failed" {
		return r, nil
	}
	if d.ExtractProgress != nil {
		r.Progress = &Progress{
			ExtractedPages: d.ExtractProgress.ExtractedPages,
			TotalPages:     d.ExtractProgress.TotalPages,
			StartTime:      d.ExtractProgress.StartTime,
		}
	}

	if d.State == "done" && d.MarkdownURL != "" {
		md, err := c.flashApi.downloadText(ctx, d.MarkdownURL)
		if err != nil {
			return nil, fmt.Errorf("download markdown: %w", err)
		}
		r.Markdown = md
	}

	return r, nil
}
