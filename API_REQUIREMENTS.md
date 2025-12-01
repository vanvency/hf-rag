# API Requirements

## Overview

This RAG system **requires** OpenAI-compatible APIs for both LLM and embedding services. Local models are **not supported**.

## Required APIs

### 1. LLM API (for answer generation)

**Endpoint**: `/v1/chat/completions`

**Required Environment Variables**:
- `OPENAI_API_BASE` - Base URL of your LLM API (e.g., `https://api.openai.com/v1`)
- `OPENAI_API_KEY` - API key for authentication
- `MODEL_NAME` - Model name to use (e.g., `gpt-3.5-turbo`, `gpt-4`)

**Request Format**:
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response Format**:
```json
{
  "choices": [
    {
      "message": {
        "content": "..."
      }
    }
  ]
}
```

### 2. Embedding API (for vector generation)

**Endpoint**: `/v1/embeddings`

**Required Environment Variables**:
- `EMBEDDING_API_BASE` - Base URL of your embedding API (e.g., `https://api.openai.com/v1`)
- `EMBEDDING_API_KEY` - API key (can use `OPENAI_API_KEY` if same service)
- `EMBEDDING_MODEL` - Model name (e.g., `text-embedding-ada-002`)

**Request Format**:
```json
{
  "input": ["text1", "text2", ...],
  "model": "text-embedding-ada-002",
  "encoding_format": "float"
}
```

**Response Format**:
```json
{
  "data": [
    {"embedding": [0.1, 0.2, ...]},
    {"embedding": [0.3, 0.4, ...]}
  ]
}
```

## Configuration

### Example `.env` file:

```env
# LLM API (REQUIRED)
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-3.5-turbo

# Embedding API (REQUIRED)
EMBEDDING_API_BASE=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-...  # Can be same as OPENAI_API_KEY
EMBEDDING_MODEL=text-embedding-ada-002
```

### Using Different Services

You can use different services for LLM and embeddings:

```env
# LLM from OpenAI
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-openai-key
MODEL_NAME=gpt-3.5-turbo

# Embeddings from another service
EMBEDDING_API_BASE=https://api.other-service.com/v1
EMBEDDING_API_KEY=sk-other-key
EMBEDDING_MODEL=embedding-model-name
```

## Error Handling

If APIs are not configured, the system will raise clear error messages:

- **Embedding API not configured**: `ValueError: Embedding API configuration required...`
- **LLM API not configured**: `ValueError: LLM API not configured...`

## Testing API Configuration

You can test your API configuration by:

1. **Check configuration**:
   ```python
   from src.core.config import get_settings
   settings = get_settings()
   print(f"LLM API: {settings.openai_api_base}")
   print(f"Embedding API: {settings.embedding_api_base}")
   ```

2. **Test embedding**:
   ```python
   from src.embeddings.generator import EmbeddingGenerator, EmbeddingConfig
   config = EmbeddingConfig(
       model_name="text-embedding-ada-002",
       api_base="https://api.openai.com/v1",
       api_key="sk-..."
   )
   generator = EmbeddingGenerator(config)
   vector = generator.embed_query("test")
   print(f"Vector shape: {vector.shape}")
   ```

3. **Test LLM**:
   ```python
   from src.services.llm_service import LLMService
   from src.core.config import get_settings
   settings = get_settings()
   llm = LLMService(settings)
   answer = llm.generate_answer("test", "context")
   print(answer)
   ```

## Supported API Providers

Any service that implements OpenAI-compatible API:

- OpenAI
- Azure OpenAI
- LocalAI
- vLLM
- Ollama (with OpenAI compatibility layer)
- Other OpenAI-compatible services

## Notes

- The system does **not** support local models (e.g., sentence-transformers)
- All embedding and LLM calls go through HTTP APIs
- API endpoints are automatically constructed from base URLs
- Self-signed certificates are allowed (for local deployments)
- Request timeouts are set appropriately (60s for LLM, 120s for embeddings)

