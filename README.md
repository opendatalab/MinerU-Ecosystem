# mineru-open-sdk

[中文文档](./README.zh-CN.md)

Python SDK for the [MinerU](https://mineru.net) document extraction API. One line to turn documents into Markdown.

## Install

```bash
pip install mineru-open-sdk
```

## Quick Start

```bash
export MINERU_TOKEN="your-api-token"   # get it from https://mineru.net
```

```python
from mineru import MinerU

md = MinerU().extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf").markdown
```

That's it. `extract()` submits the task, polls until done, downloads the result zip, and parses out the markdown — all in one blocking call.

## Usage

### Parse a single document

```python
from mineru import MinerU

client = MinerU()
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
print(result.markdown)
print(result.content_list)  # structured JSON
print(result.images)        # list of extracted images
```

### Local files

Local files are uploaded automatically:

```python
result = client.extract("./report.pdf")
```

### Extra format export

Request additional formats alongside the default markdown + JSON:

```python
result = client.extract(
    "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    extra_formats=["docx", "html", "latex"],
)

result.save_markdown("./output/report.md")  # markdown + images/ dir
result.save_docx("./output/report.docx")
result.save_html("./output/report.html")
result.save_latex("./output/report.tex")
result.save_all("./output/full/")           # extract the full zip
```

### Crawl a web page

`crawl()` is a shorthand for `extract(url, model="html")`:

```python
result = client.crawl("https://news.example.com/article/123")
print(result.markdown)
```

### Batch extraction

`extract_batch()` submits all tasks at once and yields results as each completes — first done, first yielded:

```python
for result in client.extract_batch([
    "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
]):
    print(f"{result.filename}: {result.markdown[:200]}")
```

Batch crawling works the same way:

```python
for result in client.crawl_batch(["https://a.com/1", "https://a.com/2"]):
    print(result.markdown[:200])
```

### Async submit + query

For background services or when you need to decouple submission from polling. `submit()` returns a plain `task_id` string — store it however you like:

```python
task_id = client.submit("https://cdn-mineru.openxlab.org.cn/demo/example.pdf", model="vlm")
print(task_id)  # "a90e6ab6-44f3-4554-..."

# Later (same process, different script, whatever):
result = client.get_task(task_id)
if result.state == "done":
    print(result.markdown[:500])
else:
    print(f"State: {result.state}, progress: {result.progress}")
```

Batch version:

```python
batch_id = client.submit_batch(["a.pdf", "b.pdf", "c.pdf"])

results = client.get_batch(batch_id)
for r in results:
    print(f"{r.filename}: {r.state}")
```

### Full options

```python
result = client.extract(
    "./paper.pdf",
    model="vlm",             # "pipeline" | "vlm" | "html" (auto-inferred if omitted)
    ocr=True,                # enable OCR for scanned documents
    formula=True,            # formula recognition (default: True)
    table=True,              # table recognition (default: True)
    language="en",           # document language (default: "ch")
    pages="1-20",            # page range, e.g. "1-10,15" or "2--2"
    extra_formats=["docx"],  # also export as docx / html / latex
    timeout=600,             # max seconds to wait (default: 300)
)
```

### Flash mode (no token required)

Flash mode uses a lightweight API optimised for speed. No API token needed, only outputs Markdown — no model selection, no extra formats.

```python
client = MinerU()  # no token needed
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")
print(result.markdown)
```

With options:

```python
result = client.flash_extract(
    "./report.pdf",
    language="en",       # document language (default: "ch")
    page_range="1-10",   # page range
    timeout=300,         # max seconds to wait (default: 300)
)
result.save_markdown("./output/report.md")
```

Flash mode limitations: max 50 pages, max 10 MB file size.

When you create `MinerU("token")`, both `extract()` and `flash_extract()` are available. When you create `MinerU()` without a token, only `flash_extract()` works — calling standard methods raises `NoAuthClientError`.

### Source tracking

Every API request includes a `source` header to identify the calling application. The default is `open-api-sdk-python`. Override it if you're building your own service on top of the SDK:

```python
client = MinerU("token")
client.set_source("my-backend-service")
```

## API Reference

### Methods

| Method | Input | Output | Blocking | Use case |
|--------|-------|--------|----------|----------|
| `extract(source)` | `str` | `ExtractResult` | Yes | Single document |
| `extract_batch(sources)` | `list[str]` | `Iterator[ExtractResult]` | Yes (yields) | Batch documents |
| `crawl(url)` | `str` | `ExtractResult` | Yes | Single web page |
| `crawl_batch(urls)` | `list[str]` | `Iterator[ExtractResult]` | Yes (yields) | Batch web pages |
| `submit(source)` | `str` | `str` (task_id) | No | Async submit |
| `submit_batch(sources)` | `list[str]` | `str` (batch_id) | No | Async batch submit |
| `get_task(task_id)` | `str` | `ExtractResult` | No | Query task state |
| `get_batch(batch_id)` | `str` | `list[ExtractResult]` | No | Query batch state |
| `flash_extract(source)` | `str` | `ExtractResult` | Yes | Flash mode (no token) |

### ExtractResult

| Field | Type | Description |
|-------|------|-------------|
| `markdown` | `str \| None` | Extracted markdown text |
| `content_list` | `list[dict] \| None` | Structured JSON content |
| `images` | `list[Image]` | Extracted images |
| `docx` | `bytes \| None` | Docx bytes (requires `extra_formats`) |
| `html` | `str \| None` | HTML text (requires `extra_formats`) |
| `latex` | `str \| None` | LaTeX text (requires `extra_formats`) |
| `state` | `str` | `"done"` / `"failed"` / `"pending"` / `"running"` |
| `error` | `str \| None` | Error message when `state == "failed"` |
| `progress` | `Progress \| None` | Page progress when `state == "running"` |

Save methods: `save_markdown(path)`, `save_docx(path)`, `save_html(path)`, `save_latex(path)`, `save_all(dir)`.

### Model versions

| `model=` | Description |
|----------|-------------|
| `None` (default) | Auto-infer: `.html` → `"html"`, everything else → `"vlm"` |
| `"vlm"` | Vision-language model (recommended) |
| `"pipeline"` | Classic layout analysis |
| `"html"` | Web page extraction |

## License

Apache-2.0
