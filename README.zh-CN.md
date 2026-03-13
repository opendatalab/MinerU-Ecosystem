# mineru-open-sdk

[English](./README.md)

[MinerU](https://mineru.net) 文档解析 API 的 Python SDK。一行代码把文档变成 Markdown。

## 安装

```bash
pip install mineru-open-sdk
```

## 快速开始

```bash
export MINERU_TOKEN="your-api-token"   # 在 https://mineru.net 获取
```

```python
from mineru import MinerU

md = MinerU().extract("https://example.com/report.pdf").markdown
```

`extract()` 内部完成提交任务、轮询状态、下载结果、解析 zip 的全流程，调用者只看到"传入 URL，拿到 Markdown"。

## 使用示例

### 解析单个文档

```python
from mineru import MinerU

client = MinerU()
result = client.extract("https://example.com/paper.pdf")
print(result.markdown)
print(result.content_list)  # 结构化 JSON
print(result.images)        # 提取的图片列表
```

### 本地文件

自动上传：

```python
result = client.extract("./report.pdf")
```

### 额外格式导出

在默认的 Markdown + JSON 之外，还可以导出其他格式：

```python
result = client.extract(
    "https://example.com/report.pdf",
    extra_formats=["docx", "html", "latex"],
)

result.save_markdown("./output/report.md")  # markdown + images/ 目录
result.save_docx("./output/report.docx")
result.save_html("./output/report.html")
result.save_latex("./output/report.tex")
result.save_all("./output/full/")           # 解压完整 zip
```

### 网页抓取

`crawl()` 等价于 `extract(url, model="html")`：

```python
result = client.crawl("https://news.example.com/article/123")
print(result.markdown)
```

### 批量解析

`extract_batch()` 一次性提交所有任务，先完成的先 yield：

```python
for result in client.extract_batch([
    "https://example.com/ch1.pdf",
    "https://example.com/ch2.pdf",
    "https://example.com/ch3.pdf",
]):
    print(f"{result.filename}: {result.markdown[:200]}")
```

批量网页抓取同理：

```python
for result in client.crawl_batch(["https://a.com/1", "https://a.com/2"]):
    print(result.markdown[:200])
```

### 异步提交 + 查询

适用于后台服务或需要将提交和查询解耦的场景。`submit()` 返回纯字符串 `task_id`，存取方式由你决定：

```python
task_id = client.submit("https://example.com/big-report.pdf", model="vlm")
print(task_id)  # "a90e6ab6-44f3-4554-..."

# 随时查询（同一进程、另一个脚本、都行）：
result = client.get_task(task_id)
if result.state == "done":
    print(result.markdown[:500])
else:
    print(f"状态: {result.state}, 进度: {result.progress}")
```

批量版本：

```python
batch_id = client.submit_batch(["a.pdf", "b.pdf", "c.pdf"])

results = client.get_batch(batch_id)
for r in results:
    print(f"{r.filename}: {r.state}")
```

### 完整参数

```python
result = client.extract(
    "./paper.pdf",
    model="vlm",             # "pipeline" | "vlm" | "html"（不传则自动推断）
    ocr=True,                # 扫描件启用 OCR
    formula=True,            # 公式识别（默认开启）
    table=True,              # 表格识别（默认开启）
    language="en",           # 文档语言（默认 "ch"）
    pages="1-20",            # 页码范围，如 "1-10,15" 或 "2--2"
    extra_formats=["docx"],  # 额外导出 docx / html / latex
    timeout=600,             # 最大等待秒数（默认 300）
)
```

## API 速查

### 方法

| 方法 | 输入 | 输出 | 阻塞 | 场景 |
|------|------|------|------|------|
| `extract(source)` | `str` | `ExtractResult` | 是 | 单个文档 |
| `extract_batch(sources)` | `list[str]` | `Iterator[ExtractResult]` | 是（yield） | 批量文档 |
| `crawl(url)` | `str` | `ExtractResult` | 是 | 单个网页 |
| `crawl_batch(urls)` | `list[str]` | `Iterator[ExtractResult]` | 是（yield） | 批量网页 |
| `submit(source)` | `str` | `str`（task_id） | 否 | 异步提交 |
| `submit_batch(sources)` | `list[str]` | `str`（batch_id） | 否 | 异步批量提交 |
| `get_task(task_id)` | `str` | `ExtractResult` | 否 | 查询状态 |
| `get_batch(batch_id)` | `str` | `list[ExtractResult]` | 否 | 查询批量状态 |

### ExtractResult 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `markdown` | `str \| None` | Markdown 正文 |
| `content_list` | `list[dict] \| None` | 结构化 JSON 内容 |
| `images` | `list[Image]` | 提取的图片 |
| `docx` | `bytes \| None` | docx 二进制（需 `extra_formats`） |
| `html` | `str \| None` | HTML 文本（需 `extra_formats`） |
| `latex` | `str \| None` | LaTeX 文本（需 `extra_formats`） |
| `state` | `str` | `"done"` / `"failed"` / `"pending"` / `"running"` |
| `error` | `str \| None` | 失败原因（`state == "failed"` 时） |
| `progress` | `Progress \| None` | 页级进度（`state == "running"` 时） |

保存方法：`save_markdown(path)`, `save_docx(path)`, `save_html(path)`, `save_latex(path)`, `save_all(dir)`

### model 参数

| `model=` | 说明 |
|----------|------|
| `None`（默认） | 自动推断：`.html` → `"html"`，其余 → `"vlm"` |
| `"vlm"` | VLM 视觉语言模型（推荐） |
| `"pipeline"` | 传统版面分析 |
| `"html"` | 网页解析 |

## License

Apache-2.0
