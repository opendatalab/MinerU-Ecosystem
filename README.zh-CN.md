# MinerU Open API SDK (Python)

[![PyPI version](https://badge.fury.io/py/mineru-open-sdk.svg)](https://badge.fury.io/py/mineru-open-sdk)
[![License](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](https://github.com/OpenDataLab/mineru-open-sdk-python/blob/main/LICENSE)

[English README](./README.md)

**MinerU Open API SDK** 是一个完全免费的 Python 库，用于连接 [MinerU](https://mineru.net) 文档提取服务。只需一行代码，即可将任何文档（PDF、图片、Word、PPT、Excel）或网页转换为高质量的 Markdown。

---

## 🚀 核心特性

- **完全免费**：文档提取服务没有任何隐藏费用。
- **极速模式 (No Auth)**：无需 API Token 即可立即提取。
- **全功能模式**：提供完整的版式保留、图片、表格及公式支持。
- **异步与批量**：原生支持高效处理成百上千份文档。

---

## 📦 安装指南

```bash
pip install mineru-open-sdk
```

---

## 🛠️ 快速上手

### 1. 极速模式 (Flash Extract - 免登录，只支持Markdown)
适合快速预览。无需配置 Token。
```python
from mineru import MinerU

# 极速模式无需传入 Token
client = MinerU()
result = client.flash_extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
```

### 2. 全功能模式 (Full Feature Extract - 需登录)
支持超大文件、丰富的资产（图片/表格）及多种输出格式。
```python
from mineru import MinerU

# 从 https://mineru.net 获取免费 Token
client = MinerU("your-api-token")
result = client.extract("https://cdn-mineru.openxlab.org.cn/demo/example.pdf")

print(result.markdown)
print(result.images) # 获取提取出的图片列表
```

---

## 📊 模式对比

| 特性 | 极速模式 (Flash) | 全功能模式 (Full Feature) |
| :--- | :--- | :--- |
| **身份认证** | **免登录 (No Auth)** | **需登录 (Token)** |
| **处理速度** | 极速 | 标准 |
| **文件大小上限** | 最大 10 MB | 最大 200 MB |
| **文件页数上限** | 最大 20 页 | 最大 600 页 |
| **支持格式** | PDF, 图片, Docx, PPTx, Excel | PDF, 图片, Doc/x, Ppt/x, Html |
| **内容完整度** | 仅文本 (图片、表格、公式显示占位符) | 完整资源 (图片、表格、公式全部保留) |
| **输出格式** | Markdown | MD, Docx, LaTeX, HTML, JSON |

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

### 批量处理
```python
# 边处理边返回结果
for result in client.extract_batch(["a.pdf", "b.pdf", "c.pdf"]):
    print(f"{result.filename}: 已完成")
```

### 网页爬取 (Crawl)
```python
result = client.crawl("https://www.baidu.com")
print(result.markdown)
```

---

## 🤖 AI Agent 自动化集成

本 SDK 设计时充分考虑了 LLM 工作流集成。您可以通过 `result.state` 和 `result.progress` 轻松监控任务状态。

```python
task_id = client.submit("大报告.pdf")
# ... 稍后 ...
result = client.get_task(task_id)
if result.state == "done":
    do_something(result.markdown)
```

---

## 📄 开源协议
本项目采用 Apache-2.0 协议。

## 🔗 相关链接
- [官方网站](https://mineru.net)
- [API 文档](https://mineru.net/docs)
