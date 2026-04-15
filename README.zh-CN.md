<div align="center">

# MinerU-Ecosystem

**[MinerU](https://github.com/opendatalab/MinerU) Open API 官方生态工具集**

为开发者和 AI 智能体提供无缝的文档解析能力 — PDF · Word · PPT · 图片 · 网页 → Markdown / JSON · VLM+OCR 双引擎 · 109 种语言 · MCP Server · LangChain / RAGFlow / Dify / FastGPT 原生集成。

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![MinerU](https://img.shields.io/badge/Powered%20by-MinerU-orange)](https://github.com/opendatalab/MinerU)
[![Online](https://img.shields.io/badge/Online-mineru.net-purple)](https://mineru.net)

[English Document](README.md)

</div>

---

## 📖 项目简介

**MinerU-Ecosystem** 提供基于 [MinerU Open API](https://mineru.net/apiManage/docs) 构建的完整工具套件、SDK 和集成方案。无论你是构建生产级文档处理流水线、集成 LangChain 实现 RAG，还是让 AI 智能体实时解析文档——本仓库都能满足需求。

[MinerU](https://github.com/opendatalab/MinerU) 是一款开源高精度文档解析引擎，将非结构化文档（PDF、图片、Office 文件等）转换为机器可读的 Markdown 和 JSON，专为 LLM 预训练、RAG 和 Agent 工作流场景设计。

当前整体效果仍在持续改进中。如果你遇到效果不理想、输出质量不稳定或明显的版式异常，欢迎提交 issue 或附带样例文件 / 截图反馈。

**核心解析能力：**
- 公式 → LaTeX · 表格 → HTML，精准还原复杂版面
- 支持扫描件、手写体、多栏布局、跨页表格合并
- 输出符合人类阅读顺序，自动去除页眉页脚
- VLM + OCR 双引擎，支持 109 种语言识别

---

## 🏗️ 仓库结构

```
MinerU-Ecosystem/
├── cli/                  # 命令行工具
├── sdk/                  # 多语言 SDK
│   ├── python/           #   Python SDK
│   ├── go/               #   Go SDK
│   └── typescript/       #   TypeScript SDK
├── langchain_mineru/     # LangChain 文档加载器集成
├── llama-index-readers-mineru/     # LlamaIndex 文档解析器集成
├── mcp/                  # Model Context Protocol 服务器（Python）
└── skills/               # AI 智能体技能（Claude Code、OpenClaw 等）
```

---

## 🔑 支持的 API 模式

本仓库所有组件均适配两种 API 模式：

| 对比维度       | 🎯 精准解析 API                                     | ⚡ Agent 轻量解析 API  |
| -------------- | --------------------------------------------------- | ---------------------- |
| 是否需要 Token | ✅ 需要                                             | ❌ 无需（IP 限频）     |
| 模型版本       | `pipeline`（默认）/ `vlm`（推荐）/ `MinerU-HTML`    | 固定 pipeline 轻量模型 |
| 文件大小限制   | ≤ 200MB                                             | ≤ 10MB                 |
| 页数限制       | ≤ 200 页                                            | ≤ 20 页                |
| 批量支持       | ✅ 支持（≤ 200 个）                                 | ❌ 单文件              |
| 输出格式       | Markdown、JSON、Zip，且可导出为 DOCX / HTML / LaTeX | 仅 Markdown            |

## 🧭 按使用场景选择接入方式

不确定该从哪里开始时，先按你的目标选择路径：

```text
我想要……
│
├── 🌐 立即体验，不安装也不写代码
│   └── Web App → https://mineru.net/OpenSourceTools/Extractor
│
├── 💻 在终端里直接解析文档
│   └── CLI → cli/
│       flash-extract：免 Token，适合快速预览
│       extract：功能完整，适合生产处理
│
├── 🐍 集成到 Python / Go / TypeScript 项目
│   └── SDK → sdk/python/ | sdk/go/ | sdk/typescript/
│
├── 🤖 让 AI Agent 具备文档解析能力
│   ├── 直接调用命令行工具 → cli/
│   ├── 自然语言技能接入（OpenClaw、ZeroClaw 等）→ skills/
│   └── 标准 MCP 协议接入（Cursor、Claude Desktop、Windsurf 等）→ mcp/
│
├── 📚 搭建 RAG / 知识库
│   ├── LangChain Loader → langchain_mineru/
│   └── LlamaIndex Reader → llama-index-readers-mineru/
│       flash 模式：零 Token，快速起步
│       precision 模式：支持 OCR、表格、公式等更完整能力
```

如果你只是想先验证效果，优先从 Web App 或 `flash` 模式开始；如果你已经进入正式集成阶段，需要更高精度、OCR、表格和公式识别，优先选择 `precision` 模式。

## 🚀 快速开始

### 💻 CLI 命令行工具

#### 安装

```bash
# Linux / macOS
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

```powershell
# Windows (PowerShell)
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

**Agent 轻量解析（免登录）**

```bash
mineru-open-api flash-extract 报告.pdf
```

**精准解析（需登录）**

```bash
# 首次配置 Token
mineru-open-api auth

# 提取并输出到终端
mineru-open-api extract 论文.pdf

# 保存所有资源（图片/表格）到目录
mineru-open-api extract 报告.pdf -o ./output/

# 导出为多种格式
mineru-open-api extract report.pdf -f docx,latex,html -o ./results/
```

**网页爬取**

```bash
mineru-open-api crawl https://www.example.com
```

**批量处理**

```bash
# 批量处理当前目录所有 PDF
mineru-open-api extract *.pdf -o ./results/

# 通过文件列表批量处理
mineru-open-api extract --list 文件列表.txt -o ./results/
```

---

### 🐍 Python SDK

#### 安装

```bash
pip install mineru-open-sdk
```

**Agent 轻量解析（免 Token）**

```python
from mineru import MinerU

client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
print(result.markdown)
```

**精准解析（需 Token）**

```python
from mineru import MinerU

# 从 https://mineru.net 获取免费 Token
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
print(result.markdown)
print(result.images)  # 提取的图片列表
```

---

### 🐹 Go SDK

#### 安装

```bash
go get github.com/opendatalab/MinerU-Ecosystem/sdk/go@latest
```

**轻量解析**

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

**精准解析（带选项）**

```go
result, err := client.Extract(ctx, "./paper.pdf",
    mineru.WithModel("vlm"),
    mineru.WithLanguage("ch"),
    mineru.WithPages("1-20"),
    mineru.WithExtraFormats("docx"),
    mineru.WithPollTimeout(10*time.Minute),
)
if err != nil {
    panic(err)
}
result.SaveAll("./output")
```

**批量处理**

```go
ch, err := client.ExtractBatch(ctx, []string{"a.pdf", "b.pdf"})
if err != nil {
    panic(err)
}
for result := range ch {
    fmt.Printf("%s: %s\n", result.Filename, result.State)
}
```

---

### 🟦 TypeScript / JavaScript SDK

#### 安装

```bash
npm install mineru-open-sdk
```

**轻量解析**

```typescript
import { MinerU } from "mineru-open-sdk";

const client = new MinerU();
const result = await client.flashExtract(
  "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
);
console.log(result.markdown);
```

**精准解析（带完整选项）**

```typescript
import { MinerU, saveAll } from "mineru-open-sdk";

const client = new MinerU("your-api-token");
const result = await client.extract("./paper.pdf", {
  model: "vlm",        // "vlm" | "pipeline" | "html"
  language: "ch",
  pages: "1-20",
  extraFormats: ["docx"],
  timeout: 600,
});
await saveAll(result, "./output");
```

**批量处理**

```typescript
for await (const result of client.extractBatch(["a.pdf", "b.pdf"])) {
  console.log(`${result.filename}: ${result.state}`);
}
```

---

## 🤖 MCP 服务器（接入 Claude / Cursor）

MinerU 提供官方 MCP Server，让 Claude Desktop、Cursor、Windsurf 等任意 MCP 兼容客户端直接调用文档解析能力。

> 无需 API Key — Flash 模式开箱即用，免费，每次最多 20 页 / 10 MB。

**配置方式（`claude_desktop_config.json` / `.cursor/mcp.json`）**

```json
{
  "mcpServers": {
    "mineru": {
      "command": "uvx",
      "args": ["mineru-open-mcp"],
      "env": {
        "MINERU_API_TOKEN": "your_key_here"
      }
    }
  }
}
```

**Streamable HTTP 模式（Web 端 MCP 客户端）**

```bash
MINERU_API_TOKEN=your_key mineru-open-mcp --transport streamable-http --port 8001
```

```json
{
  "mcpServers": {
    "mineru": {
      "type": "streamableHttp",
      "url": "http://127.0.0.1:8001/mcp"
    }
  }
}
```

**暴露的 MCP 工具：**

| 工具 | 说明 |
|---|---|
| `parse_documents` | 将 PDF、DOCX、PPTX、图片、HTML 转为 Markdown |
| `get_ocr_languages` | 列出全部 109 种支持的 OCR 语言 |
| `clean_logs` | 清理旧日志文件（需开启 `ENABLE_LOG=true`）|

**环境变量：**

| 变量 | 说明 | 默认值 |
|---|---|---|
| `MINERU_API_TOKEN` | MinerU 云端 API Token | — |
| `OUTPUT_DIR` | 输出文件保存目录 | `~/mineru-downloads` |
| `ENABLE_LOG` | 设为 `true` 时写入日志文件 | 禁用 |
| `MINERU_LOG_DIR` | 日志目录自定义路径 | `~/.mineru-open-mcp/logs/` |

---

## 🦜 LangChain RAG 集成

`langchain-mineru` 是官方 LangChain 文档加载器，一行代码将任意文档转为 LangChain `Document` 对象，直接接入 RAG 流水线。

#### 安装

```bash
pip install langchain-mineru
```

**最简示例（无需 Token）**

**1. 基础用法（默认 `flash` 模式，无需 Token）**

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="demo.pdf")   # 默认 flash 模式，无需 Token
docs = loader.load()
print(docs[0].page_content[:500])
print(docs[0].metadata)
```

默认使用 `mode="flash"`，适合快速预览和轻量解析。

**2. Precision 模式（需 Token）**

适合长文档、大文件，以及对解析保真度或标准 API 输出要求更高的场景。Flash 模式也支持 OCR、公式、表格开关，但仍受 flash API 自身限制。

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/manual.pdf",
    mode="precision",
    token="your-api-token",  # 或设置 MINERU_TOKEN 环境变量
    split_pages=True,
    pages="1-5",
)

docs = loader.load()
for doc in docs:
    print(doc.metadata.get("page"), doc.page_content[:200])
```

**3. 接入 LangChain RAG 流水线**

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(source="demo.pdf", split_pages=True)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("这个文档的核心结论是什么？", k=3)
for r in results:
    print(r.page_content[:200])
```

默认使用 `mode="flash"`（无需 API Token）；切换到 `mode="precision"` 可获得更高精度的解析结果（需要 Token 认证）。如果用于 RAG，建议对 PDF 开启 `split_pages=True`，这样可以得到更细粒度的页级 `Document`。

### LlamaIndex RAG 集成 

一个面向 LlamaIndex 的文档读取器，可将 PDF、Word、PPT、图片、Excel 等文件通过 MinerU 解析为 LlamaIndex 兼容的 `Document` 对象，便于直接接入索引与检索流程。

#### 安装

```bash
pip install llama-index-readers-mineru
```

#### 使用

**1. Flash 模式（默认，无需 Token）**

适合快速接入和轻量解析，返回 Markdown 结果。

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader()
documents = reader.load_data("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(documents[0].text[:500])
print(documents[0].metadata)
```

**2. Precision 模式（需 Token）**

适合长文档、大文件，以及对解析保真度或标准 API 输出要求更高的场景。Flash 模式也支持 OCR、公式和表格开关，但仍受 flash API 自身限制。

```python
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(
    mode="precision",
    token="your-api-token",  # 或设置 MINERU_TOKEN 环境变量
    pages="1-20",
)
documents = reader.load_data("/path/to/paper.pdf")
```

**3. 直接接入 LlamaIndex 索引**

```python
from llama_index.core import VectorStoreIndex
from llama_index.readers.mineru import MinerUReader

reader = MinerUReader(split_pages=True)
documents = reader.load_data("/path/to/paper.pdf")

index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("总结这篇文档的核心结论")
print(response)
```

默认使用 `mode="flash"`，无需 Token；切换为 `mode="precision"` 后需要先在 `https://mineru.net` 申请 Token。若用于 RAG，建议开启 `split_pages=True` 获取更细粒度的页级 `Document`。

---

## 🤖 AI 智能体技能

预构建的智能体技能，封装 `mineru-open-api` CLI，可直接在 Agent 工作流中使用。

- **[OpenClaw / ClawHub](https://clawhub.ai/MinerU-Extract/mineru-ai)** — 查看技能详情
- **[一键下载](https://cdn-mineru.openxlab.org.cn/open-api-cli/skill.zip)** — 技能资源包
- 兼容 Claude Code、OpenClaw、ZeroClaw 等支持技能接口的 AI 智能体

---

## 🔗 全部集成

| 框架 / 工具 | 状态 | 说明 |
|---|---|---|
| LangChain | ✅ 官方 | `pip install langchain-mineru` |
| LlamaIndex | ✅ 社区 | 见 MinerU-Ecosystem |
| RAGFlow | ✅ 支持 | 文档加载器集成 |
| RAG-Anything | ✅ 支持 | 多模态 RAG 流水线 |
| Flowise | ✅ 支持 | 可视化 RAG 构建器 |
| Dify | ✅ 原生插件 | 内置文档加载器 |
| FastGPT | ✅ 原生插件 | 接入文档 |
| Claude Desktop | ✅ MCP | `uvx mineru-open-mcp` |
| Cursor | ✅ MCP | `.cursor/mcp.json` 配置 |
| Windsurf | ✅ MCP | stdio / streamable-http |
| OpenClaw / ZeroClaw | ✅ Agent 技能 | ClawHub |
| Go SDK | ✅ 官方 | `go get .../sdk/go@latest` |
| TypeScript SDK | ✅ 官方 | `npm install mineru-open-sdk` |
| Python SDK | ✅ 官方 | `pip install mineru-open-sdk` |

---

## 📚 相关文档

| 资源                 | 链接                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------ |
| MinerU Open API 文档 | [mineru.net/apiManage/docs](https://mineru.net/apiManage/docs)                       |
| MinerU 在线体验      | [mineru.net/OpenSourceTools/Extractor](https://mineru.net/OpenSourceTools/Extractor) |
| MinerU 开源项目      | [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)               |

---

## 📄 开源许可

本项目基于 [Apache License 2.0](LICENSE) 开源。
