package mineru

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
)

// apiClient is the low-level HTTP wrapper around the MinerU v4 API.
type apiClient struct {
	httpClient *http.Client
	baseURL    string
	token      string
	source     string
}

type apiResponse struct {
	Code    any             `json:"code"`
	Msg     string          `json:"msg"`
	TraceID string          `json:"trace_id"`
	Data    json.RawMessage `json:"data"`
}

func (a *apiClient) post(ctx context.Context, path string, payload any) (json.RawMessage, error) {
	if a == nil {
		return nil, ErrNoAuthClient
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, a.baseURL+path, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+a.token)
	req.Header.Set("Content-Type", "application/json")
	if a.source != "" {
		req.Header.Set("source", a.source)
	}
	return a.do(req)
}

func (a *apiClient) get(ctx context.Context, path string) (json.RawMessage, error) {
	if a == nil {
		return nil, ErrNoAuthClient
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, a.baseURL+path, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+a.token)
	return a.do(req)
}

func (a *apiClient) putFile(ctx context.Context, url string, data []byte) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodPut, url, bytes.NewReader(data))
	if err != nil {
		return err
	}
	resp, err := a.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("upload failed: HTTP %d: %s", resp.StatusCode, body)
	}
	return nil
}

func (a *apiClient) download(ctx context.Context, url string) ([]byte, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := a.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("download failed: HTTP %d", resp.StatusCode)
	}
	return io.ReadAll(resp.Body)
}

func (a *apiClient) do(req *http.Request) (json.RawMessage, error) {
	resp, err := a.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("HTTP %d: %s", resp.StatusCode, body)
	}
	var ar apiResponse
	if err := json.Unmarshal(body, &ar); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}
	codeStr := codeToString(ar.Code)
	if codeStr != "0" {
		return nil, errorForCode(codeStr, ar.Msg, ar.TraceID)
	}
	return ar.Data, nil
}

// codeToString normalises the JSON "code" field which can be a number or a string.
func codeToString(v any) string {
	switch c := v.(type) {
	case nil:
		return ""
	case float64:
		return fmt.Sprintf("%d", int(c))
	case string:
		return c
	default:
		return fmt.Sprintf("%v", v)
	}
}
