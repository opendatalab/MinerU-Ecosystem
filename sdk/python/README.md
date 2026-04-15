# MinerU Open API SDK (Python)

[![PyPI version](https://badge.fury.io/py/mineru-open-sdk.svg)](https://badge.fury.io/py/mineru-open-sdk)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)

[中文文档](./README.zh-CN.md)

**MinerU Open API SDK** is a completely free Python library for the [MinerU](https://mineru.net) document extraction service. Turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown with just one line of code.

---

## 🚀 Key Features

- **Completely Free**: No hidden costs for document extraction.
- **Flash Extract (No Auth)**: Extract text instantly without an API token.
- **Precision Extract**: Comprehensive extraction with layout preservation, images, and formula support.
- **Batch & Polling Primitives**: Blocking methods for simple flows plus submit/query methods for asynchronous workflows.
- **Simple Save Helpers**: Save Markdown, HTML, LaTeX, DOCX, or the full extracted zip with built-in helpers.

---

## 📦 Install

```bash
pip install mineru-open-sdk
```

---

## 🛠️ Quick Start

### 1. Flash Extract (Fast, No Auth)
Ideal for quick previews. No token required.
```python
from mineru import MinerU

# No token needed for Flash Extract
client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
```

### 2. Precision Extract (Auth Required)
Supports large files, rich assets (images/tables), and multiple formats.
```python
from mineru import MinerU

# Get your free token from https://mineru.net/apiManage/token
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
print(result.images) # Access extracted images
```

---

## 🧩 Supported Public API

### Client lifecycle

- `MinerU(token: str | None = None, base_url: str = ..., flash_base_url: str | None = None)`
- `client.close()`
- `client.set_source("your-app")`
- context manager support: `with MinerU(...) as client:`

### Blocking extraction methods

- `client.extract(...) -> ExtractResult`
- `client.extract_batch(...) -> Iterator[ExtractResult]`
- `client.crawl(...) -> ExtractResult`
- `client.crawl_batch(...) -> Iterator[ExtractResult]`
- `client.flash_extract(...) -> ExtractResult`

### Submit/query methods

- `client.submit(...) -> str`
- `client.submit_batch(...) -> str`
- `client.get_batch(batch_id) -> list[ExtractResult]`
- `client.get_task(task_id) -> ExtractResult`

### Result helpers

- `result.save_markdown(path, with_images=True)`
- `result.save_docx(path)`
- `result.save_html(path)`
- `result.save_latex(path)`
- `result.save_all(dir)`
- `image.save(path)`

### Result fields you will usually use

- `result.state`
- `result.progress`
- `result.markdown`
- `result.images`
- `result.content_list`
- `result.docx`
- `result.html`
- `result.latex`
- `result.task_id`

---

## 📊 Mode Comparison

| Feature | Flash Extract | Precision Extract |
| :--- | :--- | :--- |
| **Auth** | **No Auth Required** | **Auth Required (Token)** |
| **Speed** | Blazing Fast | Standard |
| **File Limit** | Max 10 MB | Max 200 MB |
| **Page Limit** | Max 20 Pages | Max 200 Pages |
| **Formats** | PDF, Images, Docx, PPTx, Excel | PDF, Images, Doc/x, Ppt/x, Html |
| **Content** | Markdown (formula & table on by default, OCR off) | Full assets (Images, Tables, Formulas) |
| **Output** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## ⚙️ Defaults And Option Behavior

### `MinerU(...)`

| Argument | Default | Behavior |
| :--- | :--- | :--- |
| `token` | `None` | If omitted, the SDK reads `MINERU_TOKEN` from the environment |
| `base_url` | `https://mineru.net/api/v4` | Standard API base URL |
| `flash_base_url` | SDK default flash URL | Override flash API endpoint for testing/private deployments |

If neither `token` nor `MINERU_TOKEN` is set, the client works in **flash-only mode**: `flash_extract()` works, while auth-required methods raise `NoAuthClientError`.

### Precision methods

These defaults apply to `extract()`, `extract_batch()`, `submit()`, `submit_batch()`, and indirectly to `crawl()` / `crawl_batch()` unless noted otherwise.

| Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `model` | `None` | Auto-infers model: `.html`/`.htm` uses `"html"`, everything else uses `"vlm"` |
| `ocr` | not set | OCR is disabled (API default) |
| `formula` | not set | Formula recognition is enabled (API default) |
| `table` | not set | Table recognition is enabled (API default) |
| `language` | not set | Chinese `"ch"` (API default) |
| `pages` | `None` | Full document is processed |
| `extra_formats` | `None` | Only the default Markdown/JSON payload is returned |
| `file_params` | `None` | Per-file overrides for batch methods. A `dict[str, FileParam]` keyed by path/URL, where `FileParam` has fields `pages`, `ocr`, `data_id` |
| `timeout` | `300` seconds for single-item methods | Max total polling time for `extract()` / `crawl()` |
| `timeout` | `1800` seconds for batch methods | Max total polling time for `extract_batch()` / `crawl_batch()` |

### Flash Extract

| Option | Default | Behavior when omitted |
| :--- | :--- | :--- |
| `language` | `"ch"` | Default language is Chinese |
| `page_range` | `None` | Full page range allowed by the flash API |
| `is_ocr` | `None` | OCR is off (API default) |
| `enable_formula` | `None` | Formula recognition is on (API default) |
| `enable_table` | `None` | Table recognition is on (API default) |
| `timeout` | `300` seconds | Max total polling time |

### `crawl()` / `crawl_batch()`

- `crawl()` is shorthand for `extract(url, model="html", ...)`
- `crawl_batch()` is shorthand for `extract_batch(urls, model="html", ...)`

---

## 📖 Detailed Usage

### Precision Extraction Options
```python
result = client.extract(
    "./paper.pdf",
    model="vlm",             # "vlm" | "pipeline" | "html"
    ocr=True,                # Enable OCR for scanned documents
    formula=True,            # Formula recognition
    table=True,              # Table recognition
    language="en",           # "ch" | "en" | etc.
    pages="1-20",            # Page range
    extra_formats=["docx"],  # Export as docx, html, or latex
    timeout=600,
)

result.save_all("./output/") # Save markdown and all assets
```

### Context Manager
```python
from mineru import MinerU

with MinerU("your-api-token") as client:
    result = client.extract("./paper.pdf")
    print(result.markdown)
```

### Batch Processing
```python
# Yields results as they complete
for result in client.extract_batch(["a.pdf", "b.pdf", "c.pdf"]):
    print(f"{result.filename}: Done")
```

### Batch With Per-File Pages
```python
from mineru import FileParam

batch_id = client.submit_batch(
    ["a.pdf", "b.pdf"],
    file_params={
        "a.pdf": FileParam(pages="1-5"),
        "b.pdf": FileParam(pages="10-20"),
    },
)
```

### Web Crawling
```python
result = client.crawl("https://www.baidu.com")
print(result.markdown)
```

---

## 🔄 `submit()` / `get_batch()` Semantics

This is the part most people get wrong at first:

- `submit()` returns a **batch ID**
- `submit_batch()` also returns a **batch ID**
- the common async flow is therefore `submit(...) -> get_batch(batch_id)`
- recommends staying on the batch-based flow for async polling

### Recommended async flow

```python
batch_id = client.submit("large-report.pdf")

# poll the batch until the first item is done
while True:
    results = client.get_batch(batch_id)
    result = results[0]
    if result.state in ("done", "failed"):
        break

if result.state == "done":
    do_something(result.markdown)
```

---

## 🤖 Integration for AI Agents

The SDK is designed to be easily integrated into LLM workflows. For status updates, you can check `result.state` and `result.progress`.

```python
batch_id = client.submit("large-report.pdf")
# ... later ...
result = client.get_batch(batch_id)[0]
if result.state == "done":
    do_something(result.markdown)
```

---

## 📄 License
This project is licensed under the Apache-2.0 License.

## 🔗 Links
- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/apiManage/docs)
