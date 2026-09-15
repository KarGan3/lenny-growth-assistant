import httpx

from app.llm.base import LLMClient, LLMMessage, LLMUnavailableError


class OllamaClient(LLMClient):
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, timeout: int = 60, max_output_tokens: int = 512):
        self.model_name = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_output_tokens = max_output_tokens

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self._base_url}/api/tags", timeout=3)
            if r.status_code != 200:
                return False
            wanted = self.model_name if ":" in self.model_name else f"{self.model_name}:latest"
            return any(m.get("name") == wanted or m.get("model") == wanted for m in r.json().get("models", []))
        except Exception:
            return False

    def generate(self, system: str, messages: list[LLMMessage]) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "system", "content": system}]
            + [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"num_predict": self._max_output_tokens},
        }
        try:
            with httpx.Client(timeout=httpx.Timeout(self._timeout, connect=3)) as client:
                r = client.post(f"{self._base_url}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                return data.get("message", {}).get("content", "")
        except httpx.ConnectError as e:
            raise LLMUnavailableError(
                f"Could not reach Ollama at {self._base_url} — is `ollama serve` running "
                f"and has `ollama pull {self.model_name}` been run?"
            ) from e
        except Exception as e:  # noqa: BLE001
            raise LLMUnavailableError(f"Ollama request failed: {e}") from e
