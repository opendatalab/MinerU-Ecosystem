package cmd

import (
	"log"
	"net/http"
	"time"
)

type loggingRoundTripper struct {
	next http.RoundTripper
}

func (l *loggingRoundTripper) RoundTrip(req *http.Request) (*http.Response, error) {
	start := time.Now()

	// Print method and full URL
	log.Printf("[DEBUG] → %s %s\n", req.Method, req.URL.String())

	res, err := l.next.RoundTrip(req)
	duration := time.Since(start)

	if err != nil {
		log.Printf("[DEBUG] ← ERROR %s %s (%v): %v\n", req.Method, req.URL.String(), duration, err)
		return nil, err
	}

	// Print response status code, method, url, and time taken
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
