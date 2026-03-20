[英文文档](./README.md)
# MinerU Open MCP

MinerU 官方 MCP 服务器，将 [MinerU](https://mineru.net) 的文档解析能力以 MCP 工具形式对外提供。连接任何 MCP 兼容的 AI 客户端，即可将 PDF、Word 文档、PowerPoint 演示文稿、电子表格和图片转换为 Markdown、Word (docx)、HTML 或 LaTeX。

**无需 API 密钥** — Flash 模式开箱即用，免费无需注册，支持 20 页 / 10 MB 以内的文件。设置 `MINERU_API_TOKEN` 可解锁更高限制和更多输出格式。

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

> **没有 API 密钥？** 服务器将以 Flash 模式运行 — 免费，仅输出 Markdown，单文件限制 20 页 / 10 MB（支持 PDF、图片、Docx、PPTx、xls、xlsx）。

> **`mineru-open-mcp` 不在 PATH 中？** 请使用完整路径：`"/Users/you/.local/bin/mineru-open-mcp"`，或使用上述 `uvx` 方式（会自动处理路径问题）。

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

- **`parse_documents`** — 将本地文件和/或远程 URL 转换为 Markdown；支持 PDF、DOCX、PPTX、JPG、PNG、HTML；可选额外输出格式（Word、HTML、LaTeX）。Flash 模式还支持 xls、xlsx。
- **`get_ocr_languages`** — 列出 MinerU 支持的所有 OCR 语言
- **`clean_logs`** — 删除旧的服务器日志文件（仅在 `ENABLE_LOG=true` 时可用）
- **Flash 模式** — 无需 API 密钥即可使用（免费，仅输出 Markdown，单文件限制 20 页 / 10 MB，支持 PDF/图片/Docx/PPTx/xls/xlsx）；如需完整功能，请提供 `MINERU_API_TOKEN`，将自动退出 Flash 模式。
- **三种传输模式** — `stdio`、`sse`、`streamable-http`

---

## 从源码运行（开发模式）

```bash
git clone <repository-url>
cd mineru-mcp-server

uv pip install -e .

# stdio 模式
uv run mineru-open-mcp

# streamable-http 模式
uv run mineru-open-mcp --transport streamable-http --port 8001
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `MINERU_API_TOKEN` | MinerU 云端 API 令牌 | — |
| `OUTPUT_DIR` | Markdown（及其他格式）输出文件的保存目录 | `~/mineru-downloads` |
| `ENABLE_LOG` | 设置为 `true` 以写入带时间戳的日志文件 | 禁用 |
| `MINERU_LOG_DIR` | 自定义日志文件目录 | 工作区 `logs/` 或 `~/.mineru-open-mcp/logs/` |

**日志文件位置：** 当 `ENABLE_LOG=true` 时，日志将写入 `~/.mineru-open-mcp/logs/log_<timestamp>.txt`（安装模式）或工作区根目录的 `logs/`（源码运行模式）。可通过 `MINERU_LOG_DIR` 覆盖：

```json
{
  "mcpServers": {
    "mineru": {
      "command": "mineru-open-mcp",
      "env": {
        "MINERU_API_TOKEN": "your_key_here",
        "ENABLE_LOG": "true",
        "MINERU_LOG_DIR": "/Users/you/mineru-logs"
      }
    }
  }
}
```
