import httpx

from backend.app.providers.base import ModelInfo, ModelProvider, ProviderError


DEFAULT_HF_MODELS = [
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen2.5-7B-Instruct",
    "HuggingFaceH4/zephyr-7b-beta",
]


class HuggingFaceProvider(ModelProvider):
    name = "huggingface"

    def __init__(self, api_key: str, models: list[str] | None = None) -> None:
        self.api_key = api_key.strip()
        self.models = models or DEFAULT_HF_MODELS

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
            raise ProviderError("Hugging Face provider is not configured.")

        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "return_full_text": False,
                "max_new_tokens": 800,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{model}",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            raise ProviderError(f"Hugging Face generation failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"Hugging Face generation failed: {exc}") from exc

        data = response.json()
        if isinstance(data, list) and data:
            return str(data[0].get("generated_text", "")).strip()
        if isinstance(data, dict):
            return str(data.get("generated_text", "")).strip()
        return str(data).strip()
