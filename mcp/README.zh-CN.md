[英文文档](./README.md)

# MinerU Open MCP

[![MinerU-Ecosystem MCP server](https://glama.ai/mcp/servers/opendatalab/MinerU-Ecosystem/badges/card.svg)](https://glama.ai/mcp/servers/opendatalab/MinerU-Ecosystem)

MinerU 官方 MCP 服务器，将 [MinerU](https://mineru.net) 的文档解析能力以 MCP 工具形式对外提供。连接任何 MCP 兼容的 AI 客户端，即可将 PDF、Word 文档、PowerPoint 演示文稿、图片转换为 Markdown。

**无需 API 密钥** — Flash 模式开箱即用，免费无需注册, 但文件上限有限制。设置 `MINERU_API_TOKEN` 可解锁更高限制和更多输出格式。

**带沙箱的 MCP 客户端说明**：部分 MCP 客户端会将拖入输入框的文件沙箱化到临时目录。若需上传并解析本地文件，请在提示中写明目标文件的完整路径，以免服务器无法找到文件。

---

## ⚡ 最快启动方式 — uvx（无需安装）

`mineru-open-mcp` 已发布在 PyPI 上。只要安装了 `uv`，即可直接运行，无需额外安装步骤。

### 配置 MCP 客户端

#### stdio — Claude Desktop、Cursor、Windsurf

MCP 客户端会自动以子进程方式启动 `mineru-open-mcp`。

**使用 `uvx`（推荐 — 始终运行最新版本）：**

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

> **没有 API 密钥？** 服务器将以 Flash 模式运行 — 免费，仅输出 Markdown, 了解详情 [Flash Mode Docs](https://mineru.net/apiManage/docs)


> **`mineru-open-mcp` 不在 PATH 中？** 请使用完整路径：`"/Users/you/.local/bin/mineru-open-mcp"`，或使用上述 `uvx` 方式（会自动处理路径问题）。

## 使用示例

### 示例 1：解析本地 PDF 文档并指定页面范围

**用户提示：** "将这个 PDF 的第 3–5 页解析为 Markdown：\<your_path_to_file\>"

**执行过程：**

- MinerU 上传并解析该 PDF
- 返回整洁的 Markdown，表格（HTML）和公式（LaTeX）均完整保留
- 若内容长度允许，在对话中直接返回 Markdown 文本，同时附上输出路径和 zip 下载链接
- Claude 对内容进行摘要

### 示例 2：解析远程 URL 托管的文件

**用户提示：** "提取这篇论文的内容：https://arxiv.org/pdf/2509.22186"

**执行过程：**

- MinerU 解析该论文为markdown
- Claude 格式化并解释表格内容

### 示例 3：解析多个本地 PDF 文件并分别指定页面范围

**用户提示：** "将 \<file1\> 第 1–5 页、\<file2\> 第 2–9 页、\<file3\> 第 3 页解析为 Markdown"

**执行过程：**

- MinerU 分别上传并解析各文件
- 返回目标格式的输出结果、供下载的 zip 链接、Markdown 摘要，以及您指定的输出目录
- Claude 基于内容进行进一步分析

### 示例 4：高级自定义参数

**用户提示 1：** "使用 pipeline 模型解析这个韩语文件：your_path_here"

**用户提示 2：** "解析 your_path_here，并将 Markdown 保存到 your_output_dir"

**执行过程：**

- Pipeline 模型是 MinerU 服务提供的另一种解析模型（默认使用 vlm 模型）
- 您可以通过提示语指定模型、OCR 语言，甚至独立于 `OUTPUT_DIR` 的输出目录
- 您的请求会被参数化传入 `parse_documents` 工具，由 MinerU 完成后续处理

#### streamable-http — 基于 Web 的 MCP 客户端

手动启动服务器，然后将客户端指向它：

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

## 功能特性

- **`parse_documents`** — 将本地文件和/或远程 URL 转换为 Markdown；支持PDF、图片（png/jpg/jpeg/jp2/webp/gif/bmp）、Doc、Docx、Ppt、PPTx。Flash 模式还支持 xlsx。
- **`get_ocr_languages`** — 列出 MinerU 支持的所有 OCR 语言
- **Flash 模式** — 无需 API 密钥即可使用（免费，仅输出 Markdown，支持 PDF/图片/Docx/PPTx/xls/xlsx）；如需完整功能，请提供 `MINERU_API_TOKEN`，将自动退出 Flash 模式。
- **输出行为** — 单文件解析默认以内联 Markdown 形式返回；批量解析将结果保存至磁盘并返回文件元数据。超大内联内容也会自动保存至本地，并通过 `extract_path` 返回路径。
- **两种传输模式** — `stdio`、`streamable-http`

---

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `MINERU_API_TOKEN` | MinerU API 令牌，在 [MinerU](https://mineru.net) 申请以解锁完整能力。未提供时启用 Flash 模式。 | — |
| `OUTPUT_DIR` | 解析结果需要保存至本地时使用的目录，例如批量解析或超大内联内容 | `~/mineru-downloads` |

## 隐私政策

`mineru-open-mcp` 通过连接 MinerU 官方 API（mineru.net）来解析文档。

- **发送的数据**：您提供用于解析的文档内容（文件或 URL）
- **数据存储**：解析结果由 MinerU 服务器临时缓存，不用于模型训练
- **第三方**：MinerU API（mineru.net）— 详见 [MinerU 隐私政策](https://webpub.shlab.tech/dps/opendatalab-web/odl_v5.1690/privacy.html)
- **本地数据**：解析结果将保存至目标输出目录。日志文件（仅在 `ENABLE_LOG=true` 时）保存至 `MINERU_LOG_DIR`
- **联系方式**：OpenDataLab@pjlab.org.cn（或在 [MinerU-Ecosystem](https://github.com/opendatalab/MinerU-Ecosystem) 提交 issue）
