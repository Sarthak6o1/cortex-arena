import json
import re

from backend.app.models import ScoreCard


def parse_scorecard(contestant: str, raw: str) -> ScoreCard:
    data = _extract_json(raw)
    scores = {
        "correctness": _score(data.get("correctness")),
        "creativity": _score(data.get("creativity")),
        "clarity": _score(data.get("clarity")),
        "resilience": _score(data.get("resilience")),
        "usefulness": _score(data.get("usefulness")),
    }
    total = sum(scores.values())
    return ScoreCard(
        contestant=contestant,
        **scores,
        total=total,
        rationale=str(data.get("rationale", raw[:500])).strip(),
    )


def fallback_scorecard(contestant: str, error: str) -> ScoreCard:
    return ScoreCard(
        contestant=contestant,
        correctness=0,
        creativity=0,
        clarity=0,
        resilience=0,
        usefulness=0,
        total=0,
        rationale=f"Judge failed to return a valid score: {error}",
    )


def choose_winner(scorecards: list[ScoreCard]) -> str | None:
    if not scorecards:
        return None
    return max(scorecards, key=lambda score: score.total).contestant


def _extract_json(raw: str) -> dict[str, object]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in judge response.")
    parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise ValueError("Judge response JSON was not an object.")
    return parsed


def _score(value: object) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = 0
    return max(0, min(10, number))
