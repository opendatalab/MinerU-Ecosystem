# mineru-open-sdk

MinerU API 的 Python SDK。一行代码把文档变成 Markdown。

## 安装

```bash
pip install mineru-open-sdk
```

## 快速开始

```bash
export MINERU_TOKEN="your-api-token"
```

```python
from mineru import MinerU

md = MinerU().extract("https://example.com/report.pdf").markdown
```

## 使用示例

### 解析单个文档

```python
from mineru import MinerU

client = MinerU()
result = client.extract("https://example.com/paper.pdf")
print(result.markdown)
```

### 本地文件

```python
result = client.extract("./report.pdf")
```

### 额外格式导出

```python
result = client.extract(
    "https://example.com/report.pdf",
    extra_formats=["docx", "html"],
)
result.save_docx("./report.docx")
result.save_html("./report.html")
```

### 网页抓取

```python
result = client.crawl("https://news.example.com/article/123")
print(result.markdown)
```

### 批量解析

```python
for result in client.extract_batch([
    "https://example.com/ch1.pdf",
    "https://example.com/ch2.pdf",
    "https://example.com/ch3.pdf",
]):
    print(f"{result.filename}: {result.markdown[:200]}")
```

### 异步提交

```python
task_id = client.submit("https://example.com/big-report.pdf")
# ... later ...
result = client.get_task(task_id)
```

## 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `model` | `str` | 自动推断 | `"pipeline"` / `"vlm"` / `"html"` |
| `ocr` | `bool` | `False` | 启用 OCR |
| `formula` | `bool` | `True` | 公式识别 |
| `table` | `bool` | `True` | 表格识别 |
| `language` | `str` | `"ch"` | 文档语言 |
| `pages` | `str` | `None` | 页码范围，如 `"1-10,15"` |
| `extra_formats` | `list` | `None` | `["docx", "html", "latex"]` |
| `timeout` | `int` | `300` | 超时秒数 |

## License

MIT
