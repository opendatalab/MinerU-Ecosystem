# mineru-open-sdk

[中文文档](./README.zh-CN.md)

Go SDK for the [MinerU](https://mineru.net) document extraction API. One call to turn documents into Markdown.

## Install

```bash
go get github.com/OpenDataLab/mineru-open-sdk@latest
```

## Quick Start

```bash
export MINERU_TOKEN="your-api-token"   # get it from https://mineru.net
```

```go
package main

import (
	"context"
	"fmt"
	"log"

	mineru "github.com/OpenDataLab/mineru-open-sdk"
)

func main() {
	client, err := mineru.New("")
	if err != nil {
		log.Fatal(err)
	}
	result, err := client.Extract(context.Background(), "https://example.com/report.pdf")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println(result.Markdown)
}
```

## Usage

### Parse a single document

```go
client, _ := mineru.New("your-token")
result, _ := client.Extract(ctx, "https://example.com/paper.pdf")
fmt.Println(result.Markdown)
fmt.Println(result.ContentList)  // structured JSON
fmt.Println(len(result.Images))  // extracted images
```

### Local files

Local files are uploaded automatically:

```go
result, _ := client.Extract(ctx, "./report.pdf")
```

### Extra format export

Request additional formats alongside the default markdown + JSON:

```go
result, _ := client.Extract(ctx, "https://example.com/report.pdf",
    mineru.WithExtraFormats("docx", "html", "latex"),
)

result.SaveMarkdown("./output/report.md", true)  // markdown + images/ dir
result.SaveDocx("./output/report.docx")
result.SaveHTML("./output/report.html")
result.SaveLaTeX("./output/report.tex")
result.SaveAll("./output/full/")                  // extract the full zip
```

### Crawl a web page

`Crawl` is a shorthand for `Extract` with model="html":

```go
result, _ := client.Crawl(ctx, "https://news.example.com/article/123")
fmt.Println(result.Markdown)
```

### Batch extraction

`ExtractBatch` submits all tasks at once and streams results on a channel — first done, first received:

```go
ch, _ := client.ExtractBatch(ctx, []string{
    "https://example.com/ch1.pdf",
    "https://example.com/ch2.pdf",
    "https://example.com/ch3.pdf",
})
for result := range ch {
    fmt.Printf("%s: %s\n", result.Filename, result.Markdown[:200])
}
```

Batch crawling works the same way:

```go
ch, _ := client.CrawlBatch(ctx, []string{"https://a.com/1", "https://a.com/2"})
for result := range ch {
    fmt.Println(result.Markdown[:200])
}
```

### Async submit + query

For background services or when you need to decouple submission from polling. `Submit` returns a plain task ID string:

```go
taskID, _ := client.Submit(ctx, "https://example.com/big-report.pdf", mineru.WithModel("vlm"))
fmt.Println(taskID) // "a90e6ab6-44f3-4554-..."

// Later:
result, _ := client.GetTask(ctx, taskID)
if result.State == "done" {
    fmt.Println(result.Markdown[:500])
} else {
    fmt.Printf("State: %s, progress: %s\n", result.State, result.Progress)
}
```

Batch version:

```go
batchID, _ := client.SubmitBatch(ctx, []string{"a.pdf", "b.pdf", "c.pdf"})

results, _ := client.GetBatch(ctx, batchID)
for _, r := range results {
    fmt.Printf("%s: %s\n", r.Filename, r.State)
}
```

### Full options

```go
result, err := client.Extract(ctx, "./paper.pdf",
    mineru.WithModel("vlm"),             // "pipeline" | "vlm" | "html"
    mineru.WithOCR(true),                // enable OCR for scanned documents
    mineru.WithFormula(true),            // formula recognition (default: true)
    mineru.WithTable(true),              // table recognition (default: true)
    mineru.WithLanguage("en"),           // document language (default: "ch")
    mineru.WithPages("1-20"),            // page range
    mineru.WithExtraFormats("docx"),     // also export as docx / html / latex
    mineru.WithTimeout(10*time.Minute),  // max wait time (default: 5m)
)
```

### Client options

```go
client, _ := mineru.New("token",
    mineru.WithBaseURL("https://private.example.com/api/v4"),  // private deployment
    mineru.WithHTTPClient(customClient),                        // custom http.Client
)
```

## API Reference

### Methods

| Method | Input | Output | Blocking | Use case |
|--------|-------|--------|----------|----------|
| `Extract(ctx, source)` | `string` | `*ExtractResult` | Yes | Single document |
| `ExtractBatch(ctx, sources)` | `[]string` | `<-chan *ExtractResult` | No (channel) | Batch documents |
| `Crawl(ctx, url)` | `string` | `*ExtractResult` | Yes | Single web page |
| `CrawlBatch(ctx, urls)` | `[]string` | `<-chan *ExtractResult` | No (channel) | Batch web pages |
| `Submit(ctx, source)` | `string` | `string` (task_id) | No | Async submit |
| `SubmitBatch(ctx, sources)` | `[]string` | `string` (batch_id) | No | Async batch submit |
| `GetTask(ctx, taskID)` | `string` | `*ExtractResult` | No | Query task state |
| `GetBatch(ctx, batchID)` | `string` | `[]*ExtractResult` | No | Query batch state |

All methods accept variadic `ExtractOption` arguments (except `GetTask` and `GetBatch`).

### ExtractResult

| Field | Type | Description |
|-------|------|-------------|
| `Markdown` | `string` | Extracted markdown text |
| `ContentList` | `[]map[string]any` | Structured JSON content |
| `Images` | `[]Image` | Extracted images |
| `Docx` | `[]byte` | Docx bytes (requires `WithExtraFormats`) |
| `HTML` | `string` | HTML text (requires `WithExtraFormats`) |
| `LaTeX` | `string` | LaTeX text (requires `WithExtraFormats`) |
| `State` | `string` | `"done"` / `"failed"` / `"pending"` / `"running"` |
| `Error` | `string` | Error message when `State == "failed"` |
| `Progress` | `*Progress` | Page progress when `State == "running"` |

Save methods: `SaveMarkdown(path, withImages)`, `SaveDocx(path)`, `SaveHTML(path)`, `SaveLaTeX(path)`, `SaveAll(dir)`.

### Zero dependencies

This SDK uses only the Go standard library — no external packages required.

## License

MIT
