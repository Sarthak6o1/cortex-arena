import math

from backend.app.models import DecisionTrace, ProviderModel, UtilityTrace


class UtilityEngine:
    """Utility-based agent logic for explainable model selection."""

    formula = "U(a) = 0.62*Q + 0.23*prior + exploration_bonus - cost_penalty - risk_penalty"

    def __init__(self, store) -> None:
        self.store = store

    def rank_actions(
        self,
        *,
        phase: str,
        state: str,
        candidates: list[ProviderModel],
    ) -> list[UtilityTrace]:
        total_updates = self.store.get_total_q_updates(state)
        traces: list[UtilityTrace] = []
        for candidate in candidates:
            q_value = self.store.get_q_value(state, candidate.label)
            updates = self.store.get_action_updates(state, candidate.label)
            prior = self._model_prior(candidate.model)
            exploration_bonus = self._ucb_bonus(total_updates, updates)
            cost_penalty = self._cost_penalty(candidate.model, phase)
            risk_penalty = self._risk_penalty(candidate.provider)
            utility = (0.62 * q_value) + (0.23 * prior) + exploration_bonus - cost_penalty - risk_penalty
            traces.append(
                UtilityTrace(
                    agent=candidate.label,
                    expected_quality=round((0.62 * q_value) + (0.23 * prior), 4),
                    cost_penalty=round(cost_penalty, 4),
                    risk_penalty=round(risk_penalty, 4),
                    exploration_bonus=round(exploration_bonus, 4),
                    utility=round(utility, 4),
                    formula=self.formula,
                )
            )
        return sorted(traces, key=lambda trace: trace.utility, reverse=True)

    def decide(
        self,
        *,
        phase: str,
        state: str,
        candidates: list[ProviderModel],
    ) -> tuple[ProviderModel, DecisionTrace]:
        ranked = self.rank_actions(phase=phase, state=state, candidates=candidates)
        if not ranked:
            raise ValueError("Utility engine cannot decide without candidates.")
        selected = ranked[0].agent
        selected_model = next(candidate for candidate in candidates if candidate.label == selected)
        return selected_model, DecisionTrace(
            phase=phase,
            algorithm="utility_based_agent + UCB_exploration",
            state=state,
            selected_action=selected,
            candidates=ranked,
            reason=(
                "Selected the model with the highest utility after combining learned Q-value, "
                "model prior, exploration pressure, local cost, and provider risk."
            ),
        )

    @staticmethod
    def _ucb_bonus(total_updates: int, action_updates: int) -> float:
        if action_updates == 0:
            return 0.28
        return min(0.28, math.sqrt(2 * math.log(total_updates + 1) / action_updates) * 0.08)

    @staticmethod
    def _model_prior(model: str) -> float:
        lowered = model.lower()
        if "qwen" in lowered:
            return 0.76
        if "llama" in lowered:
            return 0.72
        if "phi" in lowered:
            return 0.66
        if "gemma" in lowered:
            return 0.63
        if "mistral" in lowered:
            return 0.70
        return 0.58

    @staticmethod
    def _cost_penalty(model: str, phase: str) -> float:
        lowered = model.lower()
        penalty = 0.03
        if "7b" in lowered or "8b" in lowered or "9b" in lowered:
            penalty += 0.08
        if "13b" in lowered or "14b" in lowered:
            penalty += 0.14
        if phase in {"critic", "judge"}:
            penalty *= 0.8
        return penalty

    @staticmethod
    def _risk_penalty(provider: str) -> float:
        return 0.0 if provider == "ollama" else 0.06
