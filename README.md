# RAG System with Production-Ready

A production-ready Retrieval-Augmented Generation (RAG) system that enables intelligent file content searching and retrieval based on user queries.

## 🌟 Features

- **Intelligent File Processing**: Automatically reads and parses files from the `data/` folder
- **OCR Integration**: Converts files into markdown-formatted data with OCR capabilities
- **Smart Chunking**: Intelligently chunks markdown data based on document catelog tree for optimal retrieval performance
- **Semantic Search**: Provides accurate file content searching based on natural language queries
- **Production-Ready API**: RESTful backend API built for scalability and reliability
- **Vector Storage**: Efficient embedding storage and similarity search

## 🏗️ Architecture

```

├── data/              # 
│   ├── upload/        # Upload files for processing
│   ├── parse/         # Processed markdown outputs
│   ├── db/            # Data storage
├── src/
│   ├── api/          # API endpoints and routes
│   ├── parsers/      # File parsing and OCR logic
│   ├── chunking/     # Document chunking strategies
│   ├── embeddings/   # Vector embedding generation
│   └── retrieval/    # Search and retrieval logic
└── tests/            # Unit and integration tests
│   ├── docs/         # Test doc files
│   └── docs_qa.xlsx  # Question and ground-trueth answer
```

## 🚀 Core Functions

### 1. File Processing & OCR
- Reads files from the `data/upload` folder
- Supports multiple file formats (PDF, images, DOCX, etc.)
- Parses content using OCR when necessary
- Outputs clean markdown-formatted data to `data/parse/` folder
- Preserves document structure and formatting

### 2. Document Chunking
- Intelligently splits markdown data into semantic chunks
- Configurable chunk size and overlap
- Maintains context across chunk boundaries
- Optimized for embedding and retrieval performance

### 3. Vector Embedding & Storage
- Generates high-quality embeddings for each chunk
- Stores vectors in efficient vector database
- Supports similarity search and semantic matching

### 4. Query Processing & Retrieval
- Accepts natural language queries via API
- Performs semantic search across document chunks
- Returns relevant content with source attribution
- Configurable result ranking and filtering

### 5. Complete Workflow with UI
User able to upload and parsed the file into markdown with extracted catalog, view and edit markdown result and catalog result, chunk markdown result into slices based on catalog, and create embedding vector based on slices, and then user able to search the uploaded file by following step
1. search by fulltext on catalog, if related then just return the full pages of related catalog and lastly use llm api to generate answer to the query
2. if no catalog related, then use vector search on slices embeddings, return related slices and lastly use llm api to generate answer to the query 

## 📋 Requirements

```
python>=3.10
fastapi>=0.104.0
uvicorn>=0.24.0
sentence-transformers>=2.2.2
langchain>=0.1.0
pymupdf>=1.23.0
pillow>=10.0.0
pytesseract>=0.3.10
python-docx>=0.8.11
pydantic>=2.0.0
python-multipart>=0.0.6
numpy>=1.24.0
scikit-learn>=1.3.0
rich>=13.6.0
typer>=0.9.0
pytest>=7.4.0
```

## 🛠️ Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd rag-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies for OCR
# Ubuntu/Debian:
sudo apt-get install tesseract-ocr

# macOS:
brew install tesseract
````

## ⚙️ Configuration

**Important**: This system requires OpenAI-compatible APIs for both LLM and embedding services. Local models are not supported.

Create a `.env` file in the root directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# LLM Configuration (REQUIRED)
OPENAI_API_BASE=https://your-llm-api-endpoint.com/v1
OPENAI_API_KEY=your_llm_api_key_here
MODEL_NAME=gpt-3.5-turbo

# Embedding Configuration (REQUIRED)
# Use EMBEDDING_API_KEY if different from OPENAI_API_KEY, otherwise it will use OPENAI_API_KEY
EMBEDDING_API_BASE=https://your-embedding-api-endpoint.com/v1
EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_MODEL=text-embedding-ada-002

# Vector Store Configuration
VECTOR_STORE_PATH=./data/db/

# Chunking Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# OCR Configuration
OCR_DPI=300
```

**Required Settings**:
- `OPENAI_API_BASE` and `OPENAI_API_KEY` - For LLM answer generation
- `EMBEDDING_API_BASE` and `EMBEDDING_API_KEY` (or `OPENAI_API_KEY`) - For embedding generation

Both APIs must be OpenAI-compatible (support `/v1/chat/completions` and `/v1/embeddings` endpoints).

## 🚀 Usage

### Starting the API Server

```bash
# Development mode with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Processing Files

```bash
# Place your files in the data/ folder
cp your_files/* data/

# Run the processing pipeline
python -m src.process_documents run

# Processed markdown files will be in data/parse/
```

### API Endpoints

#### 1. Query Documents

```bash
POST /api/query
Content-Type: application/json

{
  "query": "What are the main findings?",
  "top_k": 5,
  "threshold": 0.7
}
```

#### 2. Upload and Process File

```bash
POST /api/upload
Content-Type: multipart/form-data

file: <your-file>
```

#### 3. List Processed Documents

```bash
GET /api/documents
```

#### 4. Get Document by ID

```bash
GET /api/documents/{document_id}
```

#### 5. Health Check

```bash
GET /api/health
```

### Python Client Example

```python
import requests

# Query the system
response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "Explain the methodology used in the research",
        "top_k": 3
    }
)

results = response.json()
for result in results["results"]:
    print(f"Score: {result['score']}")
    print(f"Content: {result['content']}")
    print(f"Source: {result['metadata']['source']}")
    print("---")
```

## 🧪 Testing

```bash
pytest
```


## 📁 Project Structure Details

```
.
├── data/
│   ├── upload/             # Input files
│   ├── parse/              # Processed markdown files
│   ├── db/           # Vector database storage
├── src/
│   ├── api/
│   │   ├── routes.py      # API endpoints
│   │   ├── models.py      # Pydantic models
│   │   └── middleware.py  # API middleware
│   ├── core/
│   │   ├── config.py      # Configuration management
│   │   └── logging.py     # Logging setup
│   ├── parsers/
│   │   ├── pdf_parser.py  # PDF processing
│   │   ├── image_parser.py # Image OCR
│   │   └── doc_parser.py   # DOCX processing
│   ├── chunking/
│   │   └── text_splitter.py # Chunking logic
│   ├── embeddings/
│   │   └── generator.py    # Embedding generation
│   ├── retrieval/
│   │   └── search.py       # Search implementation
│   ├── services/
│   │   └── processor.py    # Orchestrates parsing->chunking->embedding
│   └── main.py             # Application entry point
├── tests/
├── .env                    # Environment variables
├── .gitignore
├── requirements.txt
├── README.md
├── Dockerfile
└── docker-compose.yml      # Docker configuration
```

## 🗺️ Roadmap

* [X] File search (file metadata)
* [X] Catelog search (keyword)
* [X] Content Hybrid search (keyword + semantic)
* [X] Real-time document processing
* [X] Advanced analytics dashboard
* [X] Export search results
