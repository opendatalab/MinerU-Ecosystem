# MinerU Open API SDK (Python)

[![PyPI version](https://badge.fury.io/py/mineru-open-sdk.svg)](https://badge.fury.io/py/mineru-open-sdk)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/opendatalab/MinerU-Ecosystem/blob/main/LICENSE)

[English README](./README.md)

**MinerU Open API SDK** 是一个完全免费的 Python 库，用于连接 [MinerU](https://mineru.net) 文档提取服务。只需一行代码，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

---

## 🚀 核心特性

- **完全免费**：文档提取服务没有任何隐藏费用。
- **Agent 轻量解析 (No Auth)**：无需 API Token 即可立即提取。
- **精准解析**：提供完整的版式保留、图片、表格及公式支持。
- **批量与轮询原语**：既提供开箱即用的阻塞式接口，也提供适合异步工作流的 submit/query 接口。
- **内置保存辅助方法**：可直接保存 Markdown、HTML、LaTeX、DOCX，或解压完整结果包。

---

## 📦 安装指南

```bash
pip install mineru-open-sdk
```

---

## 🛠️ 快速上手

### 1. Agent 轻量解析 (Flash Extract - 免登录)
适合快速预览。无需配置 Token。
```python
from mineru import MinerU

# Agent 轻量解析无需传入 Token
client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
```

### 2. 精准解析 (Precision Extract - 需登录)
支持超大文件、丰富的资产（图片/表格）及多种输出格式。
```python
from mineru import MinerU

# 从 https://mineru.net/apiManage/token 获取免费 Token
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
print(result.images) # 获取提取出的图片列表
```

---

## 🧩 支持的公开接口

### Client 生命周期

- `MinerU(token: str | None = None, base_url: str = ..., flash_base_url: str | None = None)`
- `client.close()`
- `client.set_source("your-app")`
- 支持上下文管理器：`with MinerU(...) as client:`

### 阻塞式解析接口

- `client.extract(...) -> ExtractResult`
- `client.extract_batch(...) -> Iterator[ExtractResult]`
- `client.crawl(...) -> ExtractResult`
- `client.crawl_batch(...) -> Iterator[ExtractResult]`
- `client.flash_extract(...) -> ExtractResult`

### 提交 / 查询接口

- `client.submit(...) -> str`
- `client.submit_batch(...) -> str`
- `client.get_batch(batch_id) -> list[ExtractResult]`
- `client.get_task(task_id) -> ExtractResult`

### 结果保存辅助方法

- `result.save_markdown(path, with_images=True)`
- `result.save_docx(path)`
- `result.save_html(path)`
- `result.save_latex(path)`
- `result.save_all(dir)`
- `image.save(path)`

### 常用结果字段

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

## 📊 模式对比

| 特性 | Agent 轻量解析 (Flash) | 精准解析 (Precision) |
| :--- | :--- | :--- |
| **身份认证** | **免登录 (No Auth)** | **需登录 (Token)** |
| **处理速度** | 极速 | 标准 |
| **文件大小上限** | 最大 10 MB | 最大 200 MB |
| **文件页数上限** | 最大 20 页 | 最大 600 页 |
| **支持格式** | PDF, 图片, Docx, PPTx, Excel | PDF, 图片, Doc/x, Ppt/x, Html |
| **内容完整度** | Markdown（公式和表格默认开启，OCR 默认关闭） | 完整资源 (图片、表格、公式全部保留) |
| **输出格式** | Markdown | MD, Docx, LaTeX, HTML, JSON |

---

## ⚙️ 默认行为与参数说明

### `MinerU(...)`

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `token` | `None` | 若未传入，则读取环境变量 `MINERU_TOKEN` |
| `base_url` | `https://mineru.net/api/v4` | 标准 API 的默认地址 |
| `flash_base_url` | SDK 内置默认 flash 地址 | 可用于测试或私有部署 |

如果既没有传入 `token`，环境变量 `MINERU_TOKEN` 也未设置，则 client 进入 **flash-only mode**：`flash_extract()` 可用，其他需要鉴权的方法会抛出 `NoAuthClientError`。

### 全功能接口

这些默认值适用于 `extract()`、`extract_batch()`、`submit()`、`submit_batch()`，`crawl()` / `crawl_batch()` 也会间接继承其中的大部分行为。

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `model` | `None` | 自动推断：`.html` / `.htm` 走 `"html"`，其余默认 `"vlm"` |
| `ocr` | 不设置 | 默认关闭 OCR（API 默认行为） |
| `formula` | 不设置 | 默认开启公式识别（API 默认行为） |
| `table` | 不设置 | 默认开启表格识别（API 默认行为） |
| `language` | 不设置 | 默认中文 `"ch"`（API 默认行为） |
| `pages` | `None` | 默认处理完整文档 |
| `extra_formats` | `None` | 仅返回默认的 Markdown / JSON 结果 |
| `file_params` | `None` | 批量方法中的 per-file 参数覆盖。`dict[str, FileParam]`，key 为路径/URL，`FileParam` 包含 `pages`、`ocr`、`data_id` 字段 |
| `timeout` | 单任务 `300` 秒 | `extract()` / `crawl()` 的总轮询超时 |
| `timeout` | 批量 `1800` 秒 | `extract_batch()` / `crawl_batch()` 的总轮询超时 |

### Flash Extract

| 参数 | 默认值 | 省略时行为 |
| :--- | :--- | :--- |
| `language` | `"ch"` | 默认中文 |
| `page_range` | `None` | 默认处理 flash API 允许的完整页范围 |
| `is_ocr` | `None` | OCR 默认关闭（API 默认行为） |
| `enable_formula` | `None` | 公式识别默认开启（API 默认行为） |
| `enable_table` | `None` | 表格识别默认开启（API 默认行为） |
| `timeout` | `300` 秒 | 总轮询超时 |

### `crawl()` / `crawl_batch()`

- `crawl()` 等价于 `extract(url, model="html", ...)`
- `crawl_batch()` 等价于 `extract_batch(urls, model="html", ...)`

---

## 📖 详细用法

### 全功能提取选项
```python
result = client.extract(
    "./论文.pdf",
    model="vlm",             # "vlm" | "pipeline" | "html"
    ocr=True,                # 启用 OCR 识别扫描件
    formula=True,            # 公式识别
    table=True,              # 表格识别
    language="en",           # "ch" | "en" | 等
    pages="1-20",            # 页码范围
    extra_formats=["docx"],  # 额外导出为 docx, html, 或 latex
    timeout=600,
)

result.save_all("./output/") # 保存 Markdown 和所有相关资源
```

### 上下文管理器
```python
from mineru import MinerU

with MinerU("your-api-token") as client:
    result = client.extract("./论文.pdf")
    print(result.markdown)
```

### 批量处理
```python
# 边处理边返回结果
for result in client.extract_batch(["a.pdf", "b.pdf", "c.pdf"]):
    print(f"{result.filename}: 已完成")
```

### 批量处理 - 为每个文件指定不同页码
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

### 网页爬取 (Crawl)
```python
result = client.crawl("https://www.baidu.com")
print(result.markdown)
```

---

## 🔄 `submit()` / `get_batch()` 语义说明

这一组接口最容易被误用：

- `submit()` 返回的是 **batch_id**
- `submit_batch()` 返回的也是 **batch_id**
- 因此最常见的异步流程应该是 `submit(...) -> get_batch(batch_id)`
- 对于异步轮询，建议始终沿用 batch 这一套语义

### 推荐的异步流程

```python
batch_id = client.submit("大报告.pdf")

# 轮询 batch，直到第一个结果完成
while True:
    results = client.get_batch(batch_id)
    result = results[0]
    if result.state in ("done", "failed"):
        break

if result.state == "done":
    do_something(result.markdown)
```

---

## 🤖 AI Agent 自动化集成

本 SDK 设计时充分考虑了 LLM 工作流集成。您可以通过 `result.state` 和 `result.progress` 轻松监控任务状态。

```python
batch_id = client.submit("大报告.pdf")
# ... 稍后 ...
result = client.get_batch(batch_id)[0]
if result.state == "done":
    do_something(result.markdown)
```

---

## 📄 开源协议
本项目采用 Apache-2.0 协议。

## 🔗 相关链接
- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/apiManage/docs)
