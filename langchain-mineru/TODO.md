# langchain-mineru — TODOs

该文档记录了当前项目中识别到的待优化项、潜在 Bug 和架构改进建议。

---

## 🔴 高优先级 (High Priority — 必须修复)

### ☐ SDK 发布后更新依赖配置

**现状**: `mineru-open-sdk` 尚未发布到 PyPI，当前通过本地路径 / GitLab Git 仓库安装。

**发布后需要修改的位置**:

1. **`pyproject.toml`** (第 14-16 行): 确认最终 PyPI 包名，替换 `mineru-open-sdk>=0.1.0`
2. **`pyproject.toml`** (第 19-23 行): 删除整个 `[tool.uv.sources]` section
3. **`langchain_mineru/document_loaders/mineru.py`** (第 56-62 行): 将 ImportError 安装提示从 GitLab 地址改为 `pip install mineru-open-sdk`
4. **`README.md` / `README_zh-CN.md`**: 取消注释 `pip install langchain-mineru`，简化安装步骤

### ☐ URL 下载缺少超时和错误处理

**文件**: `langchain_mineru/utils/pdf.py` — `download_url_to_temp_pdf()`

**问题**: 使用 `urllib.request.urlopen(url)` 下载 URL PDF 时，没有设置超时，也没有处理网络异常（连接超时、DNS 解析失败、HTTP 4xx/5xx 等）。大文件下载时 `response.read()` 会一次性读入内存。

**建议**:
- 添加 `timeout` 参数
- 捕获网络异常并包装为友好的错误信息
- 考虑改用 `httpx` 流式下载，与 SDK 保持一致

### ✅ `looks_like_pdf` 判断过于简单

**文件**: `langchain_mineru/utils/pdf.py` — `looks_like_pdf()`

**问题**: 仅通过 `.pdf` 后缀判断。URL PDF 可能不以 `.pdf` 结尾（如 `https://example.com/download?id=123`），导致 `split_pages=True` 时不会进入拆页逻辑。

**建议**:
- URL 场景下增加 Content-Type 检测（`application/pdf`）
- 或在 URL 去除 query string 后再检查后缀

---

## 🟡 中优先级 (Medium Priority — 健壮性增强)

### ☐ split_pages 拆页逐页请求性能问题

**文件**: `langchain_mineru/document_loaders/mineru.py` — `_lazy_load_split_pdf()`

**问题**: 每一页单独调用一次 `flash_extract()`，串行等待，N 页 PDF 需要 N 次 API 往返。对于页数较多的文档，耗时显著。

**建议**:
- 考虑使用 `extract_batch()` / `submit_batch()` 批量提交所有页面
- 或使用线程池并发调用 `flash_extract()`
- 需权衡 flash API 的速率限制

### ☐ 异常类型细化

**文件**: `langchain_mineru/document_loaders/mineru.py`

**问题**: 所有错误都抛出 `ValueError`，用户无法区分"服务端解析失败"、"结果为空"、"文件不存在"等不同类型的异常。

**建议**:
- 定义自定义异常层级（如 `MinerULoaderError` 基类）
- 将 SDK 异常（`TimeoutError`、`FlashPageLimitError` 等）映射为更具语义的 Loader 异常
- 保持与 LangChain 生态的异常处理风格一致

### ☐ 输入校验增强

**文件**: `langchain_mineru/document_loaders/mineru.py` — `_validate()`

**问题**: 当前仅校验空列表。缺少对以下情况的校验：
- `source` 为空字符串
- `language` 为不支持的语言代码
- `pages` 格式不合法（如 `"abc"`）
- `timeout` 为负数或零


---

## 🟢 低优先级 (Low Priority — 体验优化)

### ☐ 添加结构化日志

**现状**: 当前使用 `logging.getLogger(__name__)` 记录关键节点日志（拆页数、当前页码、调用 flash_extract）。

**建议**:
- 补充更多日志：下载 URL 进度、上传文件大小、API 返回耗时
- 在 README 中说明如何启用日志（`logging.basicConfig(level=logging.INFO)`）

### ☐ 支持异步 `alazy_load()`

**现状**: 仅实现同步 `lazy_load()`，在异步 Web 框架（FastAPI 等）中使用会阻塞事件循环。

**建议**: 当 SDK 提供 `AsyncMinerU` 客户端后，实现 `alazy_load()` 方法。LangChain `BaseLoader` 已预留该接口。


### ☐发布到 PyPI

**前置条件**: SDK 发布到 PyPI 后
- 更新所有 TODO 项
- 配置 PyPI 发布流水线
- 发布 `langchain-mineru` 到 PyPI

### ☐ 提交到 LangChain 官方

**前置条件**: PyPI 发布后
- 提交 PR 到 [langchain-community](https://github.com/langchain-ai/langchain) 或 LangChain integrations 目录
- 准备符合 LangChain 标准的文档和测试

---

## 🧪 测试相关

### ✅ 已完成: 基础单元测试

覆盖 18 个测试用例：验证、单源、多源、拆页、错误处理、metadata、flash_extract 调用参数。


### ☐ 补充大文件 / 多页 PDF 测试

- 测试 50+ 页 PDF 触发 flash API 限制时的异常信息
- 测试大量源（100+ 文件）的批量处理性能

### ☐ 补充 SDK 异常传播测试

- Mock `flash_extract()` 抛出 `TimeoutError`，验证 Loader 层是否正确传播
- Mock `flash_extract()` 抛出 `FlashPageLimitError`、`FlashFileTooLargeError`，验证错误信息
- Mock `_create_client()` 中 `MinerU()` 构造失败（无网络时）的行为

### ☐ 集成测试（需要真实 API）

- 使用真实 flash API 端到端测试小型 PDF
- 验证 `set_source("langchain-mineru")` 是否正确携带在请求 header 中
- 标记为 `@pytest.mark.integration`，CI 中可选跳过
