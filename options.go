package mineru

import (
	"net/http"
	"time"
)

// ---------------------------------------------------------------------------
// Client options
// ---------------------------------------------------------------------------

type clientConfig struct {
	baseURL    string
	httpClient *http.Client
}

func defaultClientConfig() clientConfig {
	return clientConfig{
		baseURL:    "https://mineru.net/api/v4",
		httpClient: &http.Client{Timeout: 5 * time.Minute},
	}
}

// ClientOption configures the [Client] constructor.
type ClientOption func(*clientConfig)

// WithBaseURL overrides the default API base URL (for private deployments).
func WithBaseURL(url string) ClientOption {
	return func(c *clientConfig) { c.baseURL = url }
}

// WithHTTPClient provides a custom *http.Client for all API requests.
func WithHTTPClient(client *http.Client) ClientOption {
	return func(c *clientConfig) { c.httpClient = client }
}

// ---------------------------------------------------------------------------
// Extract options
// ---------------------------------------------------------------------------

type extractConfig struct {
	model        *string
	ocr          bool
	formula      bool
	table        bool
	language     string
	pages        *string
	extraFormats []string
	timeout      time.Duration
}

func defaultExtractConfig() extractConfig {
	return extractConfig{
		formula:  true,
		table:    true,
		language: "ch",
		timeout:  5 * time.Minute,
	}
}

// ExtractOption configures an extraction request.
type ExtractOption func(*extractConfig)

// WithModel sets the model version: "pipeline", "vlm", or "html".
// When omitted, the model is auto-inferred from the file extension.
func WithModel(model string) ExtractOption {
	return func(c *extractConfig) { c.model = &model }
}

// WithOCR enables OCR for scanned documents.
func WithOCR(enabled bool) ExtractOption {
	return func(c *extractConfig) { c.ocr = enabled }
}

// WithFormula controls formula recognition (default: true).
func WithFormula(enabled bool) ExtractOption {
	return func(c *extractConfig) { c.formula = enabled }
}

// WithTable controls table recognition (default: true).
func WithTable(enabled bool) ExtractOption {
	return func(c *extractConfig) { c.table = enabled }
}

// WithLanguage sets the document language (default: "ch").
func WithLanguage(lang string) ExtractOption {
	return func(c *extractConfig) { c.language = lang }
}

// WithPages sets the page range, e.g. "1-10,15" or "2--2".
func WithPages(pages string) ExtractOption {
	return func(c *extractConfig) { c.pages = &pages }
}

// WithExtraFormats requests additional export formats: "docx", "html", "latex".
func WithExtraFormats(formats ...string) ExtractOption {
	return func(c *extractConfig) { c.extraFormats = formats }
}

// WithPollTimeout sets the maximum duration for the SDK to poll for task
// completion. If the caller's context already carries an earlier deadline,
// that deadline takes precedence.
//
// Default: 5 minutes.
func WithPollTimeout(d time.Duration) ExtractOption {
	return func(c *extractConfig) { c.timeout = d }
}
