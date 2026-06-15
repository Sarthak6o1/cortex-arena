"""Run judged episodes across multiple challenges to prove winners vary by query type."""

import asyncio
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.arena import ArenaRunner
from backend.app.config import get_settings
from backend.app.models import ChallengeType, EpisodeRequest, ProviderModel
from backend.app.setup import get_setup_status

CHALLENGES_PATH = ROOT / "examples" / "challenges" / "mixed_challenges.json"
OUTPUT_PATH = ROOT / "docs" / "benchmark_results.json"

CONTESTANTS = [
    ProviderModel(model="qwen2.5:3b"),
    ProviderModel(model="gemma2:2b"),
    ProviderModel(model="phi3:mini"),
]
JUDGE_MODEL = ProviderModel(model="llama3.2:3b")
REQUIRED_MODELS = {"qwen2.5:3b", "gemma2:2b", "phi3:mini", "llama3.2:3b"}


def _load_challenges() -> list[dict[str, str]]:
    raw = json.loads(CHALLENGES_PATH.read_text(encoding="utf-8"))
    return [
        {
            "title": item["title"],
            "challenge_type": ChallengeType(item["type"]),
            "challenge": item["challenge"],
        }
        for item in raw
    ]


async def _run_episode(runner: ArenaRunner, challenge: dict[str, object]) -> dict[str, object]:
    request = EpisodeRequest(
        title=str(challenge["title"]),
        challenge=str(challenge["challenge"]),
        challenge_type=challenge["challenge_type"],
        contestants=CONTESTANTS,
        judge_model=JUDGE_MODEL,
        use_reinforcement=False,
        use_goal_engine=True,
        use_utility_engine=True,
    )
    result = await runner.run_episode(request)
    scores = []
    for contestant_result in result.contestants:
        score = contestant_result.score
        scores.append(
            {
                "model": contestant_result.contestant.model,
                "total": score.total if score else 0,
                "correctness": score.correctness if score else 0,
                "creativity": score.creativity if score else 0,
                "clarity": score.clarity if score else 0,
                "resilience": score.resilience if score else 0,
                "usefulness": score.usefulness if score else 0,
                "rationale": score.rationale if score else "",
            }
        )
    scores.sort(key=lambda row: row["total"], reverse=True)
    winner_model = result.winner.split(":", 1)[-1] if result.winner else None
    return {
        "title": challenge["title"],
        "challenge_type": challenge["challenge_type"].value,
        "winner": winner_model,
        "winner_label": result.winner,
        "scores": scores,
        "episode_id": result.id,
    }


async def main() -> None:
    settings = get_settings()
    status = await get_setup_status(settings)
    if not status.ollama_running:
        raise SystemExit("Ollama is not running. Start Ollama before running the benchmark.")

    installed = {model.id for model in status.installed_models}
    missing = sorted(REQUIRED_MODELS - installed)
    if missing:
        raise SystemExit(
            "Missing required Ollama models: "
            + ", ".join(missing)
            + ". Run: python -m backend.app.cli --pull-recommended"
        )

    runner = ArenaRunner(settings)
    challenges = _load_challenges()
    episodes: list[dict[str, object]] = []

    for index, challenge in enumerate(challenges, start=1):
        print(f"[{index}/{len(challenges)}] Running: {challenge['title']} ({challenge['challenge_type'].value})")
        episodes.append(await _run_episode(runner, challenge))

    winners = [episode["winner"] for episode in episodes if episode["winner"]]
    win_counts = Counter(winners)
    unique_winners = len(win_counts)
    winners_vary = unique_winners > 1

    report = {
        "project": "Cortex Arena",
        "benchmark_at": datetime.now(timezone.utc).isoformat(),
        "judge_model": JUDGE_MODEL.model,
        "contestants": [contestant.model for contestant in CONTESTANTS],
        "challenges_run": len(episodes),
        "episodes": episodes,
        "summary": {
            "wins_by_model": dict(win_counts),
            "unique_winners": unique_winners,
            "winners_vary_by_query": winners_vary,
            "passed": winners_vary and len(episodes) >= 3,
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))

    if not report["summary"]["passed"]:
        raise SystemExit("Benchmark failed: winners did not vary across challenge types.")


if __name__ == "__main__":
    asyncio.run(main())
