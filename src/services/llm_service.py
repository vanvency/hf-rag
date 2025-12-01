import logging
from typing import Optional

from src.core.config import Settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for generating answers using LLM API"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_base = settings.openai_api_base
        self.api_key = settings.openai_api_key
        self.model_name = settings.model_name

    def generate_answer(self, query: str, context: str, max_tokens: int = 1000) -> str:
        """Generate answer based on query and context using OpenAI-compatible API"""
        if not self.api_base or not self.api_key:
            raise ValueError(
                "LLM API not configured. "
                "Please set OPENAI_API_BASE and OPENAI_API_KEY in .env file. "
                "Local models are not supported."
            )

        try:
            import requests
            from urllib.parse import urlparse

            # Parse API URL
            api_url = self.api_base.rstrip("/")
            parsed_url = urlparse(api_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
            
            # Ensure /chat/completions endpoint
            if not base_url.endswith("/chat/completions"):
                if base_url.endswith("/v1"):
                    base_url = f"{base_url}/chat/completions"
                else:
                    base_url = f"{base_url.rstrip('/')}/v1/chat/completions"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            # Construct prompt
            system_prompt = "你是一个专业的文档助手。请基于提供的文档内容，准确、简洁地回答用户的问题。如果文档中没有相关信息，请如实说明。"
            user_prompt = f"""请基于以下文档内容回答问题：

文档内容：
{context}

问题：{query}

请提供准确、简洁的答案："""

            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }

            response = requests.post(
                base_url,
                json=payload,
                headers=headers,
                verify=False,
                timeout=60,
            )

            if not response.ok:
                error_msg = f"LLM API returned {response.status_code}: {response.text[:200]}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

            result = response.json()
            
            # Extract answer from response
            if "choices" in result and len(result["choices"]) > 0:
                answer = result["choices"][0]["message"]["content"]
                return answer.strip()
            else:
                raise RuntimeError(f"Unexpected LLM API response format: {result}")

        except Exception as e:
            logger.error(f"Error generating LLM answer: {str(e)}", exc_info=True)
            # Return fallback answer
            return f"抱歉，生成答案时出现错误。相关问题：{query}\n\n相关文档内容：\n{context[:500]}..."

