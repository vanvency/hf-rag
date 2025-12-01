# 启动服务器并查看日志

## ✅ 已验证：日志系统正常工作

测试结果显示日志中间件正常工作，所有API调用都会被记录。

## 🚀 启动方式

### 方法 1：使用启动脚本（推荐）

```bash
python start_server.py
```

这个脚本会自动配置日志系统，确保所有API调用都有日志输出。

### 方法 2：使用 uvicorn 命令（必须添加 --no-access-log）

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --no-access-log
```

**重要**：必须添加 `--no-access-log` 参数，否则 uvicorn 的默认访问日志会干扰我们的自定义日志。

### 方法 3：使用 run_server.py

```bash
python run_server.py
```

## 📋 日志格式

启动服务器后，所有API调用都会在终端显示日志，格式如下：

### 成功请求（2xx）
```
[时间] INFO     ✓ GET /api/documents [IP: 127.0.0.1] - 15.23ms - 200, 1234 bytes
[时间] INFO     ✓ POST /api/upload [File Upload] [IP: 127.0.0.1] - 125.45ms - 200
[时间] INFO     ✓ POST /api/query [JSON] [IP: 127.0.0.1] - 45.67ms - 200
```

### 错误请求（4xx）
```
[时间] WARNING  ✗ GET /api/documents/123 [IP: 127.0.0.1] - 5.12ms - 404 [HTTPException: Document not found]
```

### 服务器错误（5xx）
```
[时间] ERROR    ✗ POST /api/upload [File Upload] [IP: 127.0.0.1] - 50.23ms - 500 [Exception: ...]
```

## 🔍 日志包含的信息

- **请求方法**：GET, POST, PUT, DELETE 等
- **请求路径**：完整的URL路径
- **查询参数**：如果有的话
- **请求类型**：[File Upload] 或 [JSON]
- **客户端IP**：请求来源IP地址
- **响应时间**：毫秒级精度
- **状态码**：HTTP响应状态码
- **响应大小**：响应内容的字节数（如果有）

## ⚠️ 如果看不到日志

1. **检查启动命令**：确保使用了 `--no-access-log` 参数或使用 `start_server.py`
2. **检查终端**：确保在运行服务器的终端窗口中查看
3. **检查日志级别**：确保日志级别设置为 INFO 或更低
4. **测试日志**：运行 `python test_middleware_logging.py` 验证日志系统

## 📝 测试日志输出

运行以下命令测试日志是否正常工作：

```bash
python test_logging.py
```

这会发送多个API请求，你应该能在服务器终端看到相应的日志输出。

