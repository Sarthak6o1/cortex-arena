import httpx

from backend.app.providers.base import ModelInfo, ModelProvider, ProviderError


DEFAULT_NVIDIA_MODELS = [
    "meta/llama-3.1-8b-instruct",
    "mistralai/mistral-7b-instruct-v0.3",
    "google/gemma-2-9b-it",
]


class NvidiaProvider(ModelProvider):
    name = "nvidia"

    def __init__(self, api_key: str, models: list[str] | None = None) -> None:
        self.api_key = api_key.strip()
        self.models = models or DEFAULT_NVIDIA_MODELS

    async def list_models(self) -> list[ModelInfo]:
        if not self.api_key:
            return []
        return [
            ModelInfo(id=model, name=model, provider=self.name, installed=True)
            for model in self.models
        ]

    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        timeout_seconds: int = 180,
    ) -> str:
        if not self.api_key:
            raise ProviderError("NVIDIA provider is not configured.")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 800,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ProviderError(f"NVIDIA generation failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"NVIDIA generation failed: {exc}") from exc

        data = response.json()
        choices = data.get("choices", [])
        if choices:
            return str(choices[0].get("message", {}).get("content", "")).strip()
        return ""
