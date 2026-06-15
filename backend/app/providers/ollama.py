import json

import httpx

from backend.app.providers.base import ModelInfo, ModelProvider, ProviderError


class OllamaProvider(ModelProvider):
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self.base_url = base_url.rstrip("/")

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError("Ollama is not reachable. Start Ollama and try again.") from exc

        payload = response.json()
        models = []
        for item in payload.get("models", []):
            model_id = item.get("name", "")
            if not model_id:
                continue
            models.append(
                ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider=self.name,
                    size=_format_size(item.get("size")),
                    installed=True,
                )
            )
        return models

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        timeout_seconds: int = 180,
    ) -> str:
        payload: dict[str, object] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ProviderError(f"Ollama generation failed for {model}: {detail}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Ollama generation failed for {model}: {exc}") from exc

        data = response.json()
        return str(data.get("response", "")).strip()

    async def pull_model(self, model: str) -> list[str]:
        """Pull an Ollama model and return progress messages."""
        messages: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/pull",
                    json={"name": model, "stream": True},
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        status = event.get("status")
                        if status:
                            messages.append(str(status))
        except httpx.HTTPError as exc:
            raise ProviderError(f"Could not pull Ollama model {model}: {exc}") from exc
        return messages


def _format_size(size: int | None) -> str | None:
    if not size:
        return None
    gb = size / (1024**3)
    if gb >= 1:
        return f"{gb:.1f} GB"
    mb = size / (1024**2)
    return f"{mb:.0f} MB"
