# MinerU Open SDK - TODOs

该文档记录了当前 SDK 中识别到的待优化项、潜在 Bug 和架构改进建议。

## 🔴 高优先级 (High Priority - 必须修复)

- [x] **修复 `submit_batch` 混合源逻辑错误**: 
    - ✅ **已完成**: 修正了逻辑判断，增加了 `ValueError` 防御性检查，避免了路径解析引发的 `OSError` 崩溃。API接口不支持混合，SDK是否要捏合设计中
- [ ] **增强 `_api.py` 的异常处理**:
    - 在 `_handle` 方法中，处理 `resp.json()` 可能抛出的 `JSONDecodeError`（如服务器返回 502/504 HTML 页面时）。
    - 统一将非预期的响应包装为 SDK 自定义异常。
- [ ] **优化大文件上传逻辑**:
    - 替换 `Path.read_bytes()` 为流式读取，避免在上传数 GB 的文件时造成内存溢出 (OOM)。

## 🟡 中优先级 (Medium Priority - 健壮性增强)

- [ ] **设计混合源异步提交架构 (需设计 🚀)**:
    - **现状**: `submit_batch` 目前对混合源采取报错处理（`ValueError`）。
    - **目标**: 需要设计一种优雅的机制来支持在一个异步调用中处理混合任务（URL + 本地文件）。
    - **挑战**: `submit_batch` 函数签名仅返回单个 `str` (Batch ID)，而底层 API 将其分为两个不同的提交路径。需权衡是返回复合 ID、列表还是推动后端 API 合并。
- [ ] **改进 Zip 解析编码处理**:
    - 在 `src/mineru/_zip.py` 中，为 `decode("utf-8")` 添加错误处理（如 `errors="replace"`）或实现编码自动检测。
- [ ] **优化 `parse_zip` 内容提取**:
    - 解决同后缀文件覆盖的问题。如果 Zip 中存在多个 `.md`，应考虑合并或保留所有内容。
- [ ] **增强模型推断逻辑 (`_infer_model`)**:
    - 改进对不带后缀的 URL 的识别，不仅仅依赖文件扩展名来判断是否为 HTML 模型。
- [ ] **统一 HTTP 客户端使用**:
    - 修改 `ApiClient.put_file` 和 `download` 方法，使其利用 `self._client` (httpx.Client) 而不是顶层函数，以复用连接池。

## 🟢 低优先级 (Low Priority - 性能与体验优化)

- [ ] **实现并发上传**:
    - 在 `_upload_and_submit` 中，使用线程池或异步任务并行上传多个本地文件，缩短批量处理的等待时间。
- [ ] **细化超时控制**:
    - 将用户传入的 `timeout` 与底层 HTTP 请求的 `connect`、`read` 超时进行更合理的关联。
- [ ] **异步客户端支持 (AsyncMinerU)**:
    - 考虑提供基于 `httpx.AsyncClient` 的原生异步客户端，避免在异步环境中使用 `time.sleep`。
- [ ] **完善日志记录**:
    - 在关键路径（提交任务、上传文件、解析 Zip）添加 `logging`，方便用户调试。

## 🧪 测试相关

- [x] **编写混合源回归测试**:
    - ✅ **已完成**: 编写了 `reproduce_bug.py`，涵盖了混合源报错、纯 URL、纯文件及空列表的 Mock 测试。
- [ ] **模拟大文件上传测试**: 验证内存占用是否保持在合理范围内。
- [ ] **Mock 错误响应测试**: 模拟服务器返回非 JSON 数据的情况，确保 SDK 不会崩溃。
