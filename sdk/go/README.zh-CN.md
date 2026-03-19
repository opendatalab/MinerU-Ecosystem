# MinerU Open API SDK (Go)

[![Go Reference](https://pkg.go.dev/badge/github.com/opendatalab/MinerU-Ecosystem/sdk/go.svg)](https://pkg.go.dev/github.com/opendatalab/MinerU-Ecosystem/sdk/go)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)

[English README](./README.md)

**MinerU Open API SDK** 是一个完全免费、零依赖的 Go 语言库，用于连接 [MinerU](https://mineru.net) 文档提取服务。只需一次调用，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

---

## 🚀 核心特性

- **完全免费**：文档提取服务没有任何隐藏费用。
- **零依赖**：仅使用 Go 标准库，不引入任何外部依赖。
- **极速模式 (No Auth)**：无需 API Token 即可立即提取。
- **全功能模式**：提供完整的版式保留、图片、表格及公式支持。
- **阻塞式与异步原语并存**：简单流程直接用阻塞式方法，需要自定义轮询时使用 `Submit()` / `GetBatch()` / `GetTask()`。
- **结果保存辅助方法**：可直接保存 Markdown、HTML、LaTeX、DOCX、图片，或解压完整结果包。

---

## 📦 安装指南

```bash
go get github.com/opendatalab/MinerU-Ecosystem/sdk/go@latest
```

---

## 🛠️ 快速上手

### 1. 极速模式 (Flash Extract - 免登录，只支持 Markdown)
适合快速预览。无需配置 Token。

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

### 2. 全功能模式 (Full Feature Extract - 需登录)
支持大文件、丰富资产（图片/表格）及多种输出格式。

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

## 🧩 支持的公开接口

### 构造与 Client 生命周期

- `mineru.New(token string, opts ...ClientOption) (*Client, error)`
- `mineru.NewFlash(opts ...ClientOption) *Client`
- `client.SetSource("your-app")`
- `mineru.WithBaseURL(url)`
- `mineru.WithFlashBaseURL(url)`
- `mineru.WithHTTPClient(client)`

### 阻塞式解析接口

- `client.Extract(ctx, source, opts...) -> (*ExtractResult, error)`
- `client.ExtractBatch(ctx, sources, opts...) -> (<-chan *ExtractResult, error)`
- `client.Crawl(ctx, url, opts...) -> (*ExtractResult, error)`
- `client.CrawlBatch(ctx, urls, opts...) -> (<-chan *ExtractResult, error)`
- `client.FlashExtract(ctx, source, opts...) -> (*ExtractResult, error)`

### 提交 / 查询接口

- `client.Submit(ctx, source, opts...) -> (string, error)`
- `client.SubmitBatch(ctx, sources, opts...) -> (string, error)`
- `client.GetTask(ctx, taskID) -> (*ExtractResult, error)`
- `client.GetBatch(ctx, batchID) -> ([]*ExtractResult, error)`

### 结果辅助方法

- `result.SaveMarkdown(path, withImages)`
- `result.SaveDocx(path)`
- `result.SaveHTML(path)`
- `result.SaveLaTeX(path)`
- `result.SaveAll(dir)`
- `image.Save(path)`
- `result.Err()`
- `progress.Percent()`
- `progress.String()`

### 常用结果字段

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

## 📊 模式对比

| 特性 | 极速模式 (Flash) | 全功能模式 (Full Feature) |
| :--- | :--- | :--- |
| **身份认证** | **免登录 (No Auth)** | **需登录 (Token)** |
| **处理速度** | 极速 | 标准 |
| **文件大小上限** | 最大 10 MB | 最大 200 MB |
| **文件页数上限** | 最大 20 页 | 最大 600 页 |
| **支持格式** | PDF, 图片, Docx, PPTx, Excel | PDF, 图片, Doc/x, Ppt/x, Html |
| **内容完整度** | 仅文本 (图片、表格、公式显示占位符) | 完整资源 (图片、表格、公式全部保留) |
| **输出格式** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## ⚙️ 默认行为与参数说明

### 构造函数

| 构造 / 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `New(token, opts...)` | `token` 必须非空，或由 `MINERU_TOKEN` 提供 | 如果两者都为空，`New` 会返回 `AuthError`，不会退化为 flash-only mode |
| `NewFlash(opts...)` | 无需 token | 创建 flash-only client；`Extract()` / `Submit()` / `GetTask()` 等鉴权接口会返回 `ErrNoAuthClient` |
| `WithBaseURL(url)` | `https://mineru.net/api/v4` | 只覆盖标准 API 的 base URL |
| `WithFlashBaseURL(url)` | flash 默认 base URL | 只覆盖 flash API 的 base URL |
| `WithHTTPClient(client)` | SDK 默认创建的 `http.Client` | 自定义 HTTP client 会同时用于标准 API 和 flash API |

### HTTP 与轮询默认值

| 设置 | 默认值 | 含义 |
| :--- | :--- | :--- |
| `DefaultRequestTimeout` | `60 * time.Second` | SDK 默认 `http.Client` 的单次请求超时 |
| `WithPollTimeout(...)` | `5 * time.Minute` | `Extract()` / `Crawl()` 及其后续轮询的总超时 |
| `WithPollTimeout(...)` 用于 `ExtractBatch()` / `CrawlBatch()` | 如果仍保持单任务默认值，则自动提升到 `30 * time.Minute` | 整个批次轮询的总超时 |
| `WithFlashTimeout(...)` | `5 * time.Minute` | `FlashExtract()` 的总轮询超时 |

### 全功能提取选项

这些默认值适用于 `Extract()`、`ExtractBatch()`、`Submit()`、`SubmitBatch()`，除非特别说明。

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `WithModel(...)` | 不设置 | 自动推断：`.html` / `.htm` 走 `"html"`（发给 API 时为 `"MinerU-HTML"`），其余默认 `"vlm"` |
| `WithOCR(true)` | `false` | 默认关闭 OCR，只有启用时才发送 |
| `WithFormula(false)` | `true` | 默认开启公式识别 |
| `WithTable(false)` | `true` | 默认开启表格识别 |
| `WithLanguage(...)` | `"ch"` | 默认中文；只有修改时才显式传给 API |
| `WithPages(...)` | 不设置 | 默认处理完整文档 |
| `WithExtraFormats(...)` | 无 | 只返回默认 Markdown / JSON 结果 |

### `Crawl()` / `CrawlBatch()`

- `Crawl()` 等价于 `Extract(..., WithModel("html"))`
- `CrawlBatch()` 等价于 `ExtractBatch(..., WithModel("html"))`
- 它们仍然接受同一组 `ExtractOption`，因此也可以叠加 `WithExtraFormats(...)` 或 `WithPollTimeout(...)`

### Flash 模式选项

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `WithFlashLanguage(...)` | `"ch"` | 默认中文 |
| `WithFlashPages(...)` | 不设置 | 默认处理 flash API 允许的完整页范围 |
| `WithFlashTimeout(...)` | `5 * time.Minute` | 总轮询超时 |

---

## 🔀 `New()` 与 `NewFlash()` 的区别

需要标准鉴权 API 时，使用 `New(token)`：

- 支持 `Extract()`、`ExtractBatch()`、`Crawl()`、`CrawlBatch()`、`Submit()`、`SubmitBatch()`、`GetTask()`、`GetBatch()`
- 同时也保留 flash 能力，因此通过 `New(...)` 创建的 client 依然可以调用 `FlashExtract(...)`
- 必须提供 token，或在环境变量里提供 `MINERU_TOKEN`

只需要免登录快速提取时，使用 `NewFlash()`：

- 只保证 `FlashExtract()` 可用
- 标准鉴权方法会返回 `ErrNoAuthClient`
- 适合公开预览、演示场景，或明确不希望暴露 token 能力的环境

---

## 📖 详细用法

### 全功能提取选项

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

### 批量处理

```go
ch, err := client.ExtractBatch(ctx, []string{"a.pdf", "b.pdf"})
if err != nil {
    panic(err)
}

for result := range ch {
    fmt.Printf("%s: %s\n", result.Filename, result.State)
}
```

### 网页抓取

```go
result, err := client.Crawl(ctx, "https://www.baidu.com")
if err != nil {
    panic(err)
}

fmt.Println(result.Markdown)
```

---

## 🔄 `Submit()` / `GetBatch()` 语义说明

Go SDK 这里最重要的一条规则是：

- `Submit()` 返回的是 **batch ID**
- `SubmitBatch()` 返回的也是 **batch ID**
- 因此最常见的异步流程应该是 `Submit(...) -> GetBatch(batchID)`
- `GetTask(taskID)` 只有在你已经从别处拿到真实 task ID 时才适合使用，不能假定它来自 `Submit()`

### 为什么 `Submit()` 返回 batch ID

Go SDK 在实现上刻意把单任务提交也统一到了 batch 语义：

- 单个 URL 会通过 batch endpoint 提交
- 单个本地文件会通过 batch upload 流程提交
- 所以 `Submit()` 始终返回一个适合 `GetBatch()` 轮询的 ID

### 推荐轮询方式

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

### `GetBatch()` 什么时候填充内容字段

- 当任务仍处于 pending / running 等非终态时，返回值主要包含 `State`、`Progress`、`TaskID` 以及可能的错误字段
- 当任务进入 `State == "done"` 且服务端提供 zip 地址后，`GetBatch()` 会自动下载并解析结果包，此时 `Markdown`、`Images`、`ContentList`、`Docx`、`HTML`、`LaTeX` 等字段才会被填充

---

## 🤖 AI Agent 自动化集成

SDK 提供了适合后端 Agent 循环使用的状态字段，核心就是 `result.State` 和 `result.Progress`。

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

## 📄 开源协议

本项目采用 Apache-2.0 协议。

## 🔗 相关链接

- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/docs)
