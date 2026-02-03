import os
import time
import json
import logging
from typing import Optional, Dict, Any
from functools import wraps
import openai
from .cache import ResponseCache

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Raised when API rate limit is hit."""
    pass


class LLMClient:
    """Enhanced OpenAI wrapper with retry logic, caching, and rate limit awareness.
    
    Features:
    - Automatic retry with exponential backoff for transient errors
    - Response caching to reduce API calls
    - Structured JSON output for consistent parsing
    - Rate limit tracking and awareness
    - Proper timeout handling
    - Token estimation for cost tracking
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        cache_enabled: bool = True,
        cache_ttl_hours: int = 24,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY in environment to use LLM features")

        openai.api_key = key
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Caching
        self.cache = ResponseCache(cache_dir=".cache", ttl_hours=cache_ttl_hours) if cache_enabled else None
        
        # Rate limit tracking
        self.total_tokens_used = 0
        self.total_api_calls = 0
        self.rate_limit_reset_at = None
        
        logger.info(f"LLMClient initialized with model={self.model}, cache_enabled={cache_enabled}")

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars for English)."""
        return len(text) // 4

    def _handle_rate_limit_error(self, retry_after: Optional[int] = None) -> None:
        """Handle rate limit error and set reset time."""
        reset_seconds = retry_after or 60
        self.rate_limit_reset_at = time.time() + reset_seconds
        logger.warning(f"Rate limit hit. Reset at {self.rate_limit_reset_at}")

    def generate(
        self,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 2000,
        use_cache: bool = True,
        structured_json: bool = False,
    ) -> str:
        """Generate text from prompt with retry logic and caching.
        
        Args:
            prompt: The user prompt
            temperature: Sampling temperature (0.0 - 2.0)
            max_tokens: Max output tokens
            use_cache: Whether to use cached responses
            structured_json: If True, request JSON output and validate
            
        Returns:
            Generated text or JSON string
        """
        # Check cache first
        if use_cache and self.cache:
            cached = self.cache.get(prompt, self.model)
            if cached:
                logger.info("Cache hit for prompt")
                return cached

        # Check if we're rate-limited and need to wait
        if self.rate_limit_reset_at and time.time() < self.rate_limit_reset_at:
            wait_time = self.rate_limit_reset_at - time.time()
            logger.info(f"Rate limit in effect. Waiting {wait_time:.1f}s")
            time.sleep(wait_time + 1)
            self.rate_limit_reset_at = None

        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                return self._call_api(
                    prompt, temperature, max_tokens, structured_json, use_cache
                )
            except RateLimitError as e:
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff: 2s, 4s, 8s
                backoff = 2 ** (attempt + 1)
                logger.warning(f"Rate limit hit. Backing off {backoff}s (attempt {attempt + 1}/{self.max_retries})")
                time.sleep(backoff)
            except openai.error.APIError as e:
                if "timeout" in str(e).lower():
                    if attempt == self.max_retries - 1:
                        raise
                    backoff = 2 ** (attempt + 1)
                    logger.warning(f"API timeout. Backing off {backoff}s (attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(backoff)
                else:
                    raise

    def _call_api(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        structured_json: bool,
        use_cache: bool,
    ) -> str:
        """Internal API call with error handling."""
        try:
            # Build the request
            messages = [{"role": "user", "content": prompt}]
            
            # If structured JSON requested, add instruction
            if structured_json:
                messages[0]["content"] += (
                    "\n\nIMPORTANT: Return output as valid JSON only. "
                    "Do not include markdown code blocks or any text outside the JSON."
                )

            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=self.timeout,
            )

            # Extract and validate response
            choices = resp.get("choices", [])
            if not choices:
                raise RuntimeError("No choices in API response")

            content = choices[0].get("message", {}).get("content", "").strip()

            # Track usage
            usage = resp.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            self.total_tokens_used += prompt_tokens + completion_tokens
            self.total_api_calls += 1

            logger.info(
                f"API call successful. "
                f"Tokens: +{prompt_tokens + completion_tokens} (total: {self.total_tokens_used}), "
                f"calls: {self.total_api_calls}"
            )

            # Validate JSON if requested
            if structured_json:
                try:
                    json.loads(content)  # Validate it's valid JSON
                    logger.info("JSON output validated")
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in response: {e}")
                    raise ValueError(f"LLM returned invalid JSON: {str(e)[:200]}")

            # Cache the response
            if use_cache and self.cache:
                self.cache.set(prompt, self.model, content)

            return content

        except openai.error.RateLimitError as e:
            # Extract retry-after header if available
            retry_after = None
            if hasattr(e, "http_response"):
                retry_after = e.http_response.headers.get("retry-after")
            self._handle_rate_limit_error(retry_after)
            raise RateLimitError(str(e)) from e
        except openai.error.APIConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise
        except openai.error.AuthenticationError as e:
            logger.error(f"Authentication error: {e}")
            raise

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit and usage status."""
        is_rate_limited = self.rate_limit_reset_at and time.time() < self.rate_limit_reset_at
        reset_in = None
        if self.rate_limit_reset_at:
            reset_in = max(0, self.rate_limit_reset_at - time.time())

        return {
            "model": self.model,
            "total_api_calls": self.total_api_calls,
            "total_tokens_used": self.total_tokens_used,
            "is_rate_limited": is_rate_limited,
            "rate_limit_resets_in_seconds": reset_in,
        }

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        if self.cache:
            self.cache.clear()
            logger.info("Cache cleared")
