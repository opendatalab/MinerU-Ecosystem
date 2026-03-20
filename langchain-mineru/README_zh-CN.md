# langchain-mineru

基于 [MinerU](https://mineru.net) 的 LangChain 文档加载器 —— 一行代码将 PDF 等文档转换为 Markdown。

## langchain-mineru 简介

`langchain-mineru` 是深度集成至 LangChain 生态的文档加载器（Document Loader）。利用 MinerU 的文档解析能力将多种外部数据源转换为 LangChain 可处理的 `Document` 对象，便于直接接入 RAG 构建链路。支持单文档与多文档输入，并无缝衔接后续的 Text Splitter、Embedding 与 Vector Store 流程。

- ✅ `fast` 模式支持：PDF、图片（png/jpg/jpeg/jp2/webp/gif/bmp）、DOCX、PPTX、XLS、XLSX
- ✅ `accurate` 模式支持：.pdf、.doc、.docx、.ppt、.pptx、.png、.jpg、.jpeg、.html
- ✅ 支持单文档、多文档输入与 `lazy_load` 流式加载
- ✅ PDF 类型可选 `split_pages`，按页拆分 PDF 后输出多个 `Document`
- ✅ 支持两种解析模式：`fast`（快速，无需 Token）与 `accurate`（精准，需 Token）
- ✅ 适配 LangChain RAG Pipeline，便于后续切分、向量化与检索

### MinerU 简介

[MinerU](https://github.com/opendatalab/MinerU) 是一款开源文档内容提取工具，能够将 PDF、Word、PPT、图片等复杂文档转换为 Markdown、JSON 等机器可读格式，专为 LLM 预训练、RAG 和 Agent 工作流设计。

更多详情请访问 [MinerU GitHub 仓库](https://github.com/opendatalab/MinerU)。

## 安装

### 环境要求

- Python >= 3.10

### 安装步骤

```bash
pip install langchain-mineru
```

### 验证安装

```bash
python -c "from langchain_mineru import MinerULoader; print('OK')"
```

## 快速开始

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="demo.pdf")
docs = loader.load()

print(docs[0].page_content[:500])
print(docs[0].metadata)
```

默认 `mode="fast"`，无需 API Token。

## 模式说明

- `fast`：快速解析模式，调用 MinerU flash API，无需 Token。支持格式：PDF、图片（png/jpg/jpeg/jp2/webp/gif/bmp）、DOCX、PPTX、XLS、XLSX。
- `accurate`：精准解析模式，调用 MinerU 标准 `extract` 接口，需要 Token。支持格式：.pdf、.doc、.docx、.ppt、.pptx、.png、.jpg、.jpeg、.html。

`accurate` 模式 Token 申请地址：[https://mineru.net/apiManage/token](https://mineru.net/apiManage/token)。

精准模式可通过以下两种方式提供 Token：

```bash
# 方式 1：环境变量（推荐）
export MINERU_TOKEN="your-token"
```

```python
# 方式 2：构造 Loader 时显式传入
loader = MinerULoader(source="demo.pdf", mode="accurate", token="your-token")
```

## 使用示例

### 基础用法

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="demo.pdf",
    split_pages=True,
)

docs = loader.load()
for doc in docs:
    print(f"第 {doc.metadata['page']} 页: {doc.page_content[:200]}")
```

### 带参数使用

### Fast 模式（无需 Token）

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/demo.pdf",
    mode="fast",
    language="en",
    timeout=300,
)

docs = loader.load()
print(docs[0].page_content[:500])
```

### Accurate 模式（需 Token）

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="/path/to/demo.pdf",
    mode="accurate",
    token="your-token",  # 或通过 MINERU_TOKEN 环境变量提供
    language="en",
    split_pages=True,
    pages="1-5",
    timeout=300,
    ocr=True,
    formula=True,
    table=True,
)

docs = loader.load()
for doc in docs:
    print("-"*100)
    print(f"Page {doc.metadata['page']}: \n {doc.page_content[:200]}")
```

也可以直接运行示例脚本：

```bash
export MINERU_TOKEN="your-token"
uv run python mineru_example/example_accurate.py
```

### 多文件输入

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source=[
        "/path/to/demo_a.pdf",
        "/path/to/demo_b.pdf",
        "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
    ],
)

docs = loader.load()
for doc in docs:
    print(doc.metadata["source"], "-", doc.page_content[:100])
```

### RAG Pipeline

#### RAG（fast 模式，无需 Token）

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(source="demo.pdf", mode="fast")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("这个文档的核心配置步骤是什么？", k=3)
for r in results:
    print(r.page_content[:200])
```

#### RAG（accurate 模式，需 Token）

```python
from langchain_mineru import MinerULoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

loader = MinerULoader(
    source="manual.pdf",
    mode="accurate",
    token="your-token",  # 或设置 MINERU_TOKEN
    ocr=True,
    formula=True,
    table=True,
)
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
chunks = splitter.split_documents(docs)

vs = FAISS.from_documents(chunks, OpenAIEmbeddings())
results = vs.similarity_search("这个文档怎么配置 OCR？", k=3)
for r in results:
    print(r.page_content[:200])
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | `str \| list[str]` | *必填* | 本地文件路径或 URL，支持单个或列表。支持格式依赖 `mode`：`fast` 支持 PDF、图片（png/jpg/jpeg/jp2/webp/gif/bmp）、DOCX、PPTX、XLS、XLSX；`accurate` 支持 .pdf、.doc、.docx、.ppt、.pptx、.png、.jpg、.jpeg、.html。 |
| `mode` | `str` | `"fast"` | 解析模式。`"fast"` 为快速模式（无需 Token）；`"accurate"` 为精准模式（需 Token）。 |
| `token` | `str \| None` | `None` | MinerU API Token。仅 `mode="accurate"` 时需要。申请地址：[https://mineru.net/apiManage/token](https://mineru.net/apiManage/token)。不传时会读取环境变量 `MINERU_TOKEN`。 |
| `language` | `str` | `"ch"` | OCR 识别语言代码。常用值：`"ch"`（中文）、`"en"`（英文）。完整列表请参考[标准 API 文档](https://mineru.net/apiManage/docs)。 |
| `pages` | `str \| None` | `None` | 页码范围，仅对 PDF 有效，例如 `"1-5"` 或 `"3"`。`split_pages=False` 时，页码范围直接传给 API；`split_pages=True` 时，本地只拆指定页，减少 API 调用次数。 |
| `timeout` | `int` | `1200` | 单文件最大等待时间（秒）。 |
| `split_pages` | `bool` | `False` | 仅对 PDF 有效。为 `True` 时，按页拆分 PDF，每页生成一个 `Document`，`metadata["page"]` 可用。非 PDF 文件不受影响，始终返回一个 `Document`。 |
| `ocr` | `bool` | `False` | 在 `mode="accurate"` 下生效并控制 OCR；在 `mode="fast"` 下 OCR 为内置能力，该参数会被忽略。 |
| `formula` | `bool` | `True` | 仅 `mode="accurate"` 生效，是否启用公式识别。`mode="fast"` 下传非默认值会报错。 |
| `table` | `bool` | `True` | 仅 `mode="accurate"` 生效，是否启用表格识别。`mode="fast"` 下传非默认值会报错。 |

## Document Metadata 说明

每个返回的 `Document` 包含以下 metadata 字段：

```python
{
    "source": "report.pdf",          # 原始输入路径或 URL
    "loader": "mineru",
    "output_format": "markdown",
    "mode": "fast",                  # fast / accurate
    "language": "ch",
    "pages": None,
    "split_pages": True,
    "filename": "report.pdf",        # MinerU 返回的文件名
    "page": 1,                       # 仅 split_pages=True 时存在
    "page_source": "report.pdf",     # 仅 split_pages=True 时存在
}
```

## 支持的文件格式

- `accurate` 模式：.pdf、.doc、.docx、.ppt、.pptx、.png、.jpg、.jpeg、.html
- `fast` 模式：PDF、图片（png/jpg/jpeg/jp2/webp/gif/bmp）、DOCX、PPTX、XLS、XLSX

## 限制

- 输出格式仅支持 Markdown
- `fast` 模式受 flash API 限制（如页数/文件大小），请以 MinerU 官方文档为准
- `accurate` 模式需要有效 Token，且请求配额由账号策略决定

## 许可证

Apache-2.0
