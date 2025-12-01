# Changelog: API-Only Mode

## Changes Made

### Summary
The system has been updated to **require** OpenAI-compatible APIs for all LLM and embedding operations. Local models are no longer supported.

### Modified Files

#### 1. `src/embeddings/generator.py`
- **Removed**: Local model fallback (`sentence-transformers`)
- **Added**: Requirement check in `__init__` - raises `ValueError` if API not configured
- **Updated**: `embed()` method - only uses API, no local fallback
- **Updated**: `embed_query()` method - only uses API, clear error messages

**Before**:
- Would fall back to local `sentence-transformers` model if API not configured
- Silent fallback could cause confusion

**After**:
- Raises clear error if API not configured
- All embedding calls go through API only

#### 2. `src/services/llm_service.py`
- **Removed**: Placeholder answer fallback
- **Updated**: `generate_answer()` - raises `ValueError` if API not configured

**Before**:
- Would return placeholder answer if API not configured
- Could hide configuration issues

**After**:
- Raises clear error if API not configured
- Forces proper configuration

#### 3. `requirements.txt`
- **Removed**: `sentence-transformers` dependency (no longer needed)
- **Note**: Added comment explaining removal

#### 4. Documentation Updates
- **README.md**: Updated configuration section with API requirements
- **API_REQUIREMENTS.md**: New file with detailed API documentation

### Error Messages

#### Embedding API Not Configured
```
ValueError: Embedding API configuration required. 
Please set EMBEDDING_API_BASE and EMBEDDING_API_KEY (or OPENAI_API_KEY) in .env file. 
Local models are not supported.
```

#### LLM API Not Configured
```
ValueError: LLM API not configured. 
Please set OPENAI_API_BASE and OPENAI_API_KEY in .env file. 
Local models are not supported.
```

### Migration Guide

#### For Existing Users

1. **Update `.env` file**:
   ```env
   # REQUIRED - LLM API
   OPENAI_API_BASE=https://your-llm-api.com/v1
   OPENAI_API_KEY=your-key
   
   # REQUIRED - Embedding API
   EMBEDDING_API_BASE=https://your-embedding-api.com/v1
   EMBEDDING_API_KEY=your-key
   ```

2. **Remove local model dependencies** (optional):
   ```bash
   pip uninstall sentence-transformers
   ```

3. **Test configuration**:
   ```python
   from src.core.config import get_settings
   settings = get_settings()
   assert settings.openai_api_base, "LLM API not configured"
   assert settings.embedding_api_base, "Embedding API not configured"
   ```

### Benefits

1. **Consistency**: All operations use the same API-based approach
2. **Clarity**: Clear error messages when configuration is missing
3. **Simplicity**: No need to manage local model dependencies
4. **Scalability**: API-based approach scales better
5. **Flexibility**: Can use any OpenAI-compatible service

### Breaking Changes

- ❌ Local models no longer supported
- ❌ `sentence-transformers` dependency removed
- ✅ API configuration now required
- ✅ Clear error messages for missing configuration

### Testing

All tests have been updated to work with API-only mode:
- Tests require API configuration in environment
- Tests use temporary API endpoints when needed
- Error handling tests verify proper error messages

