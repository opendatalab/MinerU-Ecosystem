# MinerU Open API SDK (Go)

[![Go Reference](https://pkg.go.dev/badge/github.com/opendatalab/MinerU-Ecosystem/sdk/go.svg)](https://pkg.go.dev/github.com/opendatalab/MinerU-Ecosystem/sdk/go)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)

[中文文档](./README.zh-CN.md)

**MinerU Open API SDK** is a completely free, zero-dependency Go library for the [MinerU](https://mineru.net) document extraction service. Turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown with just one call.

---

## 🚀 Key Features

- **Completely Free**: No hidden costs for document extraction.
- **Zero Dependencies**: Uses only the Go standard library.
- **Flash Mode (No Auth)**: Extract text instantly without an API token.
- **Precision Mode**: Comprehensive extraction with layout preservation, images, and formula support.
- **Blocking And Async Primitives**: Use blocking helpers for simple flows, or `Submit()` / `GetBatch()` / `GetTask()` when you want your own polling.
- **Result Save Helpers**: Save Markdown, HTML, LaTeX, DOCX, images, or the full extracted zip.

---

## 📦 Install

```bash
go get github.com/opendatalab/MinerU-Ecosystem/sdk/go@latest
```

---

## 🛠️ Quick Start

### 1. Flash Extract (Fast, No Auth, Markdown-only)
Ideal for quick previews. No token required.

```go
package main

import (
    "context"
    "fmt"

    mineru "github.com/opendatalab/MinerU-Ecosystem/sdk/go"
)

func main() {
    client := mineru.NewFlash()
    result, err := client.FlashExtract(
        context.Background(),
        "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    )
    if err != nil {
        panic(err)
    }

    fmt.Println(result.Markdown)
}
```

### 2. Precision Extract (Auth Required)
Supports large files, rich assets (images/tables), and multiple formats.

```go
package main

import (
    "context"
    "fmt"

    mineru "github.com/opendatalab/MinerU-Ecosystem/sdk/go"
)

func main() {
    client, err := mineru.New("your-api-token")
    if err != nil {
        panic(err)
    }

    result, err := client.Extract(
        context.Background(),
        "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    )
    if err != nil {
        panic(err)
    }

    fmt.Println(result.Markdown)
    fmt.Println(len(result.Images))
}
```

---

## 🧩 Supported Public API

### Constructors and client lifecycle

- `mineru.New(token string, opts ...ClientOption) (*Client, error)`
- `mineru.NewFlash(opts ...ClientOption) *Client`
- `client.SetSource("your-app")`
- `mineru.WithBaseURL(url)`
- `mineru.WithFlashBaseURL(url)`
- `mineru.WithHTTPClient(client)`

### Blocking extraction methods

- `client.Extract(ctx, source, opts...) -> (*ExtractResult, error)`
- `client.ExtractBatch(ctx, sources, opts...) -> (<-chan *ExtractResult, error)`
- `client.Crawl(ctx, url, opts...) -> (*ExtractResult, error)`
- `client.CrawlBatch(ctx, urls, opts...) -> (<-chan *ExtractResult, error)`
- `client.FlashExtract(ctx, source, opts...) -> (*ExtractResult, error)`

### Submit/query methods

- `client.Submit(ctx, source, opts...) -> (string, error)`
- `client.SubmitBatch(ctx, sources, opts...) -> (string, error)`
- `client.GetTask(ctx, taskID) -> (*ExtractResult, error)`
- `client.GetBatch(ctx, batchID) -> ([]*ExtractResult, error)`

### Result helpers

- `result.SaveMarkdown(path, withImages)`
- `result.SaveDocx(path)`
- `result.SaveHTML(path)`
- `result.SaveLaTeX(path)`
- `result.SaveAll(dir)`
- `image.Save(path)`
- `result.Err()`
- `progress.Percent()`
- `progress.String()`

### Result fields you will usually use

- `result.TaskID`
- `result.State`
- `result.Progress`
- `result.Markdown`
- `result.Images`
- `result.ContentList`
- `result.Docx`
- `result.HTML`
- `result.LaTeX`
- `result.Filename`
- `result.Error`

---

## 📊 Mode Comparison

| Feature | Flash Extract | Precision Extract |
| :--- | :--- | :--- |
| **Auth** | **No Auth Required** | **Auth Required (Token)** |
| **Speed** | Blazing Fast | Standard |
| **File Limit** | Max 10 MB | Max 200 MB |
| **Page Limit** | Max 20 Pages | Max 600 Pages |
| **Formats** | PDF, Images, Docx, PPTx, Excel | PDF, Images, Doc/x, Ppt/x, Html |
| **Content** | Markdown only (Placeholders) | Full assets (Images, Tables, Formulas) |
| **Output** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## ⚙️ Defaults And Option Behavior

### Constructors

| Constructor / Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `New(token, opts...)` | `token` must be non-empty or provided via `MINERU_TOKEN` | If both are empty, `New` returns `AuthError`; it does not fall back to flash-only mode |
| `NewFlash(opts...)` | No token required | Creates a flash-only client; auth-required methods such as `Extract()` / `Submit()` / `GetTask()` return `ErrNoAuthClient` |
| `WithBaseURL(url)` | `https://mineru.net/api/v4` | Overrides the standard API base URL only |
| `WithFlashBaseURL(url)` | Flash default base URL | Overrides the flash API base URL only |
| `WithHTTPClient(client)` | SDK-managed `http.Client` | Uses your custom HTTP client for both standard and flash requests |

### HTTP and polling defaults

| Setting | Default | Meaning |
| :--- | :--- | :--- |
| `DefaultRequestTimeout` | `60 * time.Second` | Default timeout of the SDK-created `http.Client` |
| `WithPollTimeout(...)` | `5 * time.Minute` | Total polling timeout for `Extract()` / `Crawl()` / `Submit()` follow-up flows |
| `WithPollTimeout(...)` on `ExtractBatch()` / `CrawlBatch()` | auto-promoted to `30 * time.Minute` when left at the single-item default | Total timeout for all batch polling |
| `WithFlashTimeout(...)` | `5 * time.Minute` | Total polling timeout for `FlashExtract()` |

### Precision extraction options

These defaults apply to `Extract()`, `ExtractBatch()`, `Submit()`, and `SubmitBatch()` unless noted otherwise.

| Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `WithModel(...)` | not set | Auto-infers model: `.html` / `.htm` uses `"html"` (`"MinerU-HTML"` at the API layer), everything else uses `"vlm"` |
| `WithOCR(true)` | not set | OCR is disabled (API default) |
| `WithFormula(false)` | not set | Formula recognition is enabled (API default) |
| `WithTable(false)` | not set | Table recognition is enabled (API default) |
| `WithLanguage(...)` | not set | Chinese `"ch"` (API default) |
| `WithPages(...)` | not set | Full document is processed |
| `WithExtraFormats(...)` | none | Only the default Markdown/JSON payload is returned |
| `WithFileParams(map)` | none | Per-file overrides for batch methods. A `map[string]FileParam` keyed by path/URL, where `FileParam` has fields `Pages`, `OCR`, `DataID` |

### `Crawl()` / `CrawlBatch()`

- `Crawl()` is shorthand for `Extract(..., WithModel("html"))`
- `CrawlBatch()` is shorthand for `ExtractBatch(..., WithModel("html"))`
- They still accept the same `ExtractOption` values, so you can set `WithExtraFormats(...)` or `WithPollTimeout(...)` if needed

### Flash mode options

| Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `WithFlashLanguage(...)` | `"ch"` | Chinese is the default |
| `WithFlashPages(...)` | not set | Full page range allowed by the flash API |
| `WithFlashTimeout(...)` | `5 * time.Minute` | Total polling timeout |

---

## 🔀 `New()` vs `NewFlash()`

Use `New(token)` when you need the standard authenticated API:

- supports `Extract()`, `ExtractBatch()`, `Crawl()`, `CrawlBatch()`, `Submit()`, `SubmitBatch()`, `GetTask()`, and `GetBatch()`
- also keeps flash capability available, so `client.FlashExtract(...)` still works on a client created with `New(...)`
- requires a token argument or `MINERU_TOKEN`

Use `NewFlash()` when you only need fast no-auth extraction:

- supports `FlashExtract()` only
- standard authenticated methods return `ErrNoAuthClient`
- useful for public previews, demos, or environments where you intentionally do not want token-backed methods

---

## 📖 Detailed Usage

### Precision Extraction Options

```go
result, err := client.Extract(ctx, "./paper.pdf",
    mineru.WithModel("vlm"),
    mineru.WithOCR(true),
    mineru.WithFormula(true),
    mineru.WithTable(true),
    mineru.WithLanguage("en"),
    mineru.WithPages("1-20"),
    mineru.WithExtraFormats("docx"),
    mineru.WithPollTimeout(10*time.Minute),
)
if err != nil {
    panic(err)
}

if err := result.SaveAll("./output"); err != nil {
    panic(err)
}
```

### Batch Processing

```go
ch, err := client.ExtractBatch(ctx, []string{"a.pdf", "b.pdf"})
if err != nil {
    panic(err)
}

for result := range ch {
    fmt.Printf("%s: %s\n", result.Filename, result.State)
}
```

### Batch With Per-File Pages

```go
batchID, err := client.SubmitBatch(ctx, []string{"a.pdf", "b.pdf"},
    mineru.WithFileParams(map[string]mineru.FileParam{
        "a.pdf": {Pages: "1-5"},
        "b.pdf": {Pages: "10-20"},
    }),
)
```

### Web Crawling

```go
result, err := client.Crawl(ctx, "https://www.baidu.com")
if err != nil {
    panic(err)
}

fmt.Println(result.Markdown)
```

---

## 🔄 `Submit()` / `GetBatch()` Semantics

The important Go-specific rule is simple:

- `Submit()` returns a **batch ID**
- `SubmitBatch()` also returns a **batch ID**
- the normal async flow is therefore `Submit(...) -> GetBatch(batchID)`
- `GetTask(taskID)` is only useful when you obtained a real task ID from somewhere else, not from `Submit()`

### Why `Submit()` returns a batch ID

The Go SDK deliberately normalizes both single-URL and local-file submissions onto batch semantics:

- a single URL is submitted through the batch endpoint internally
- a single local file is uploaded through the batch upload flow internally
- that means `Submit()` always gives you a batch-oriented handle

### Recommended polling pattern

```go
batchID, err := client.Submit(ctx, "https://example.com/large-report.pdf")
if err != nil {
    panic(err)
}

for {
    results, err := client.GetBatch(ctx, batchID)
    if err != nil {
        panic(err)
    }

    result := results[0]
    if result.State == "done" || result.State == "failed" {
        break
    }

    time.Sleep(5 * time.Second)
}
```

### What `GetBatch()` populates

- in-progress tasks mainly expose metadata such as `State`, `Progress`, `TaskID`, and possible error fields
- once a task reaches `State == "done"` and a zip URL is available, `GetBatch()` automatically downloads and parses the zip so `Markdown`, `Images`, `ContentList`, `Docx`, `HTML`, and `LaTeX` become available

---

## 🤖 Integration for AI Agents

The SDK exposes enough state for backend agent loops via `result.State` and `result.Progress`.

```go
batchID, err := client.Submit(ctx, "https://example.com/large-report.pdf")
if err != nil {
    panic(err)
}

results, err := client.GetBatch(ctx, batchID)
if err != nil {
    panic(err)
}
if len(results) > 0 && results[0].State == "done" {
    processMarkdown(results[0].Markdown)
}
```

---

## 📄 License

This project is licensed under the Apache-2.0 License.

## 🔗 Links

- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/apiManage/docs)
