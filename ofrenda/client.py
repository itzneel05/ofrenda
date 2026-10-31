"""A stdlib-only client for a local Ollama server.

There is deliberately no base-URL option: this tool talks to
``127.0.0.1:11434`` and nowhere else. The model is load-bearing — if it is
missing, ofrenda stops rather than inventing eulogies itself.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "gemma3:4b"


class ModelUnavailable(Exception):
    """The local model (or the server behind it) is not there."""


class OllamaClient:
    def __init__(self, model: str = DEFAULT_MODEL, host: str = OLLAMA_URL,
                 timeout: float = 300.0):
        self.model = model
        self.host = host.rstrip("/")
        self.timeout = timeout

    # -- health ---------------------------------------------------------
    def available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError):
            return False
        return any(m.get("name", "").split(":")[0] == self.model.split(":")[0]
                   for m in data.get("models", []))

    def require(self) -> None:
        if not self.available():
            raise ModelUnavailable(
                f"model '{self.model}' is not available on {self.host} — "
                "start Ollama and `ollama pull gemma3:4b`"
            )

    # -- generate -------------------------------------------------------
    def generate(self, prompt: str, temperature: float = 0.8,
                 num_predict: int = 500) -> str:
        payload = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.host}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            raise ModelUnavailable(f"cannot reach Ollama at {self.host}: {exc}") from exc
        text = (body or {}).get("response", "")
        if not text:
            raise ModelUnavailable("model returned an empty response")
        return text
