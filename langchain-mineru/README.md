# langchain-mineru

LangChain document loader powered by [MinerU](https://mineru.net) — turn PDFs and documents into Markdown with one line of code.

## What is langchain-mineru?

`langchain-mineru` is a LangChain Document Loader deeply integrated into the LangChain ecosystem. It requires no API key registration — simply call it directly and leverage MinerU's document parsing capabilities to convert diverse external data sources into LangChain-compatible `Document` objects, ready to plug into RAG pipelines. It supports both single-document and multi-document input, and integrates seamlessly with downstream Text Splitter, Embedding, and Vector Store workflows.

- ✅ Supports PDF / Image / DOCX / PPTx / XLS / XLSX / online URL 
- ✅ Supports single and multi-document input with `lazy_load` streaming
- ✅ Optional `split_pages` mode for PDFs — splits into one `Document` per page
- ✅ Compatible with LangChain RAG Pipelines — ready for chunking, embedding, and retrieval

### What is MinerU?

[MinerU](https://github.com/opendatalab/MinerU) is an open-source tool that converts complex documents (PDFs, Word, PPT, images, etc.) into machine-readable formats like Markdown and JSON. It is designed to extract high-quality content for LLM pre-training, RAG, and agentic workflows.

For more details, visit the [MinerU GitHub repository](https://github.com/opendatalab/MinerU).

## Installation

<!-- TODO: 发布到 PyPI 后取消注释，替换为以下安装方式：
```bash
pip install langchain-mineru
```
-->

### Prerequisites

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Step 1: Clone the repository

```bash
git clone https://github.com/opendatalab/langchain-mineru.git
cd langchain-mineru
```

### Step 2: Install

**Using uv (recommended):**

```bash
uv sync
```

`uv sync` will read `pyproject.toml`，install all dependences.

**Using pip:**

```bash
# 先安装 MinerU SDK（尚未发布到 PyPI，需要从 GitLab 安装）
pip install git+https://gitlab.pjlab.org.cn/yangqi/mineru-open-sdk-python.git

# 再安装 langchain-mineru
pip install -e .
```

### Step 3: Verify

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

No API token required.

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
    language="en",
    pages="1-10",
    timeout=300,
)

docs = loader.load()
print(docs[0].page_content[:500])
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

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(source="manual.pdf")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("how to configure OCR?", k=3)
for r in results:
    print(r.page_content[:200])
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str \| list[str]` | *required* | Local file path(s) or URL(s). Supports PDF, DOCX, PPTX, images, and online URLs. |
| `language` | `str` | `"ch"` | Document language code for OCR. Common values: `"ch"` (Chinese), `"en"` (English), `"auto"` (auto-detect). For the complete list, refer to the [standard API documentation](https://mineru.net/apiManage/docs). |
| `pages` | `str \| None` | `None` | Page range to extract, e.g. `"1-5"` or `"3"`. Only applies to PDF files. When `split_pages=False`, the range is forwarded to the API. When `split_pages=True`, only the specified pages are split and parsed locally — reducing API calls and processing time. |
| `timeout` | `int` | `1200` | Maximum seconds to wait for extraction per file. |
| `split_pages` | `bool` | `False` | PDF only. When `True`, splits the PDF into one `Document` per page. Each page is parsed independently, so `metadata["page"]` is available. Non-PDF files are unaffected — they always produce one `Document`. |

## Document Metadata

Each returned `Document` includes the following metadata:

```python
{
    "source": "report.pdf",          # original source path or URL
    "loader": "mineru",
    "output_format": "markdown",
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
- Maximum 20 pages per document
- Maximum 10 MB per file

## License

Apache-2.0
