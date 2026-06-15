import pytest

from backend.app.agentic.goals import GoalBasedEngine
from backend.app.agentic.utility import UtilityEngine
from backend.app.models import (
    AgentTurn,
    ChallengeType,
    ContestantResult,
    EpisodeResult,
    ProviderModel,
    ScoreCard,
)
from backend.app.reinforcement import QLearningEngine
from backend.app.storage import EpisodeStore


def test_q_learning_update_uses_bellman_rule(tmp_path):
    store = EpisodeStore(tmp_path / "arena.sqlite3")
    engine = QLearningEngine(store)

    signal = engine.update(
        state="coding:contestant",
        action="ollama:qwen2.5:3b",
        reward=0.8,
        next_state="coding:winner",
    )

    assert signal.previous_q == 0
    assert signal.next_best_q == 0
    assert signal.updated_q == 0.28
    assert store.get_q_value("coding:contestant", "ollama:qwen2.5:3b") == pytest.approx(0.28)


def test_utility_engine_prefers_high_q_model(tmp_path):
    store = EpisodeStore(tmp_path / "arena.sqlite3")
    store.set_q_value("security:judge", "ollama:qwen2.5:3b", 0.7)
    store.set_q_value("security:judge", "ollama:gemma2:2b", 0.1)

    selected, trace = UtilityEngine(store).decide(
        phase="judge",
        state="security:judge",
        candidates=[
            ProviderModel(model="qwen2.5:3b"),
            ProviderModel(model="gemma2:2b"),
        ],
    )

    assert selected.label == "ollama:qwen2.5:3b"
    assert trace.algorithm == "utility_based_agent + UCB_exploration"
    assert trace.candidates[0].utility >= trace.candidates[1].utility


def test_goal_engine_marks_strong_episode_as_met():
    result = ContestantResult(
        contestant=ProviderModel(model="qwen2.5:3b"),
        first_answer=_turn("first"),
        critique=_turn("critique"),
        revised_answer=_turn("revised"),
        score=ScoreCard(
            contestant="ollama:qwen2.5:3b",
            correctness=9,
            creativity=8,
            clarity=9,
            resilience=9,
            usefulness=9,
            total=44,
            rationale="Strong answer.",
        ),
    )

    traces = GoalBasedEngine().evaluate(ChallengeType.product, [result])

    assert traces
    assert any(trace.status == "met" for trace in traces)
    assert any(trace.target == "winner_quality" for trace in traces)


def test_episode_store_persists_replay_leaderboard_and_q_table(tmp_path):
    store = EpisodeStore(tmp_path / "arena.sqlite3")
    episode = EpisodeResult(
        title="Test Episode",
        challenge="Design a secure notes app.",
        challenge_type=ChallengeType.product,
        host_intro="Welcome.",
        contestants=[
            ContestantResult(
                contestant=ProviderModel(model="qwen2.5:3b"),
                first_answer=_turn("first"),
                critique=_turn("critique"),
                revised_answer=_turn("revised"),
                score=ScoreCard(
                    contestant="ollama:qwen2.5:3b",
                    correctness=8,
                    creativity=8,
                    clarity=8,
                    resilience=8,
                    usefulness=8,
                    total=40,
                    rationale="Solid.",
                ),
            )
        ],
        winner="ollama:qwen2.5:3b",
        final_summary="qwen won.",
    )

    store.save_episode(episode)
    store.set_q_value("product:contestant", "ollama:qwen2.5:3b", 0.5)

    assert store.get_episode(episode.id).winner == "ollama:qwen2.5:3b"
    assert store.leaderboard()[0]["avg_score"] == 40
    assert store.q_table()[0]["q_value"] == 0.5


def _turn(content: str) -> AgentTurn:
    return AgentTurn(
        role="test",
        provider="ollama",
        model="qwen2.5:3b",
        content=content,
        latency_seconds=1,
    )
