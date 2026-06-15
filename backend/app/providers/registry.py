from backend.app.config import Settings
from backend.app.providers.base import ModelProvider, ProviderError
from backend.app.providers.huggingface import HuggingFaceProvider
from backend.app.providers.nvidia import NvidiaProvider
from backend.app.providers.ollama import OllamaProvider


class ProviderRegistry:
    def __init__(self, settings: Settings) -> None:
        self.providers: dict[str, ModelProvider] = {
            "ollama": OllamaProvider(settings.ollama_base_url)
        }
        if settings.huggingface_configured:
            self.providers["huggingface"] = HuggingFaceProvider(settings.huggingface_api_key)
        if settings.nvidia_configured:
            self.providers["nvidia"] = NvidiaProvider(settings.nvidia_api_key)

    def get(self, provider_name: str) -> ModelProvider:
        provider = self.providers.get(provider_name)
        if not provider:
            raise ProviderError(f"Provider {provider_name} is not configured.")
        return provider

    async def list_all_models(self) -> dict[str, list[str]]:
        all_models: dict[str, list[str]] = {}
        for name, provider in self.providers.items():
            try:
                all_models[name] = [model.id for model in await provider.list_models()]
            except ProviderError:
                all_models[name] = []
        return all_models
