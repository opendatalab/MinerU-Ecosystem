package mineru

import (
	"net/http"
	"time"
)

// ---------------------------------------------------------------------------
// Constants & Defaults
// ---------------------------------------------------------------------------

const (
	// DefaultBaseURL is the default standard MinerU API base URL.
	DefaultBaseURL = "https://mineru.net/api/v4"

	// DefaultFlashBaseURL is the default flash MinerU API base URL.
	// TODO(release): 上线前换回 https://mineru.net/api/v1/agent
	DefaultFlashBaseURL = "https://staging.mineru.org.cn/api/v1/agent"

	// DefaultRequestTimeout is the timeout for a single HTTP request (e.g., upload, query).
	DefaultRequestTimeout = 60 * time.Second

	// DefaultSinglePollTimeout is the total time to wait for a single document extraction.
	DefaultSinglePollTimeout = 5 * time.Minute

	// DefaultBatchPollTimeout is the total time to wait for a batch of documents.
	DefaultBatchPollTimeout = 30 * time.Minute
)

func defaultClientConfig() clientConfig {
	return clientConfig{
		baseURL:      DefaultBaseURL,
		flashBaseURL: DefaultFlashBaseURL,
		// This is the HTTP connection timeout for single requests.
		httpClient: &http.Client{Timeout: DefaultRequestTimeout},
	}
}

// ---------------------------------------------------------------------------
// Client options
// ---------------------------------------------------------------------------

type clientConfig struct {
	baseURL      string
	flashBaseURL string
	httpClient   *http.Client
}

// ClientOption configures the [Client] constructor.
type ClientOption func(*clientConfig)

// WithBaseURL overrides the default API base URL (for private deployments).
func WithBaseURL(url string) ClientOption {
	return func(c *clientConfig) { c.baseURL = url }
}

// WithFlashBaseURL overrides the default flash API base URL.
func WithFlashBaseURL(url string) ClientOption {
	return func(c *clientConfig) { c.flashBaseURL = url }
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
	ocr          *bool
	formula      *bool
	table        *bool
	language     *string
	pages        *string
	extraFormats []string
	fileParams   map[string]FileParam
	timeout      time.Duration // This is the business polling timeout
}

func defaultExtractConfig() extractConfig {
	return extractConfig{
		timeout: DefaultSinglePollTimeout,
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
	return func(c *extractConfig) { c.ocr = &enabled }
}

// WithFormula controls formula recognition. Only sent to API when explicitly set.
func WithFormula(enabled bool) ExtractOption {
	return func(c *extractConfig) { c.formula = &enabled }
}

// WithTable controls table recognition. Only sent to API when explicitly set.
func WithTable(enabled bool) ExtractOption {
	return func(c *extractConfig) { c.table = &enabled }
}

// WithLanguage sets the document language. Only sent to API when explicitly set.
func WithLanguage(lang string) ExtractOption {
	return func(c *extractConfig) { c.language = &lang }
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
// Per-file parameters for batch methods
// ---------------------------------------------------------------------------

// FileParam holds per-file overrides for batch extraction.
// Fields left at zero value inherit the global ExtractOption defaults.
type FileParam struct {
	// Pages overrides page_ranges for this file (e.g. "1-10,15").
	Pages string

	// OCR overrides is_ocr for this file. nil inherits the global WithOCR value.
	OCR *bool

	// DataID sets data_id for this file, used to correlate with your business data.
	DataID string
}

// WithFileParams provides per-file overrides keyed by path or URL.
// Keys must match the strings passed to ExtractBatch / SubmitBatch / CrawlBatch.
//
//	client.SubmitBatch(ctx, []string{"a.pdf", "b.pdf"},
//	    mineru.WithFileParams(map[string]mineru.FileParam{
//	        "a.pdf": {Pages: "1-5"},
//	        "b.pdf": {Pages: "10-20", OCR: mineru.Bool(true)},
//	    }),
//	)
func WithFileParams(params map[string]FileParam) ExtractOption {
	return func(c *extractConfig) { c.fileParams = params }
}

// Bool is a helper that returns a pointer to a bool value,
// useful for setting optional per-file fields like [FileParam.OCR].
func Bool(v bool) *bool { return &v }

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
