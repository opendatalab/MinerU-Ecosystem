# MinerU Open API SDK (Python)

[![PyPI version](https://badge.fury.io/py/mineru-open-sdk.svg)](https://badge.fury.io/py/mineru-open-sdk)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/sdk/go-python/blob/main/LICENSE)

[中文文档](./README.zh-CN.md)

**MinerU Open API SDK** is a completely free Python library for the [MinerU](https://mineru.net) document extraction service. Turn any document (PDF, Images, Word, PPT, Excel) or Web Page into high-quality Markdown with just one line of code.

---

## 🚀 Key Features

- **Completely Free**: No hidden costs for document extraction.
- **Flash Mode (No Auth)**: Extract text instantly without an API token.
- **Full Feature Mode**: Comprehensive extraction with layout preservation, images, and formula support.
- **Async & Batch**: Built-in support for processing hundreds of documents efficiently.

---

## 📦 Install

```bash
pip install mineru-open-sdk
```

---

## 🛠️ Quick Start

### 1. Flash Extract (Fast, No Auth, Markdown-only)
Ideal for quick previews. No token required.
```python
from mineru import MinerU

# No token needed for Flash Mode
client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
```

### 2. Full Feature Extract (Auth Required)
Supports large files, rich assets (images/tables), and multiple formats.
```python
from mineru import MinerU

# Get your free token from https://mineru.net
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
print(result.images) # Access extracted images
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

### Batch Processing
```python
# Yields results as they complete
for result in client.extract_batch(["a.pdf", "b.pdf", "c.pdf"]):
    print(f"{result.filename}: Done")
```

### Web Crawling
```python
result = client.crawl("https://www.baidu.com")
print(result.markdown)
```

---

## 🤖 Integration for AI Agents

The SDK is designed to be easily integrated into LLM workflows. For status updates, you can check `result.state` and `result.progress`.

```python
task_id = client.submit("large-report.pdf")
# ... later ...
result = client.get_task(task_id)
if result.state == "done":
    do_something(result.markdown)
```

---

## 📄 License
This project is licensed under the Apache-2.0 License.

## 🔗 Links
- [Official Website](https://mineru.net)
- [API Documentation](https://mineru.net/docs)
