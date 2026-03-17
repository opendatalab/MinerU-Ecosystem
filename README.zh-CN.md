# mineru-open-sdk

[English](./README.md)

[MinerU](https://mineru.net) 文档解析 API 的 Go SDK。一次调用把文档变成 Markdown。

## 安装

```bash
go get github.com/OpenDataLab/mineru-open-sdk@latest
```

## 快速开始

```bash
export MINERU_TOKEN="your-api-token"   # 在 https://mineru.net 获取
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

`Extract()` 内部完成提交任务、轮询状态、下载结果、解析 zip 的全流程，调用者只看到"传入 URL，拿到 Markdown"。

## 使用示例

### 解析单个文档

```go
client, _ := mineru.New("your-token")
result, _ := client.Extract(ctx, "https://example.com/paper.pdf")
fmt.Println(result.Markdown)
fmt.Println(result.ContentList)  // 结构化 JSON
fmt.Println(len(result.Images))  // 提取的图片列表
```

### 本地文件

自动上传：

```go
result, _ := client.Extract(ctx, "./report.pdf")
```

### 额外格式导出

在默认的 Markdown + JSON 之外，还可以导出其他格式：

```go
result, _ := client.Extract(ctx, "https://example.com/report.pdf",
    mineru.WithExtraFormats("docx", "html", "latex"),
)

result.SaveMarkdown("./output/report.md", true)  // markdown + images/ 目录
result.SaveDocx("./output/report.docx")
result.SaveHTML("./output/report.html")
result.SaveLaTeX("./output/report.tex")
result.SaveAll("./output/full/")                  // 解压完整 zip
```

### 网页抓取

`Crawl` 等价于 `Extract` + `WithModel("html")`：

```go
result, _ := client.Crawl(ctx, "https://news.example.com/article/123")
fmt.Println(result.Markdown)
```

### 批量解析

`ExtractBatch` 一次性提交所有任务，通过 channel 流式返回结果——先完成的先收到：

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

批量网页抓取同理：

```go
ch, _ := client.CrawlBatch(ctx, []string{"https://a.com/1", "https://a.com/2"})
for result := range ch {
    fmt.Println(result.Markdown[:200])
}
```

### 异步提交 + 查询

适用于后台服务或需要将提交和查询解耦的场景。`Submit` 返回纯字符串 task ID：

```go
taskID, _ := client.Submit(ctx, "https://example.com/big-report.pdf", mineru.WithModel("vlm"))
fmt.Println(taskID) // "a90e6ab6-44f3-4554-..."

// 随时查询：
result, _ := client.GetTask(ctx, taskID)
if result.State == "done" {
    fmt.Println(result.Markdown[:500])
} else {
    fmt.Printf("状态: %s, 进度: %s\n", result.State, result.Progress)
}
```

批量版本：

```go
batchID, _ := client.SubmitBatch(ctx, []string{"a.pdf", "b.pdf", "c.pdf"})

results, _ := client.GetBatch(ctx, batchID)
for _, r := range results {
    fmt.Printf("%s: %s\n", r.Filename, r.State)
}
```

### 完整参数

```go
result, err := client.Extract(ctx, "./paper.pdf",
    mineru.WithModel("vlm"),             // "pipeline" | "vlm" | "html"（不传则自动推断）
    mineru.WithOCR(true),                // 扫描件启用 OCR
    mineru.WithFormula(true),            // 公式识别（默认开启）
    mineru.WithTable(true),              // 表格识别（默认开启）
    mineru.WithLanguage("en"),           // 文档语言（默认 "ch"）
    mineru.WithPages("1-20"),            // 页码范围
    mineru.WithExtraFormats("docx"),     // 额外导出 docx / html / latex
    mineru.WithPollTimeout(10*time.Minute),  // 轮询最大等待时间（默认 5 分钟）
)
```

### 客户端选项

```go
client, _ := mineru.New("token",
    mineru.WithBaseURL("https://private.example.com/api/v4"),  // 私有化部署
    mineru.WithHTTPClient(customClient),                        // 自定义 http.Client
)
```

### Flash 模式（无需 token）

Flash 模式使用轻量级 API，速度优先。无需 API token，仅输出 Markdown —— 不支持模型选择和额外格式导出。

```go
client := mineru.NewFlash()
result, _ := client.FlashExtract(ctx, "https://example.com/report.pdf")
fmt.Println(result.Markdown)
```

带参数：

```go
result, _ := client.FlashExtract(ctx, "./report.pdf",
    mineru.WithFlashLanguage("en"),   // 文档语言（默认 "ch"）
    mineru.WithFlashPages("1-10"),    // 页码范围
    mineru.WithFlashTimeout(10*time.Minute),  // 轮询最大等待（默认 5 分钟）
)
result.SaveMarkdown("./output/report.md", false)
```

Flash 模式限制：最多 50 页，最大 10 MB。

`mineru.New("token")` 创建的客户端同时支持 `Extract()` 和 `FlashExtract()`。`mineru.NewFlash()` 创建的仅 flash 客户端，调用标准方法会返回 `ErrNoAuthClient`。

## API 速查

### 方法

| 方法 | 输入 | 输出 | 阻塞 | 场景 |
|------|------|------|------|------|
| `Extract(ctx, source)` | `string` | `*ExtractResult` | 是 | 单个文档 |
| `ExtractBatch(ctx, sources)` | `[]string` | `<-chan *ExtractResult` | 否（channel） | 批量文档 |
| `Crawl(ctx, url)` | `string` | `*ExtractResult` | 是 | 单个网页 |
| `CrawlBatch(ctx, urls)` | `[]string` | `<-chan *ExtractResult` | 否（channel） | 批量网页 |
| `Submit(ctx, source)` | `string` | `string`（task_id） | 否 | 异步提交 |
| `SubmitBatch(ctx, sources)` | `[]string` | `string`（batch_id） | 否 | 异步批量提交 |
| `GetTask(ctx, taskID)` | `string` | `*ExtractResult` | 否 | 查询状态 |
| `GetBatch(ctx, batchID)` | `string` | `[]*ExtractResult` | 否 | 查询批量状态 |
| `FlashExtract(ctx, source)` | `string` | `*ExtractResult` | 是 | Flash 模式（无需 token） |

所有方法都接受可变参数 `ExtractOption`（`GetTask` 和 `GetBatch` 除外）。

### ExtractResult 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `Markdown` | `string` | Markdown 正文 |
| `ContentList` | `[]map[string]any` | 结构化 JSON 内容 |
| `Images` | `[]Image` | 提取的图片 |
| `Docx` | `[]byte` | docx 二进制（需 `WithExtraFormats`） |
| `HTML` | `string` | HTML 文本（需 `WithExtraFormats`） |
| `LaTeX` | `string` | LaTeX 文本（需 `WithExtraFormats`） |
| `State` | `string` | `"done"` / `"failed"` / `"pending"` / `"running"` |
| `Error` | `string` | 失败原因（`State == "failed"` 时） |
| `Progress` | `*Progress` | 页级进度（`State == "running"` 时） |

保存方法：`SaveMarkdown(path, withImages)`, `SaveDocx(path)`, `SaveHTML(path)`, `SaveLaTeX(path)`, `SaveAll(dir)`

### model 参数

| `WithModel(...)` | 说明 |
|-------------------|------|
| 不传（默认） | 自动推断：`.html` → `"html"`，其余 → `"vlm"` |
| `"vlm"` | VLM 视觉语言模型（推荐） |
| `"pipeline"` | 传统版面分析 |
| `"html"` | 网页解析 |

### 零依赖

本 SDK 仅使用 Go 标准库，无任何外部依赖。

## License

MIT
