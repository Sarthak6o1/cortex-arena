import random
from dataclasses import dataclass

from backend.app.models import (
    ChallengeType,
    ContestantResult,
    DecisionTrace,
    ProviderModel,
    ReinforcementSignal,
    UtilityTrace,
)


@dataclass(frozen=True)
class QLearningPolicy:
    alpha: float = 0.35
    gamma: float = 0.65
    epsilon: float = 0.12
    ucb_c: float = 0.18


class QLearningEngine:
    """Small persisted Q-learning layer for model selection and post-episode learning."""

    def __init__(self, store, policy: QLearningPolicy | None = None) -> None:
        self.store = store
        self.policy = policy or QLearningPolicy()

    def choose_model(
        self,
        *,
        challenge_type: ChallengeType,
        phase: str,
        candidates: list[ProviderModel],
    ) -> ProviderModel:
        selected, _ = self.choose_model_with_trace(
            challenge_type=challenge_type,
            phase=phase,
            candidates=candidates,
        )
        return selected

    def choose_model_with_trace(
        self,
        *,
        challenge_type: ChallengeType,
        phase: str,
        candidates: list[ProviderModel],
    ) -> tuple[ProviderModel, DecisionTrace]:
        if not candidates:
            raise ValueError("Cannot choose from an empty candidate list.")

        state = self.state_key(challenge_type, phase)
        traces = self._action_traces(state, candidates)
        if random.random() < self.policy.epsilon:
            selected = random.choice(candidates)
            return selected, DecisionTrace(
                phase=phase,
                algorithm="epsilon_greedy_q_learning",
                state=state,
                selected_action=selected.label,
                candidates=traces,
                reason="Exploration step: epsilon triggered a random action.",
            )

        selected = max(
            candidates,
            key=lambda candidate: self._q_ucb_score(state, candidate.label),
        )
        return selected, DecisionTrace(
            phase=phase,
            algorithm="q_learning_ucb",
            state=state,
            selected_action=selected.label,
            candidates=traces,
            reason="Exploitation step: selected highest Q-value plus UCB exploration bonus.",
        )

    def learn_from_results(
        self,
        *,
        challenge_type: ChallengeType,
        results: list[ContestantResult],
    ) -> list[ReinforcementSignal]:
        signals: list[ReinforcementSignal] = []
        for result in results:
            if result.score is None:
                continue
            reward = self._contestant_reward(result)
            signals.append(
                self.update(
                    state=self.state_key(challenge_type, "contestant"),
                    action=result.contestant.label,
                    reward=reward,
                    next_state=self.state_key(challenge_type, "winner"),
                )
            )

            if result.score.contestant == result.contestant.label:
                signals.append(
                    self.update(
                        state=self.state_key(challenge_type, "reviser"),
                        action=result.contestant.label,
                        reward=reward * 0.9,
                        next_state=self.state_key(challenge_type, "complete"),
                    )
                )
        return signals

    def update(self, *, state: str, action: str, reward: float, next_state: str) -> ReinforcementSignal:
        previous_q = self.store.get_q_value(state, action)
        next_best_q = self.store.get_best_q_value(next_state)
        updated_q = previous_q + self.policy.alpha * (
            reward + self.policy.gamma * next_best_q - previous_q
        )
        self.store.set_q_value(state, action, updated_q)
        return ReinforcementSignal(
            state=state,
            action=action,
            reward=round(reward, 4),
            previous_q=round(previous_q, 4),
            next_best_q=round(next_best_q, 4),
            updated_q=round(updated_q, 4),
            formula="Q(s,a) = Q(s,a) + alpha * (reward + gamma * maxQ(s_next) - Q(s,a))",
        )

    @staticmethod
    def state_key(challenge_type: ChallengeType, phase: str) -> str:
        return f"{challenge_type.value}:{phase}"

    @staticmethod
    def _contestant_reward(result: ContestantResult) -> float:
        if result.score is None:
            return 0

        score_reward = result.score.total / 50
        error_penalty = 0.15 if _has_error(result) else 0
        latency_penalty = min(
            0.15,
            (
                result.first_answer.latency_seconds
                + result.revised_answer.latency_seconds
            )
            / 600,
        )
        return max(0, min(1, score_reward - error_penalty - latency_penalty))

    def _q_ucb_score(self, state: str, action: str) -> float:
        q_value = self.store.get_q_value(state, action)
        updates = self.store.get_action_updates(state, action)
        total_updates = self.store.get_total_q_updates(state)
        if updates == 0:
            return q_value + self.policy.ucb_c
        bonus = self.policy.ucb_c * (2 * (total_updates + 1) / updates) ** 0.5 / 10
        return q_value + bonus

    def _action_traces(self, state: str, candidates: list[ProviderModel]) -> list[UtilityTrace]:
        traces = []
        for candidate in candidates:
            q_value = self.store.get_q_value(state, candidate.label)
            q_ucb = self._q_ucb_score(state, candidate.label)
            traces.append(
                UtilityTrace(
                    agent=candidate.label,
                    expected_quality=round(q_value, 4),
                    cost_penalty=0,
                    risk_penalty=0,
                    exploration_bonus=round(q_ucb - q_value, 4),
                    utility=round(q_ucb, 4),
                    formula="Q_UCB(a) = Q(s,a) + c * exploration_bonus",
                )
            )
        return sorted(traces, key=lambda trace: trace.utility, reverse=True)


def _has_error(result: ContestantResult) -> bool:
    return bool(
        result.first_answer.error
        or result.critique.error
        or result.revised_answer.error
    )
