import os
from typing import Optional
import openai

class LLMClient:
    """Thin OpenAI wrapper. Requires OPENAI_API_KEY in env.

    Optional env: OPENAI_MODEL (defaults to 'gpt-4o-mini')
    """
    def __init__(self):
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError("Set OPENAI_API_KEY in environment to use LLM features")
        openai.api_key = key
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
        resp = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        # Return concatenated assistant content
        choices = resp.get("choices", [])
        if not choices:
            return ""
        return "\n".join([c.get("message", {}).get("content", "") for c in choices])
