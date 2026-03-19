# langchain-mineru

LangChain document loader powered by [MinerU](https://mineru.net) — turn PDFs and documents into Markdown with one line of code.

## What is langchain-mineru?

`langchain-mineru` is a LangChain Document Loader deeply integrated into the LangChain ecosystem. It leverages MinerU's document parsing capabilities to convert diverse external data sources into LangChain-compatible `Document` objects, ready to plug into RAG pipelines. It supports both single-document and multi-document input, and integrates seamlessly with downstream Text Splitter, Embedding, and Vector Store workflows.

- ✅ Supports PDF / Image / DOCX / PPTx / XLS / XLSX / online URL 
- ✅ Supports single and multi-document input with `lazy_load` streaming
- ✅ Optional `split_pages` mode for PDFs — splits into one `Document` per page
- ✅ Two parsing modes: `fast` (no token) and `accurate` (token required)
- ✅ Compatible with LangChain RAG Pipelines — ready for chunking, embedding, and retrieval

### What is MinerU?

[MinerU](https://github.com/opendatalab/MinerU) is an open-source tool that converts complex documents (PDFs, Word, PPT, images, etc.) into machine-readable formats like Markdown and JSON. It is designed to extract high-quality content for LLM pre-training, RAG, and agentic workflows.

For more details, visit the [MinerU GitHub repository](https://github.com/opendatalab/MinerU).

## Installation

### Prerequisites

- Python >= 3.10

### Installation Steps

```bash
pip install langchain-mineru
```

### Verify

```bash
python -c "from langchain_mineru import MinerULoader; print('OK')"
```

## Quick Start

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="report.pdf")
docs = loader.load()

print(docs[0].page_content[:500])
print(docs[0].metadata)
```

Default is `model="fast"` and no API token is required.

## Mode Selection

- `fast`: Calls MinerU flash API, optimized for speed, no token required, and supports both document and HTML input.
- `accurate`: Calls MinerU standard `extract` API, token required.

You can provide token in two ways:

```bash
# Option 1: environment variable (recommended)
export MINERU_TOKEN="your-token"
```

```python
# Option 2: pass token directly
loader = MinerULoader(source="report.pdf", model="accurate", token="your-token")
```

## Usage Examples

### Basic Usage

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="report.pdf",
    split_pages=True,
)

docs = loader.load()
for doc in docs:
    print(f"Page {doc.metadata['page']}: {doc.page_content[:200]}")
```

### With Parameters

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/demo.pdf",
    model="fast",
    language="en",
    pages="1-10",
    timeout=300,
)

docs = loader.load()
print(docs[0].page_content[:500])
```

### Accurate Mode (Token Required)

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/demo.pdf",
    model="accurate",
    token="your-token",  # or set MINERU_TOKEN
    language="en",
    pages="1-10",
    timeout=300,
    ocr=True,
    formula=True,
    table=True,
)

docs = loader.load()
print(docs[0].page_content[:500])
```

Or run the dedicated example script directly:

```bash
export MINERU_TOKEN="your-token"
uv run python mineru_example/example_accurate.py
```

### Multiple Sources

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source=[
        "/path/to/a.pdf",
        "/path/to/b.pdf",
        "https://example.com/demo.pdf",
    ],
)

docs = loader.load()
for doc in docs:
    print(doc.metadata["source"], "-", doc.page_content[:100])
```

### RAG Pipeline

#### RAG (fast mode, no token)

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(source="manual.pdf", model="fast")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("what are the core setup steps in this document?", k=3)
for r in results:
    print(r.page_content[:200])
```

#### RAG (accurate mode, token required)

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(
    source="manual.pdf",
    model="accurate",
    token="your-token",  # or set MINERU_TOKEN
    ocr=True,
    formula=True,
    table=True,
)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("what are the core setup steps in this document?", k=3)
for r in results:
    print(r.page_content[:200])
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str \| list[str]` | *required* | Local file path(s) or URL(s). Supports PDF, DOCX, PPTX, images, and online URLs. |
| `model` | `str` | `"fast"` | Parsing mode. `"fast"` is speed-first and token-free; `"accurate"` uses standard API and requires token. |
| `token` | `str \| None` | `None` | MinerU API token. Required for `model="accurate"`. If omitted, `MINERU_TOKEN` environment variable is used. |
| `language` | `str` | `"ch"` | Document language code for OCR. Common values: `"ch"` (Chinese), `"en"` (English), `"auto"` (auto-detect). For the complete list, refer to the [standard API documentation](https://mineru.net/apiManage/docs). |
| `pages` | `str \| None` | `None` | Page range to extract, e.g. `"1-5"` or `"3"`. Only applies to PDF files. When `split_pages=False`, the range is forwarded to the API. When `split_pages=True`, only the specified pages are split and parsed locally — reducing API calls and processing time. |
| `timeout` | `int` | `1200` | Maximum seconds to wait for extraction per file. |
| `split_pages` | `bool` | `False` | PDF only. When `True`, splits the PDF into one `Document` per page. Each page is parsed independently, so `metadata["page"]` is available. Non-PDF files are unaffected — they always produce one `Document`. |
| `ocr` | `bool` | `False` | Effective only when `model="accurate"`. Enables OCR. Passing non-default value in `model="fast"` raises an error. |
| `formula` | `bool` | `True` | Effective only when `model="accurate"`. Enables formula recognition. Passing non-default value in `model="fast"` raises an error. |
| `table` | `bool` | `True` | Effective only when `model="accurate"`. Enables table recognition. Passing non-default value in `model="fast"` raises an error. |

## Document Metadata

Each returned `Document` includes the following metadata:

```python
{
    "source": "report.pdf",          # original source path or URL
    "loader": "mineru",
    "output_format": "markdown",
    "model": "fast",                 # fast / accurate
    "language": "ch",
    "pages": None,
    "split_pages": False,
    "filename": "report.pdf",
    "page": 1,                       # only present when split_pages=True
    "page_source": "report.pdf",     # only present when split_pages=True
}
```

## Supported File Formats

PDF, DOC, DOCX, PPT, PPTX, PNG, JPG, JPEG

## Limitations

- Output format is Markdown only
- `fast` mode follows flash API limits (such as page/file constraints)
- `accurate` mode requires a valid token and available account quota

## License

Apache-2.0
