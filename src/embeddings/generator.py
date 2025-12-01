from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional

import numpy as np


@dataclass
class EmbeddingConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    api_base: Optional[str] = None
    api_key: Optional[str] = None

    @property
    def use_api(self) -> bool:
        """Check if API-based embeddings should be used."""
        return bool(self.api_base) and bool(self.api_key)


class EmbeddingGenerator:
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        # Require API configuration - no local models
        if not config.use_api:
            raise ValueError(
                "Embedding API configuration required. "
                "Please set EMBEDDING_API_BASE and EMBEDDING_API_KEY (or OPENAI_API_KEY) in .env file. "
                "Local models are not supported."
            )

    def _embed_via_api(self, texts: List[str], retry_count: int = 0) -> np.ndarray:
        """Generate embeddings using OpenAI-compatible API."""
        import requests
        from urllib.parse import urlparse, parse_qs
        import logging

        logger = logging.getLogger(__name__)
        
        # Clean and validate texts
        MAX_TEXT_LENGTH = 8000  # Limit text length to avoid API errors
        cleaned_texts = []
        for text in texts:
            # Remove control characters except newlines and tabs
            cleaned = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
            # Truncate if too long
            if len(cleaned) > MAX_TEXT_LENGTH:
                logger.warning(f"Truncating text from {len(cleaned)} to {MAX_TEXT_LENGTH} characters")
                cleaned = cleaned[:MAX_TEXT_LENGTH]
            cleaned_texts.append(cleaned)
        
        # Parse the API base URL and extract query parameters
        api_url = self.config.api_base.rstrip("/")
        
        # Extract query parameters from the URL if present
        parsed_url = urlparse(api_url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
        
        # Ensure /embeddings endpoint
        if not base_url.endswith("/embeddings"):
            if base_url.endswith("/v1"):
                base_url = f"{base_url}/embeddings"
            else:
                base_url = f"{base_url.rstrip('/')}/embeddings"
        
        # Extract query parameters
        query_params = {}
        if parsed_url.query:
            query_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed_url.query).items()}

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }

        # Prepare the request payload
        payload = {
            "input": cleaned_texts,
            "model": self.config.model_name,
            "encoding_format": "float",
        }

        try:
            logger.debug(f"Requesting embeddings for {len(cleaned_texts)} texts (attempt {retry_count + 1})")
            response = requests.post(
                base_url,
                json=payload,
                headers=headers,
                params=query_params,
                verify=False,  # Allow self-signed certificates
                timeout=120,  # Increased timeout for large requests
            )
            
            if not response.ok:
                error_detail = response.text[:1000] if response.text else "No error details"
                error_msg = (
                    f"API returned {response.status_code} for {len(cleaned_texts)} texts. "
                    f"Error: {error_detail}"
                )
                
                # Log request details for debugging
                logger.error(f"API request failed: {error_msg}")
                logger.debug(f"Request URL: {base_url}")
                logger.debug(f"Request payload size: {len(str(payload))} chars")
                logger.debug(f"Text lengths: {[len(t) for t in cleaned_texts]}")
                
                raise RuntimeError(error_msg)
            
            result = response.json()
            
            # Extract embeddings from the response
            # OpenAI format: {"data": [{"embedding": [...]}, ...]}
            if "data" in result:
                vectors = [item["embedding"] for item in result["data"]]
            elif "embeddings" in result:
                # Alternative format
                vectors = result["embeddings"]
            else:
                # Direct array format
                vectors = result if isinstance(result, list) else result.get("embeddings", [])
            
            if len(vectors) != len(cleaned_texts):
                raise RuntimeError(
                    f"Expected {len(cleaned_texts)} embeddings but got {len(vectors)}"
                )
            
            logger.debug(f"Successfully generated {len(vectors)} embeddings")
            return np.asarray(vectors, dtype=np.float32)
            
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                f"API request timed out after 120s for {len(cleaned_texts)} texts"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Network error while requesting embeddings: {str(exc)}"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to generate embeddings via API: {str(exc)}"
            ) from exc

    def embed(self, texts: Iterable[str]) -> np.ndarray:
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        texts_list = list(texts)
        
        if self.config.use_api:
            # Batch API requests to avoid overwhelming the server
            # Start with smaller batches and reduce if errors occur
            batch_size = 3  # Process 3 chunks at a time for better reliability
            all_vectors = []
            failed_indices = []
            
            for i in range(0, len(texts_list), batch_size):
                batch = texts_list[i:i + batch_size]
                batch_indices = list(range(i, min(i + batch_size, len(texts_list))))
                
                # Retry logic for API calls with exponential backoff
                max_retries = 5
                batch_success = False
                
                for attempt in range(max_retries):
                    try:
                        batch_vectors = self._embed_via_api(batch, retry_count=attempt)
                        all_vectors.append(batch_vectors)
                        batch_success = True
                        logger.info(f"Successfully processed batch {i//batch_size + 1} ({len(batch)} texts)")
                        break
                    except RuntimeError as e:
                        error_msg = str(e)
                        # If it's a 500 error and we have multiple texts, try individual texts
                        if "500" in error_msg and len(batch) > 1 and attempt >= 2:
                            logger.warning(
                                f"Batch failed, trying individual texts. Error: {error_msg[:200]}"
                            )
                            # Try processing texts one by one
                            individual_vectors = []
                            for idx, text in zip(batch_indices, batch):
                                try:
                                    single_vector = self._embed_via_api([text], retry_count=0)
                                    individual_vectors.append(single_vector[0])
                                    time.sleep(0.5)  # Small delay between individual requests
                                except Exception as single_exc:
                                    logger.error(
                                        f"Failed to process text at index {idx}: {str(single_exc)[:200]}"
                                    )
                                    failed_indices.append(idx)
                                    # Create a zero vector as placeholder
                                    individual_vectors.append(np.zeros(1024, dtype=np.float32))
                            
                            if individual_vectors:
                                all_vectors.append(np.vstack(individual_vectors))
                                batch_success = True
                                break
                        
                        if attempt == max_retries - 1:
                            logger.error(
                                f"Failed to process batch after {max_retries} attempts: {error_msg[:200]}"
                            )
                            failed_indices.extend(batch_indices)
                            # Create zero vectors as placeholders for failed texts
                            placeholder_vectors = np.zeros((len(batch), 1024), dtype=np.float32)
                            all_vectors.append(placeholder_vectors)
                        else:
                            # Exponential backoff with jitter
                            wait_time = (2 ** attempt) + (attempt * 0.5)
                            logger.warning(
                                f"Retry {attempt + 1}/{max_retries} after {wait_time:.1f}s"
                            )
                            time.sleep(wait_time)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"Unexpected error processing batch: {str(e)[:200]}")
                            failed_indices.extend(batch_indices)
                            placeholder_vectors = np.zeros((len(batch), 1024), dtype=np.float32)
                            all_vectors.append(placeholder_vectors)
                        else:
                            wait_time = (2 ** attempt) + (attempt * 0.5)
                            time.sleep(wait_time)
                
                # Add delay between batches to avoid rate limiting
                if i + batch_size < len(texts_list):
                    time.sleep(0.3)
            
            if failed_indices:
                logger.warning(
                    f"Warning: {len(failed_indices)} texts failed to generate embeddings "
                    f"(indices: {failed_indices[:10]}{'...' if len(failed_indices) > 10 else ''})"
                )
            
            if all_vectors:
                return np.vstack(all_vectors)
            else:
                raise RuntimeError("Failed to generate any embeddings")
        else:
            # This should never be reached due to __init__ check, but keep for safety
            raise RuntimeError(
                "Embedding API not configured. "
                "Please set EMBEDDING_API_BASE and EMBEDDING_API_KEY in .env file."
            )

    def embed_query(self, text: str) -> np.ndarray:
        """Generate embedding for a single query text using API."""
        if not self.config.use_api:
            raise RuntimeError(
                "Embedding API not configured. "
                "Please set EMBEDDING_API_BASE and EMBEDDING_API_KEY in .env file."
            )
        
        try:
            vecs = self._embed_via_api([text], retry_count=0)
            return np.asarray(vecs[0], dtype=np.float32)
        except Exception as e:
            raise RuntimeError(
                f"Failed to generate query embedding via API: {str(e)}"
            ) from e

