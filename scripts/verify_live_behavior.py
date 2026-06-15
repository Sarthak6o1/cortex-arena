"""Live verification that Cortex Arena produces distinct outputs per query and model."""

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.agents import CONTESTANT_SYSTEM, contestant_prompt
from backend.app.config import get_settings
from backend.app.models import ChallengeType, EpisodeRequest, ProviderModel
from backend.app.providers.ollama import OllamaProvider
from backend.app.setup import get_setup_status


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _preview(text: str, limit: int = 180) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


async def _contestant_answer(
    provider: OllamaProvider,
    model: str,
    challenge: str,
    challenge_type: ChallengeType,
) -> dict[str, object]:
    content = await provider.generate(
        model,
        contestant_prompt(challenge, challenge_type),
        system=CONTESTANT_SYSTEM,
        temperature=0.7,
        timeout_seconds=180,
    )
    return {
        "model": model,
        "challenge_type": challenge_type.value,
        "challenge": challenge,
        "digest": _digest(content),
        "preview": _preview(content),
        "length": len(content),
    }


async def main() -> None:
    settings = get_settings()
    status = await get_setup_status(settings)
    if not status.ollama_running:
        raise SystemExit("Ollama is not running. Start Ollama before verification.")

    if not status.installed_models:
        raise SystemExit("No Ollama models installed.")

    provider = OllamaProvider(settings.ollama_base_url)
    model_a = "qwen2.5:3b"
    model_b = "gemma2:2b"

    coding_challenge = (
        "A Python function sometimes returns None instead of an empty list when no records "
        "are found. Explain the likely bug, propose a fix, and include a minimal test."
    )
    security_challenge = (
        "Review a simple email/password login design for a SaaS app. Find security risks "
        "and propose practical mitigations for a small team."
    )

    query_cases = await asyncio.gather(
        _contestant_answer(provider, model_a, coding_challenge, ChallengeType.coding),
        _contestant_answer(provider, model_a, security_challenge, ChallengeType.security),
    )

    model_cases = await asyncio.gather(
        _contestant_answer(provider, model_a, coding_challenge, ChallengeType.coding),
        _contestant_answer(provider, model_b, coding_challenge, ChallengeType.coding),
    )

    query_distinct = query_cases[0]["digest"] != query_cases[1]["digest"]
    model_distinct = model_cases[0]["digest"] != model_cases[1]["digest"]

    report = {
        "project": "Cortex Arena",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "ollama_running": status.ollama_running,
        "installed_models": [model.id for model in status.installed_models],
        "tests": {
            "different_queries_same_model": {
                "description": "Same model, different challenge prompts must produce different answers.",
                "model": model_a,
                "cases": query_cases,
                "distinct_outputs": query_distinct,
                "passed": query_distinct,
            },
            "same_query_different_models": {
                "description": "Same challenge, different models must produce different answers.",
                "challenge_type": ChallengeType.coding.value,
                "cases": model_cases,
                "distinct_outputs": model_distinct,
                "passed": model_distinct,
            },
        },
        "overall_passed": query_distinct and model_distinct,
    }

    output_path = Path("docs/verification_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    if not report["overall_passed"]:
        raise SystemExit("Live verification failed: outputs were not distinct.")


if __name__ == "__main__":
    asyncio.run(main())
