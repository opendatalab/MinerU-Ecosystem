package cmd

import (
	"bytes"
	"io"
	"log"
	"net/http"
	"strings"
	"time"
)

type loggingRoundTripper struct {
	next http.RoundTripper
}

func (l *loggingRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	start := time.Now()

	log.Printf("[DEBUG] → %s %s\n", req.Method, req.URL.String())

	// Log request body for JSON payloads only (skip binary uploads like OSS PUT)
	if req.Body != nil && strings.Contains(req.Header.Get("Content-Type"), "application/json") {
		bodyBytes, err := io.ReadAll(req.Body)
		req.Body.Close()
		if err == nil && len(bodyBytes) > 0 {
			log.Printf("[DEBUG]    body: %s\n", string(bodyBytes))
		}
		req.Body = io.NopCloser(bytes.NewReader(bodyBytes))
	}

	res, err := l.next.RoundTrip(req)
	duration := time.Since(start)

	if err != nil {
		log.Printf("[DEBUG] ← ERROR %s %s (%v): %v\n", req.Method, req.URL.String(), duration, err)
		return nil, err
	}

	log.Printf("[DEBUG] ← %d %s %s (%v)\n", res.StatusCode, req.Method, req.URL.String(), duration)
	return res, err
}

// newVerboseHTTPClient returns an http.Client that logs requests and responses
// when the --verbose flag is enabled.
func newVerboseHTTPClient() *http.Client {
	return &http.Client{
		Transport: &loggingRoundTripper{
			next: http.DefaultTransport,
		},
	}
}
