package mineru

import (
	"net/http"
	"time"
)

// ---------------------------------------------------------------------------
// Constants & Defaults
// ---------------------------------------------------------------------------

const (
	// DefaultRequestTimeout is the timeout for a single HTTP request (e.g., upload, query).
	DefaultRequestTimeout = 60 * time.Second

	// DefaultSinglePollTimeout is the total time to wait for a single document extraction.
	DefaultSinglePollTimeout = 5 * time.Minute

	// DefaultBatchPollTimeout is the total time to wait for a batch of documents.
	DefaultBatchPollTimeout = 30 * time.Minute
)

func defaultClientConfig() clientConfig {
	return clientConfig{
		baseURL: "https://mineru.net/api/v4",
		// This is the HTTP connection timeout for single requests.
		httpClient: &http.Client{Timeout: DefaultRequestTimeout},
	}
}

// ---------------------------------------------------------------------------
// Client options
// ---------------------------------------------------------------------------

type clientConfig struct {
	baseURL    string
	httpClient *http.Client
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
	timeout      time.Duration // This is the business polling timeout
}

func defaultExtractConfig() extractConfig {
	return extractConfig{
		formula:  true,
		table:    true,
		language: "ch",
		timeout:  DefaultSinglePollTimeout,
	}
}

// ExtractOption configures an extraction request.
type ExtractOption func(*extractConfig)

// WithModel sets the model version: "pipeline", "vlm", or "html".
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

// WithPollTimeout sets the maximum total duration to wait for task completion.
//
// Default: DefaultSinglePollTimeout (5 minutes).
func WithPollTimeout(d time.Duration) ExtractOption {
	return func(c *extractConfig) { c.timeout = d }
}

// ---------------------------------------------------------------------------
// FlashExtract options
// ---------------------------------------------------------------------------

type flashExtractConfig struct {
	language string
	pages    *string
	timeout  time.Duration // Business polling timeout
}

func defaultFlashExtractConfig() flashExtractConfig {
	return flashExtractConfig{
		language: "ch",
		timeout:  DefaultSinglePollTimeout,
	}
}

// FlashExtractOption configures a [Client.FlashExtract] request.
type FlashExtractOption func(*flashExtractConfig)

// WithFlashLanguage sets the document language for flash extraction (default: "ch").
func WithFlashLanguage(lang string) FlashExtractOption {
	return func(c *flashExtractConfig) { c.language = lang }
}

// WithFlashPages sets the page range for flash extraction, e.g. "1-10".
func WithFlashPages(pages string) FlashExtractOption {
	return func(c *flashExtractConfig) { c.pages = &pages }
}

// WithFlashTimeout sets the maximum polling duration for flash extraction.
// Default: DefaultSinglePollTimeout (5 minutes).
func WithFlashTimeout(d time.Duration) FlashExtractOption {
	return func(c *flashExtractConfig) { c.timeout = d }
}
