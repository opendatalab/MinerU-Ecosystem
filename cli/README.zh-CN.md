# MinerU Open API 命令行工具 (CLI)

[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/cli/blob/main/LICENSE)

**MinerU Open API CLI** 是一个零依赖的命令行工具，用于文档解析和网页抓取。

适合以下场景：

- 需要干净 `stdout` 输出的 AI Agent
- CI/CD 和自动化脚本
- 需要将文档解析能力集成到自身工作流中的开发者和团队

---

## 🚀 核心特性

- **零依赖**：单二进制文件，无需 Python/Node.js 运行时
- **Agent 友好**：严格分离 `stdout` / `stderr`，便于管道和自动化集成
- **免登录解析**：使用 `flash-extract` 即可获得结果，无需 API Token
- **全功能模式**：使用 `extract` 和 `crawl` 搭配 Token，获得更丰富的输出和更完整的能力
- **批量输入**：支持位置参数、`--list` 和 `--stdin-list`
- **支持标准输入文件流**：可通过 `extract --stdin` 从管道读取文件字节

---

## 📦 安装指南

### Windows (PowerShell)

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

### Linux / macOS (Shell)

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

---

## 🧭 命令总览

| 命令 | 是否需要鉴权 | 用途 |
|---|---|---|
| `flash-extract` | 否 | 极速文档解析，仅输出 Markdown |
| `extract` | 是 | 全功能文档解析 |
| `crawl` | 是 | 网页抓取与解析 |
| `auth` | 可选 | 保存、查看、校验 Token 配置 |
| `status` | 是 | 按 task ID 查询任务状态 |
| `set-source` | 否 | 持久化请求来源标识 |
| `update` | 否 | 检查或安装最新 CLI 版本 |
| `version` | 否 | 输出版本与构建信息 |

### `flash-extract` 与 `extract` 对比

| | `flash-extract` | `extract` |
|---|---|---|
| **鉴权** | 无需 Token | 需要 Token |
| **支持格式** | PDF, 图片 (png, jpg, webp 等), Docx, PPTx, Excel (xls, xlsx) | PDF, 图片 (png, jpg 等), Doc, Docx, Ppt, Pptx, Html |
| **文件大小** | 最大 10 MB | 最大 200 MB |
| **页数限制** | 最大 20 页 | 最大 600 页 |
| **输出内容** | 仅 Markdown（图片/表格/公式以占位符替代） | Markdown, HTML, LaTeX, Docx, JSON |
| **批量处理** | 一次一个文件 | 支持多文件和 URL |

---

## ⚙️ 全局配置

### Token 查找顺序

CLI 按以下顺序解析 API Token：

1. `--token`
2. `MINERU_TOKEN`
3. `~/.mineru/config.yaml`

可以通过 `mineru-open-api auth` 将 Token 保存到 `~/.mineru/config.yaml`。

### Source 查找顺序

请求来源标识按以下顺序解析：

1. `MINERU_SOURCE`
2. `~/.mineru/config.yaml` 中的 `source`
3. 默认值：`open-api-cli`

可以通过 `mineru-open-api set-source <value>` 持久化设置。

### 全局参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--token` | 未设置 | 仅对当前命令覆盖 env/config 中的 Token |
| `--base-url` | 公共 API 默认地址 | 私有部署时覆盖 API 基地址 |
| `-v`, `--verbose` | `false` | 打印 HTTP 请求/响应调试日志 |

---

## 🧱 输入与输出行为

### 输入来源

- `extract` 支持本地文件和 URL
- `flash-extract` 支持单个本地文件或 URL
- `crawl` 支持一个或多个 URL
- `extract --stdin` 从 `stdin` 读取原始文件字节流
- `extract --list <file>` 与 `crawl --list <file>` 从文件逐行读取输入
- `extract --stdin-list` 与 `crawl --stdin-list` 从 `stdin` 逐行读取输入

### 输出流约定

- 未指定 `-o/--output` 时，解析结果输出到 `stdout`
- 状态、进度、报错输出到 `stderr`

这意味着你可以安全地做管道串联：

```bash
mineru-open-api extract report.pdf | some-llm-tool
```

### Stdout 规则

未指定 `-o` 时：

- 只能处理 **一个** 输入
- 只能输出 **一种** 格式
- `docx` 这类二进制格式不能输出到 `stdout`

批量模式必须配合 `-o` 输出到目录。

---

## ⚡ `flash-extract`

适用于快速预览和 Agent 场景的免登录解析命令。

### 行为说明

- 无需 Token
- 一次只处理一个输入
- 仅输出 Markdown
- 支持本地文件或 URL
- 更适合小文件和较短文档

### 默认值

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--language` | `ch` | 只有改动时才会显式传给 API |
| `--pages` | 未设置 | 默认处理 API 允许的完整页范围 |
| `--timeout` | `300` 秒 | 轮询等待总时长 |
| `-o`, `--output` | 未设置 | 输出 Markdown 到 `stdout` |

### 参数说明

| 参数 | 说明 |
|---|---|
| `-o`, `--output` | 输出文件或目录；省略时输出到 `stdout` |
| `--language` | 文档语言 |
| `--pages` | 页码范围，例如 `1-10` |
| `--timeout` | 轮询超时时间，单位秒 |

### 示例

```bash
# 输出 Markdown 到 stdout
mineru-open-api flash-extract 报告.pdf

# 解析 URL
mineru-open-api flash-extract https://cdn-mineru.openxlab.org.cn/demo/example.pdf

# 保存到文件或目录
mineru-open-api flash-extract 报告.pdf -o ./out/

# 指定语言与页码范围
mineru-open-api flash-extract 报告.pdf --language en --pages 1-5
```

---

## 📄 `extract`

全功能文档解析命令，需要 Token。

### 行为说明

- 支持单文件、单 URL、多输入、`--list`、`--stdin`
- 默认输出 Markdown
- 支持 HTML、LaTeX、DOCX 等额外导出格式
- 单输入场景下，`-o` 可以是文件路径或目录
- 批量场景下，`-o` 必须是目录

### 默认值

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-f`, `--format` | `md` | 逗号分隔的输出格式 |
| `--model` | 自动推断 | HTML 文件/URL 走 `html`；其余默认 `vlm` |
| `--ocr` | `false` | OCR 默认关闭 |
| `--formula` | `true` | 启用/禁用公式识别 |
| `--table` | `true` | 启用/禁用表格识别 |
| `-l`, `--language` | `ch` | 只有改动时才会显式传给 API |
| `--pages` | 未设置 | 默认处理完整文档 |
| `--timeout` | 单文件 `300` / 批量 `1800` 秒 | 轮询等待总时长 |
| `--stdin` | `false` | 从 `stdin` 读取文件字节流 |
| `--stdin-name` | `stdin.pdf` | `--stdin` 模式下使用的虚拟文件名 |
| `--list` | 未设置 | 从文件逐行读取输入 |
| `--stdin-list` | `false` | 从 `stdin` 逐行读取输入 |
| `--concurrency` | `0` | 参数已存在；当前 CLI 版本尚未实际使用 |

### 格式支持

| 格式 | 可输出到 stdout | 配合 `-o` 保存 |
|---|---|---|
| `md` | 是 | 是 |
| `json` | 是 | 否 |
| `html` | 是 | 是 |
| `latex` | 是 | 是 |
| `docx` | 否 | 是 |

### 参数说明

| 参数 | 说明 |
|---|---|
| `-o`, `--output` | 输出文件或目录；省略时输出到 `stdout` |
| `-f`, `--format` | `md,json,html,latex,docx` |
| `--model` | `vlm`、`pipeline` 或 `html` |
| `--ocr` | 启用 OCR |
| `--formula=false` | 关闭公式识别 |
| `--table=false` | 关闭表格识别 |
| `-l`, `--language` | 文档语言 |
| `--pages` | 页码范围，例如 `1-10,15` |
| `--timeout` | 轮询超时时间，单位秒 |
| `--list` | 从文件读取输入 |
| `--stdin-list` | 从 `stdin` 读取输入列表 |
| `--stdin` | 从 `stdin` 读取原始文件字节流 |
| `--stdin-name` | 与 `--stdin` 搭配使用的文件名 |
| `--concurrency` | 预留的批量并发参数 |

### 示例

```bash
# 先配置 Token
mineru-open-api auth

# 输出 Markdown 到 stdout
mineru-open-api extract 论文.pdf

# 输出 HTML 到 stdout
mineru-open-api extract 论文.pdf -f html

# 同时保存 markdown 和 docx
mineru-open-api extract 论文.pdf -f md,docx -o ./results/

# 处理远程 URL
mineru-open-api extract https://example.com/file.pdf

# 从列表文件批量处理
mineru-open-api extract --list files.txt -o ./results/

# 通过 stdin 传入文件字节
cat report.pdf | mineru-open-api extract --stdin --stdin-name report.pdf
```

---

## 🌐 `crawl`

全功能网页抓取命令，需要 Token。

### 行为说明

- 支持一个或多个公开 URL
- 内部固定使用 HTML 抓取模型
- 支持将 Markdown、JSON、HTML 输出到 `stdout`
- 指定 `-o` 时，结果始终写入目录

### 默认值

| 参数 | 默认值 | 说明 |
|---|---|---|
| `-f`, `--format` | `md` | 逗号分隔的输出格式 |
| `--timeout` | 单 URL `300` / 批量 `1800` 秒 | 轮询等待总时长 |
| `--list` | 未设置 | 从文件读取 URL 列表 |
| `--stdin-list` | `false` | 从 `stdin` 读取 URL 列表 |
| `--concurrency` | `0` | 参数已存在；当前 CLI 版本尚未实际使用 |

### 格式支持

| 格式 | 可输出到 stdout | 配合 `-o` 保存 |
|---|---|---|
| `md` | 是 | 是 |
| `json` | 是 | 否 |
| `html` | 是 | 是 |

### 参数说明

| 参数 | 说明 |
|---|---|
| `-o`, `--output` | 输出目录；省略时输出到 `stdout` |
| `-f`, `--format` | `md,json,html` |
| `--timeout` | 轮询超时时间，单位秒 |
| `--list` | 从文件读取 URL |
| `--stdin-list` | 从 `stdin` 读取 URL |
| `--concurrency` | 预留的批量并发参数 |

### 示例

```bash
# 输出 Markdown
mineru-open-api crawl https://mineru.net

# 输出 HTML
mineru-open-api crawl https://mineru.net -f html

# 批量抓取到目录
mineru-open-api crawl https://mineru.net https://example.com -o ./pages/

# 从文件读取 URL 列表
mineru-open-api crawl --list urls.txt -o ./pages/
```

---

## 🔐 `auth`

用于管理需要鉴权命令的 Token 配置。

### 示例

```bash
# 交互式配置
mineru-open-api auth

# 查看已配置 Token 的来源和脱敏值
mineru-open-api auth --show

# 本地校验 Token 格式
mineru-open-api auth --verify
```

---

## 🧰 其他命令

### `status`

按 **task ID** 查询任务状态，并可选择等待完成。

```bash
mineru-open-api status <task-id>
mineru-open-api status <task-id> --wait
mineru-open-api status <task-id> --wait -o ./out/
```

### `set-source`

持久化设置请求来源标识。

```bash
mineru-open-api set-source my-agent
mineru-open-api set-source --show
mineru-open-api set-source --reset
```

### `update`

```bash
mineru-open-api update
mineru-open-api update --check
```

### `version`

```bash
mineru-open-api version
```

---

## 🤖 典型场景

### 将 Markdown 直接喂给后续工具

```bash
export MINERU_TOKEN="your_token_here"
mineru-open-api extract paper.pdf | some-llm-tool
```

### 批量输出到目录

```bash
mineru-open-api extract *.pdf -o ./results/
```

### 不想管理 Token 时使用 flash 模式

```bash
mineru-open-api flash-extract quick-preview.pdf
```

### 在 Shell 流水线中通过 stdin 传文件

```bash
curl -L https://example.com/report.pdf | mineru-open-api extract --stdin --stdin-name report.pdf
```

---

## 📄 开源协议

本项目采用 Apache-2.0 开源协议。

---

## 🔗 相关链接

- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/docs)
