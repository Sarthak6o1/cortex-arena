from dataclasses import dataclass

from backend.app.config import Settings
from backend.app.providers.base import ModelInfo
from backend.app.providers.ollama import OllamaProvider


RECOMMENDED_OLLAMA_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="llama3.2:3b",
        name="Llama 3.2 3B",
        provider="ollama",
        size="~2.0 GB",
        installed=False,
        recommended=True,
    ),
    ModelInfo(
        id="qwen2.5:3b",
        name="Qwen 2.5 3B",
        provider="ollama",
        size="~1.9 GB",
        installed=False,
        recommended=True,
    ),
    ModelInfo(
        id="phi3:mini",
        name="Phi-3 Mini",
        provider="ollama",
        size="~2.2 GB",
        installed=False,
        recommended=True,
    ),
    ModelInfo(
        id="gemma2:2b",
        name="Gemma 2 2B",
        provider="ollama",
        size="~1.6 GB",
        installed=False,
        recommended=True,
    ),
]


@dataclass(frozen=True)
class SetupStatus:
    ollama_running: bool
    installed_models: list[ModelInfo]
    recommended_models: list[ModelInfo]
    missing_recommended_models: list[ModelInfo]
    provider_status: dict[str, bool]


async def get_setup_status(settings: Settings) -> SetupStatus:
    ollama = OllamaProvider(settings.ollama_base_url)
    ollama_running = await ollama.health()
    installed_models: list[ModelInfo] = []
    if ollama_running:
        installed_models = await ollama.list_models()

    installed_ids = {model.id for model in installed_models}
    recommended_models = [
        ModelInfo(
            id=model.id,
            name=model.name,
            provider=model.provider,
            size=model.size,
            installed=model.id in installed_ids,
            recommended=True,
        )
        for model in RECOMMENDED_OLLAMA_MODELS
    ]
    missing = [model for model in recommended_models if not model.installed]

    return SetupStatus(
        ollama_running=ollama_running,
        installed_models=installed_models,
        recommended_models=recommended_models,
        missing_recommended_models=missing,
        provider_status={
            "ollama": ollama_running,
            "huggingface": settings.huggingface_configured,
            "nvidia": settings.nvidia_configured,
        },
    )


async def pull_recommended_model(settings: Settings, model_id: str) -> list[str]:
    recommended_ids = {model.id for model in RECOMMENDED_OLLAMA_MODELS}
    if model_id not in recommended_ids:
        raise ValueError(f"{model_id} is not in the recommended free model list.")
    ollama = OllamaProvider(settings.ollama_base_url)
    return await ollama.pull_model(model_id)
