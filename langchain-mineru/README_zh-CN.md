# langchain-mineru

基于 [MinerU](https://mineru.net) 的 LangChain 文档加载器 —— 一行代码将 PDF 等文档转换为 Markdown。

## langchain-mineru 简介

`langchain-mineru` 是深度集成至 LangChain 生态的文档加载器（Document Loader）。无需注册 API key 即可直接调用，利用 MinerU 的文档解析能力将多种外部数据源转换为 LangChain 可处理的 `Document` 对象，便于直接接入 RAG 构建链路。支持单文档与多文档输入，并无缝衔接后续的 Text Splitter、Embedding 与 Vector Store 流程。

- ✅ 支持 PDF / 图片 / DOCX / PPTx / XLS / XLSX / 在线 URL 
- ✅ 支持单文档、多文档输入与 `lazy_load` 流式加载
- ✅ PDF 类型可选 `split_pages`，按页拆分 PDF 后输出多个 `Document`
- ✅ 适配 LangChain RAG Pipeline，便于后续切分、向量化与检索

### MinerU 简介

[MinerU](https://github.com/opendatalab/MinerU) 是一款开源文档内容提取工具，能够将 PDF、Word、PPT、图片等复杂文档转换为 Markdown、JSON 等机器可读格式，专为 LLM 预训练、RAG 和 Agent 工作流设计。

更多详情请访问 [MinerU GitHub 仓库](https://github.com/opendatalab/MinerU)。

## 安装

<!-- TODO: 发布到 PyPI 后取消注释，替换为以下安装方式：
```bash
pip install langchain-mineru
```
-->

### 环境要求

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/)（推荐）或 pip

### 第一步：克隆仓库

```bash
git clone https://github.com/opendatalab/langchain-mineru.git
cd langchain-mineru
```

### 第二步：安装

**使用 uv（推荐）：**

```bash
uv sync
```

`uv sync` 会自动读取 `pyproject.toml`，安装所有依赖（包括 MinerU SDK）并创建虚拟环境。

**使用 pip：**

```bash
# 先安装 MinerU SDK（尚未发布到 PyPI，需要从 GitLab 安装）
pip install git+https://gitlab.pjlab.org.cn/yangqi/mineru-open-sdk-python.git

# 再安装 langchain-mineru
pip install -e .
```

### 第三步：验证安装

```bash
python -c "from langchain_mineru import MinerULoader; print('OK')"
```

## 快速开始

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(source="report.pdf")
docs = loader.load()

print(docs[0].page_content[:500])
print(docs[0].metadata)
```

无需 API Token。

## 使用示例

### 基础用法

```python
from langchain_mineru import MinerULoader

loader = MinerULoader(
    source="report.pdf",
    split_pages=True,
)

docs = loader.load()
for doc in docs:
    print(f"第 {doc.metadata['page']} 页: {doc.page_content[:200]}")
```

### 自定义参数

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

### 多文件输入

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

### RAG 流水线

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
results = vs.similarity_search("这个文档怎么配置 OCR？", k=3)
for r in results:
    print(r.page_content[:200])
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `source` | `str \| list[str]` | *必填* | 本地文件路径或 URL，支持单个或列表。支持 PDF、DOCX、PPTX、图片及在线 URL。 |
| `language` | `str` | `"ch"` | OCR 识别语言代码。常用值：`"ch"`（中文）、`"en"`（英文）、`"auto"`（自动检测）。完整列表请参考[标准 API 文档](https://mineru.net/apiManage/docs)。 |
| `pages` | `str \| None` | `None` | 页码范围，仅对 PDF 有效，例如 `"1-5"` 或 `"3"`。`split_pages=False` 时，页码范围直接传给 API；`split_pages=True` 时，本地只拆指定页，减少 API 调用次数。 |
| `timeout` | `int` | `1200` | 单文件最大等待时间（秒）。 |
| `split_pages` | `bool` | `False` | 仅对 PDF 有效。为 `True` 时，按页拆分 PDF，每页生成一个 `Document`，`metadata["page"]` 可用。非 PDF 文件不受影响，始终返回一个 `Document`。 |

## Document Metadata 说明

每个返回的 `Document` 包含以下 metadata 字段：

```python
{
    "source": "report.pdf",          # 原始输入路径或 URL
    "loader": "mineru",
    "output_format": "markdown",
    "language": "ch",
    "pages": None,
    "split_pages": False,
    "filename": "report.pdf",        # MinerU 返回的文件名
    "page": 1,                       # 仅 split_pages=True 时存在
    "page_source": "report.pdf",     # 仅 split_pages=True 时存在
}
```

## 支持的文件格式

PDF、DOC、DOCX、PPT、PPTX、PNG、JPG、JPEG

## 限制

- 输出格式仅支持 Markdown
- 单文档最多 20 页
- 单文件最大 10 MB

## 许可证

Apache-2.0
