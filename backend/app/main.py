from fastapi import FastAPI, HTTPException

from backend.app.arena import ArenaRunner
from backend.app.branding import APP_NAME
from backend.app.config import get_settings
from backend.app.models import EpisodeRequest, EpisodeResult
from backend.app.providers.registry import ProviderRegistry
from backend.app.setup import get_setup_status, pull_recommended_model
from backend.app.storage import EpisodeStore

app = FastAPI(title=APP_NAME, version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/setup")
async def setup_status() -> dict[str, object]:
    settings = get_settings()
    status = await get_setup_status(settings)
    return {
        "ollama_running": status.ollama_running,
        "installed_models": [model.__dict__ for model in status.installed_models],
        "recommended_models": [model.__dict__ for model in status.recommended_models],
        "missing_recommended_models": [
            model.__dict__ for model in status.missing_recommended_models
        ],
        "provider_status": status.provider_status,
    }


@app.post("/setup/pull/{model_id}")
async def pull_model(model_id: str) -> dict[str, object]:
    try:
        messages = await pull_recommended_model(get_settings(), model_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"model": model_id, "messages": messages}


@app.get("/models")
async def list_models() -> dict[str, list[str]]:
    registry = ProviderRegistry(get_settings())
    return await registry.list_all_models()


@app.post("/episodes", response_model=EpisodeResult)
async def run_episode(request: EpisodeRequest) -> EpisodeResult:
    runner = ArenaRunner(get_settings())
    try:
        episode = await runner.run_episode(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    EpisodeStore(get_settings().database_path).save_episode(episode)
    return episode


@app.get("/episodes")
async def list_episodes(limit: int = 20) -> list[dict[str, object]]:
    return EpisodeStore(get_settings().database_path).list_episodes(limit)


@app.get("/episodes/{episode_id}", response_model=EpisodeResult)
async def get_episode(episode_id: str) -> EpisodeResult:
    episode = EpisodeStore(get_settings().database_path).get_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@app.get("/leaderboard")
async def leaderboard(limit: int = 20) -> list[dict[str, object]]:
    return EpisodeStore(get_settings().database_path).leaderboard(limit)


@app.get("/reinforcement/q-table")
async def q_table(limit: int = 100) -> list[dict[str, object]]:
    return EpisodeStore(get_settings().database_path).q_table(limit)
