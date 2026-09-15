from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "user" | "assistant"
    content: str


class LLMUnavailableError(RuntimeError):
    """Raised when a provider can't be reached (missing key, connection refused, timeout)."""


class LLMClient(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate(self, system: str, messages: list[LLMMessage]) -> str:
        """Returns the assistant's reply text. Raises LLMUnavailableError on failure."""

    @abstractmethod
    def is_available(self) -> bool:
        """Cheap reachability check for the /health endpoint."""
