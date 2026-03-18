# MinerU Open API SDK (Go)

[![Go Reference](https://pkg.go.dev/badge/github.com/opendatalab/MinerU-Ecosystem/sdk/go-go.svg)](https://pkg.go.dev/github.com/opendatalab/MinerU-Ecosystem/sdk/go-go)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/sdk/go-go/blob/main/LICENSE)

[English README](./README.md)

**MinerU Open API SDK** 是一个完全免费、零依赖的 Go 语言库，用于连接 [MinerU](https://mineru.net) 文档提取服务。只需一次调用，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

---

## 🚀 核心特性

- **完全免费**：文档提取服务没有任何隐藏费用。
- **零依赖**：仅使用 Go 标准库，不引入任何外部依赖。
- **极速模式 (No Auth)**：无需 API Token 即可立即提取。
- **全功能模式**：提供完整的版式保留、图片、表格及公式支持。
- **并发支持**：原生支持 Go Channel，高效处理批量文档。

---

## 📦 安装指南

```bash
go get github.com/opendatalab/MinerU-Ecosystem/sdk/go@latest
```

---

## 🛠️ 快速上手

### 1. 极速模式 (Flash Extract - 免登录，Markdown 唯一)
适合快速预览。无需配置 Token。
```go
import "github.com/opendatalab/MinerU-Ecosystem/sdk/go"

// 极速模式无需传入 Token
client := mineru.NewFlash()
result, _ := client.FlashExtract(ctx, "https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

fmt.Println(result.Markdown)
```

### 2. 全功能模式 (Full Feature Extract - 需登录)
支持超大文件、丰富的资产（图片/表格）及多种输出格式。
```go
import "github.com/opendatalab/MinerU-Ecosystem/sdk/go"

// 从 https://mineru.net 获取免费 Token
client, _ := mineru.New("your-api-token")
result, _ := client.Extract(ctx, "https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

fmt.Println(result.Markdown)
fmt.Println(len(result.Images)) // 获取提取出的图片数量
```

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

## 📖 详细用法

### 全功能提取选项
```go
result, _ := client.Extract(ctx, "./论文.pdf",
    mineru.WithModel("vlm"),             // "vlm" | "pipeline" | "html"
    mineru.WithOCR(true),                // 启用 OCR 识别扫描件
    mineru.WithFormula(true),            // 公式识别
    mineru.WithTable(true),              // 表格识别
    mineru.WithLanguage("en"),           // "ch" | "en" | 等
    mineru.WithPages("1-20"),            // 页码范围
    mineru.WithExtraFormats("docx"),     // 额外导出为 docx, html, 或 latex
    mineru.WithPollTimeout(10*time.Minute),
)

result.SaveAll("./output/") // 保存 Markdown 和所有相关资源
```

### 批量处理
```go
// 返回一个 Channel，边处理边返回结果
ch, _ := client.ExtractBatch(ctx, []string{"a.pdf", "b.pdf"})
for result := range ch {
    fmt.Printf("%s: 已完成\n", result.Filename)
}
```

### 网页爬取 (Crawl)
```go
result, _ := client.Crawl(ctx, "https://www.baidu.com")
fmt.Println(result.Markdown)
```

---

## 🤖 AI Agent 自动化集成

非常适合基于 Go 的 AI 后端服务集成。您可以通过 `result.State` 和 `result.Progress` 轻松监控任务状态。

```go
taskID, _ := client.Submit(ctx, "报告.pdf")
// ... 稍后 ...
result, _ := client.GetTask(ctx, taskID)
if result.State == "done" {
    processMarkdown(result.Markdown)
}
```

---

## 📄 开源协议
本项目采用 MIT 协议。

## 🔗 相关链接
- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/docs)
