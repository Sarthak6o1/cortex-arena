from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(RuntimeError):
    """Raised when a model provider cannot complete a request."""


@dataclass(frozen=True)
class ModelInfo:
    id: str
    name: str
    provider: str
    size: str | None = None
    installed: bool = True
    recommended: bool = False


class ModelProvider(ABC):
    name: str

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        raise NotImplementedError

    @abstractmethod
    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        timeout_seconds: int = 180,
    ) -> str:
        raise NotImplementedError
