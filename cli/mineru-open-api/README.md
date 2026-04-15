# MinerU Open API CLI

[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)
[![Go Report Card](https://goreportcard.com/badge/github.com/opendatalab/MinerU-Ecosystem/cli)](https://goreportcard.com/report/github.com/opendatalab/MinerU-Ecosystem/cli)

**MinerU Open API CLI** is a zero-dependency command-line tool for document extraction and web crawling.

It is designed for:

- AI agents that need clean `stdout` for downstream tools
- CI/CD jobs and scripts
- developers and teams integrating document extraction into their workflows

---

## 🚀 Key Features

- **Zero dependency**: single binary, no Python/Node.js runtime required
- **Agent Friendly**: clean stdout/stderr separation, easy to pipe and automate
- **No Auth Extract**: use `flash-extract` for instant results without any API token
- **Precision Extraction**: use `extract` and `crawl` with a token for richer outputs and larger workloads
- **Batch input support**: positional args, `--list`, and `--stdin-list`
- **Stdin support for file content**: pipe bytes into `extract --stdin`

---

## 📦 Installation

### Windows (PowerShell)

```powershell
irm https://cdn-mineru.openxlab.org.cn/open-api-cli/install.ps1 | iex
```

### Linux / macOS (Shell)

```bash
curl -fsSL https://cdn-mineru.openxlab.org.cn/open-api-cli/install.sh | sh
```

---

## 🧭 Command Overview

| Command | Auth | Purpose |
|---|---|---|
| `flash-extract` | No | Fast document extraction, Markdown output |
| `extract` | Yes | Precision document extraction |
| `crawl` | Yes | Web page extraction |
| `auth` | Optional | Save, inspect, or verify token configuration |
| `status` | Yes | Query a task status by task ID |
| `set-source` | No | Persist the source header used for request tracking |
| `update` | No | Check for or install the latest CLI version |
| `version` | No | Print build and version info |

### `flash-extract` vs `extract`

| | `flash-extract` | `extract` |
|---|---|---|
| **Auth** | No token required | Token required |
| **File Formats** | PDF, Images (png, jpg, webp, etc.), Docx, PPTx, Excel (xls, xlsx) | PDF, Images (png, jpg, etc.), Doc, Docx, Ppt, Pptx, Html |
| **File Size** | Max 10 MB | Max 200 MB |
| **Page Limit** | Max 20 pages | Max 200 pages |
| **Output** | Markdown (formula & table on by default, OCR off) | Markdown, HTML, LaTeX, Docx, JSON |
| **Batch** | One file at a time | Multiple files and URLs |

---

## ⚙️ Global Configuration

### Token resolution order

The CLI resolves the API token in this order:

1. `--token`
2. `MINERU_TOKEN`
3. `~/.mineru/config.yaml`

Use `mineru-open-api auth` to save a token into `~/.mineru/config.yaml`.

### Source resolution order

The request source identifier is resolved in this order:

1. `MINERU_SOURCE`
2. `~/.mineru/config.yaml` `source`
3. default value: `open-api-cli`

Use `mineru-open-api set-source <value>` to persist it.

### Global flags

| Flag | Default | Description |
|---|---|---|
| `--token` | unset | Override token from env/config for the current command |
| `--base-url` | default public API | Override API base URL for private deployments |
| `-v`, `--verbose` | `false` | Print HTTP request/response debug logs |

---

## 🧱 Input And Output Behavior

### Input sources

- `extract` accepts local files and URLs
- `flash-extract` accepts one local file or one URL
- `crawl` accepts one or more URLs
- `extract --stdin` reads raw file bytes from `stdin`
- `extract --list <file>` and `crawl --list <file>` read one input per line
- `extract --stdin-list` and `crawl --stdin-list` read one input per line from `stdin`

### Output streams

- extracted content is written to `stdout` when `-o/--output` is omitted
- status, progress, and error messages are written to `stderr`

This makes piping safe:

```bash
mineru-open-api extract report.pdf | some-llm-tool
```

### Stdout rules

When `-o` is omitted:

- only **one** input is allowed
- only **one** format is allowed
- binary formats like `docx` cannot be written to `stdout`

For batch mode, you must pass `-o` and save to a directory.

---

## ⚡ `flash-extract`

Fast no-auth extraction for quick previews and agent workflows.

### Behavior

- token not required
- one input at a time
- Markdown output (formula & table on by default, OCR off)
- supports local file or URL input
- intended for smaller files and shorter documents

### Defaults

| Flag | Default | Notes |
|---|---|---|
| `--language` | `ch` | Only sent when changed |
| `--pages` | unset | Full document/page range allowed by API |
| `--ocr` | unset | OCR is off by default; use `--ocr` to enable |
| `--formula` | unset | Formula recognition is on by default; use `--formula=false` to disable |
| `--table` | unset | Table recognition is on by default; use `--table=false` to disable |
| `--timeout` | `300` seconds | Total wait time for polling |
| `-o`, `--output` | unset | Print Markdown to `stdout` |

### Flags

| Flag | Description |
|---|---|
| `-o`, `--output` | Output file or directory; omit for `stdout` |
| `--language` | Document language |
| `--pages` | Page range such as `1-10` |
| `--ocr` | OCR for scanned documents (default off) |
| `--formula` | Formula recognition (default on, use `--formula=false` to disable) |
| `--table` | Table recognition (default on, use `--table=false` to disable) |
| `--timeout` | Poll timeout in seconds |

### Examples

```bash
# Print markdown to stdout
mineru-open-api flash-extract report.pdf

# Extract from URL
mineru-open-api flash-extract https://cdn-mineru.openxlab.org.cn/demo/example.pdf

# Save to file or directory
mineru-open-api flash-extract report.pdf -o ./out/

# Restrict language and pages
mineru-open-api flash-extract report.pdf --language en --pages 1-5
```

---

## 📄 `extract`

Precision document extraction. Requires a token.

### Behavior

- accepts a local file, a URL, multiple inputs, `--list`, or `--stdin`
- default output format is Markdown
- supports extra export formats such as HTML, LaTeX, and DOCX
- when `-o` is provided for a single input, it may be a file path or a directory
- when running in batch mode, `-o` must be a directory

### Defaults

| Flag | Default | Notes |
|---|---|---|
| `-f`, `--format` | `md` | Comma-separated formats |
| `--model` | auto | HTML files/URLs use `html`; everything else defaults to `vlm` |
| `--ocr` | `false` | OCR is opt-in |
| `--formula` | `true` | Enable/disable formula recognition |
| `--table` | `true` | Enable/disable table recognition |
| `-l`, `--language` | `ch` | Only sent when changed |
| `--pages` | unset | Full document |
| `--timeout` | `300` single / `1800` batch | Total wait time for polling |
| `--stdin` | `false` | Read file bytes from `stdin` |
| `--stdin-name` | `stdin.pdf` | Virtual filename used with `--stdin` |
| `--list` | unset | Read sources from file |
| `--stdin-list` | `false` | Read sources from `stdin` |
| `--concurrency` | `0` | Flag is present; current CLI does not apply it yet |

### Formats

| Format | Stdout | Save with `-o` |
|---|---|---|
| `md` | Yes | Yes |
| `json` | Yes | No |
| `html` | Yes | Yes |
| `latex` | Yes | Yes |
| `docx` | No | Yes |

### Flags

| Flag | Description |
|---|---|
| `-o`, `--output` | Output file or directory; omit for `stdout` |
| `-f`, `--format` | `md,json,html,latex,docx` |
| `--model` | `vlm`, `pipeline`, or `html` |
| `--ocr` | Enable OCR for scanned documents |
| `--formula=false` | Disable formula recognition |
| `--table=false` | Disable table recognition |
| `-l`, `--language` | Document language |
| `--pages` | Page range like `1-10,15` |
| `--timeout` | Poll timeout in seconds |
| `--list` | Read sources from a file |
| `--stdin-list` | Read sources from `stdin` |
| `--stdin` | Read raw file bytes from `stdin` |
| `--stdin-name` | Filename used together with `--stdin` |
| `--concurrency` | Reserved batch concurrency flag |

### Examples

```bash
# Authenticate once
mineru-open-api auth

# Print markdown to stdout
mineru-open-api extract report.pdf

# Print HTML to stdout
mineru-open-api extract report.pdf -f html

# Save markdown and docx
mineru-open-api extract report.pdf -f md,docx -o ./results/

# Process a URL
mineru-open-api extract https://example.com/file.pdf

# Process a list file
mineru-open-api extract --list files.txt -o ./results/

# Pipe file bytes through stdin
cat report.pdf | mineru-open-api extract --stdin --stdin-name report.pdf
```

---

## 🌐 `crawl`

Precision web page extraction. Requires a token.

### Behavior

- accepts one or more public URLs
- always uses the HTML crawler model internally
- supports Markdown, JSON, and HTML on `stdout`
- when saving with `-o`, files are written into a directory

### Defaults

| Flag | Default | Notes |
|---|---|---|
| `-f`, `--format` | `md` | Comma-separated formats |
| `--timeout` | `300` single / `1800` batch | Total wait time for polling |
| `--list` | unset | Read URLs from file |
| `--stdin-list` | `false` | Read URLs from `stdin` |
| `--concurrency` | `0` | Flag is present; current CLI does not apply it yet |

### Formats

| Format | Stdout | Save with `-o` |
|---|---|---|
| `md` | Yes | Yes |
| `json` | Yes | No |
| `html` | Yes | Yes |

### Flags

| Flag | Description |
|---|---|
| `-o`, `--output` | Output directory; omit for `stdout` |
| `-f`, `--format` | `md,json,html` |
| `--timeout` | Poll timeout in seconds |
| `--list` | Read URLs from a file |
| `--stdin-list` | Read URLs from `stdin` |
| `--concurrency` | Reserved batch concurrency flag |

### Examples

```bash
# Print markdown
mineru-open-api crawl https://mineru.net

# Print HTML
mineru-open-api crawl https://mineru.net -f html

# Batch crawl to a directory
mineru-open-api crawl https://mineru.net https://example.com -o ./pages/

# Read URLs from file
mineru-open-api crawl --list urls.txt -o ./pages/
```

---

## 🔐 `auth`

Manage token configuration for auth-required commands.

### Examples

```bash
# Interactive setup
mineru-open-api auth

# Show masked token and source
mineru-open-api auth --show

# Validate token format locally
mineru-open-api auth --verify
```

---

## 🧰 Other Commands

### `status`

Query a task by **task ID** and optionally wait for completion.

```bash
mineru-open-api status <task-id>
mineru-open-api status <task-id> --wait
mineru-open-api status <task-id> --wait -o ./out/
```

### `set-source`

Persist the request source header used for tracking.

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

## 🤖 Typical Scenarios

### Pipe Markdown into another tool

```bash
export MINERU_TOKEN="your_token_here"
mineru-open-api extract paper.pdf | some-llm-tool
```

### Save all batch results to a directory

```bash
mineru-open-api extract *.pdf -o ./results/
```

### Use flash mode when you do not want to manage tokens

```bash
mineru-open-api flash-extract quick-preview.pdf
```

### Use stdin in a larger shell pipeline

```bash
curl -L https://example.com/report.pdf | mineru-open-api extract --stdin --stdin-name report.pdf
```

---

## 📄 License

This project is licensed under the Apache-2.0 License.

---

## 🔗 Links

- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/apiManage/docs)
