# 启动指南

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）：

```env
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_API_BASE=your_llm_api_base
OPENAI_API_KEY=your_llm_api_key
MODEL_NAME=gpt-3.5-turbo
VECTOR_STORE_PATH=./data/db/
EMBEDDING_API_BASE=your_embedding_api_base
EMBEDDING_API_KEY=your_embedding_api_key
EMBEDDING_MODEL=atom
CHUNK_SIZE=800
CHUNK_OVERLAP=200
OCR_DPI=300
```

### 3. 启动服务器

```bash
python run_server.py
```

或者使用 uvicorn 直接启动：

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问 Web 界面

打开浏览器访问：http://localhost:8000

## 功能说明

### 📤 上传文档
- 支持拖拽或点击上传
- 支持 PDF, DOCX, TXT, MD, 图片等格式
- 自动解析为 Markdown 并提取目录结构

### 📋 文档管理
- 查看所有已上传的文档
- 查看/编辑 Markdown 内容
- 查看目录结构
- 查看文档分块
- 保存编辑后自动重新分块和生成向量

### 🔍 智能搜索
- **两步搜索策略**：
  1. 首先在目录中进行全文搜索
  2. 如果未找到，则使用向量语义搜索
- **AI 回答生成**：基于检索到的内容，使用 LLM API 生成答案

## API 端点

- `GET /` - Web 前端界面
- `POST /api/upload` - 上传文档
- `GET /api/documents` - 获取文档列表
- `GET /api/documents/{id}/parsed` - 获取解析后的 Markdown
- `PUT /api/documents/{id}/parsed` - 更新 Markdown 内容
- `GET /api/documents/{id}/catalog` - 获取目录结构
- `GET /api/documents/{id}/chunks` - 获取文档分块
- `POST /api/query/smart` - 智能搜索（目录优先，向量备选）
- `POST /api/query` - 传统向量搜索
- `GET /api/health` - 健康检查

## 技术架构

1. **目录提取** (`src/chunking/catalog_extractor.py`)
   - 从 Markdown 中提取标题层级结构
   - 生成目录树

2. **目录分块** (`src/chunking/catalog_splitter.py`)
   - 基于目录结构进行智能分块
   - 保持章节完整性

3. **向量存储** (`src/retrieval/search.py`)
   - 支持目录全文搜索
   - 支持向量相似度搜索

4. **LLM 服务** (`src/services/llm_service.py`)
   - 集成 OpenAI 兼容 API
   - 生成基于上下文的答案

5. **Web 前端** (`src/web/index.html`)
   - 现代化的响应式界面
   - 完整的文档管理功能
   - 实时搜索和编辑

## 注意事项

- 确保已安装 Tesseract OCR（如果使用图片 OCR 功能）
- LLM API 和 Embedding API 需要正确配置
- 首次运行会自动创建必要的目录结构

