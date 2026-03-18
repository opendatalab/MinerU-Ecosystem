# MinerU Open API SDK (Go)

[![Go Reference](https://pkg.go.dev/badge/github.com/OpenDataLab/mineru-open-sdk-go.svg)](https://pkg.go.dev/github.com/OpenDataLab/mineru-open-sdk-go)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/OpenDataLab/mineru-open-sdk-go/blob/main/LICENSE)

[中文文档](./README.zh-CN.md)

**MinerU Open API SDK** is a completely free, zero-dependency Go library for the [MinerU](https://mineru.net) document extraction service. Turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown with just one call.

---

## 🚀 Key Features

- **Completely Free**: No hidden costs for document extraction.
- **Zero Dependencies**: Uses only the Go standard library.
- **Flash Mode (No Auth)**: Extract text instantly without an API token.
- **Full Feature Mode**: Comprehensive extraction with layout preservation, images, and formula support.
- **Concurrency**: Native Go channel support for efficient batch processing.

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
import "github.com/opendatalab/MinerU-Ecosystem/sdk/go"

// No token needed for Flash Mode
client := mineru.NewFlash()
result, _ := client.FlashExtract(ctx, "https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

fmt.Println(result.Markdown)
```

### 2. Full Feature Extract (Auth Required)
Supports large files, rich assets (images/tables), and multiple formats.
```go
import "github.com/opendatalab/MinerU-Ecosystem/sdk/go"

// Get your free token from https://mineru.net
client, _ := mineru.New("your-api-token")
result, _ := client.Extract(ctx, "https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

fmt.Println(result.Markdown)
fmt.Println(len(result.Images)) // Access extracted images
```

---

## 📊 Mode Comparison

| Feature | Flash Extract | Full Feature Extract |
| :--- | :--- | :--- |
| **Auth** | **No Auth Required** | **Auth Required (Token)** |
| **Speed** | Blazing Fast | Standard |
| **File Limit** | Max 10 MB | Max 200 MB |
| **Page Limit** | Max 20 Pages | Max 600 Pages |
| **Formats** | PDF, Images, Docx, PPTx, Excel | PDF, Images, Doc/x, Ppt/x, Html |
| **Content** | Markdown only (Placeholders) | Full assets (Images, Tables, Formulas) |
| **Output** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## 📖 Detailed Usage

### Full Feature Extraction Options
```go
result, _ := client.Extract(ctx, "./paper.pdf",
    mineru.WithModel("vlm"),             // "vlm" | "pipeline" | "html"
    mineru.WithOCR(true),                // Enable OCR for scanned documents
    mineru.WithFormula(true),            // Formula recognition
    mineru.WithTable(true),              // Table recognition
    mineru.WithLanguage("en"),           // "ch" | "en" | etc.
    mineru.WithPages("1-20"),            // Page range
    mineru.WithExtraFormats("docx"),     // Export as docx, html, or latex
    mineru.WithPollTimeout(10*time.Minute),
)

result.SaveAll("./output/") // Save markdown and all assets
```

### Batch Processing
```go
// Returns a channel that streams results as they complete
ch, _ := client.ExtractBatch(ctx, []string{"a.pdf", "b.pdf"})
for result := range ch {
    fmt.Printf("%s: Done\n", result.Filename)
}
```

### Web Crawling
```go
result, _ := client.Crawl(ctx, "https://www.baidu.com")
fmt.Println(result.Markdown)
```

---

## 🤖 Integration for AI Agents

Perfect for Go-based AI backend services. Status and progress can be monitored via `result.State` and `result.Progress`.

```go
taskID, _ := client.Submit(ctx, "report.pdf")
// ... later ...
result, _ := client.GetTask(ctx, taskID)
if result.State == "done" {
    processMarkdown(result.Markdown)
}
```

---

## 📄 License
This project is licensed under the MIT License.

## 🔗 Links
- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/docs)
