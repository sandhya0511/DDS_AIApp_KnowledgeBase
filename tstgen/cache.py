import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class ResponseCache:
    """Simple file-based cache for LLM responses with TTL support."""

    def __init__(self, cache_dir: str = ".cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir.mkdir(exist_ok=True)

    def _hash_prompt(self, prompt: str, model: str) -> str:
        """Create a deterministic hash of the prompt and model."""
        content = f"{model}:{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cache_path(self, prompt: str, model: str) -> Path:
        """Get the cache file path for a prompt."""
        fname = self._hash_prompt(prompt, model)
        return self.cache_dir / f"{fname}.json"

    def get(self, prompt: str, model: str) -> Optional[str]:
        """Retrieve cached response if it exists and hasn't expired."""
        path = self._get_cache_path(prompt, model)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check TTL
            cached_at = datetime.fromisoformat(data.get("timestamp"))
            if datetime.now() - cached_at > self.ttl:
                path.unlink()  # Delete expired cache
                return None

            return data.get("response")
        except Exception:
            return None

    def set(self, prompt: str, model: str, response: str) -> None:
        """Store a response in cache with timestamp."""
        path = self._get_cache_path(prompt, model)
        try:
            data = {
                "prompt_hash": self._hash_prompt(prompt, model),
                "model": model,
                "response": response,
                "timestamp": datetime.now().isoformat(),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass  # Silent fail on cache write

    def clear(self) -> None:
        """Clear all cache entries."""
        for f in self.cache_dir.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass
