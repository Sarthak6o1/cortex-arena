import asyncio
import time

from backend.app import agents
from backend.app.agentic import GoalBasedEngine, UtilityEngine
from backend.app.config import Settings
from backend.app.judge import choose_winner, fallback_scorecard, parse_scorecard
from backend.app.models import (
    AgentTurn,
    ContestantResult,
    DecisionTrace,
    EpisodeRequest,
    EpisodeResult,
    ProviderModel,
)
from backend.app.providers.base import ProviderError
from backend.app.providers.registry import ProviderRegistry
from backend.app.reinforcement import QLearningEngine
from backend.app.storage import EpisodeStore


class ArenaRunner:
    def __init__(self, settings: Settings) -> None:
        self.registry = ProviderRegistry(settings)
        self.store = EpisodeStore(settings.database_path)
        self.learning = QLearningEngine(self.store)
        self.goals = GoalBasedEngine()
        self.utility = UtilityEngine(self.store)

    async def run_episode(self, request: EpisodeRequest) -> EpisodeResult:
        if not request.contestants:
            raise ValueError("At least one contestant model is required.")

        goal_trace = self.goals.plan_goals(request.challenge_type) if request.use_goal_engine else []
        decisions: list[DecisionTrace] = []
        contestant_state = self.learning.state_key(request.challenge_type, "contestant")
        if request.use_utility_engine:
            decisions.append(
                DecisionTrace(
                    phase="contestant_roster",
                    algorithm="utility_based_agent",
                    state=contestant_state,
                    selected_action="all_selected_contestants",
                    candidates=self.utility.rank_actions(
                        phase="contestant",
                        state=contestant_state,
                        candidates=request.contestants,
                    ),
                    reason="Ranked contestants before the episode using utility, priors, risk, and exploration.",
                )
            )

        judge_model, judge_decision = self._select_control_model(request)
        decisions.append(judge_decision)

        host_intro = await self._safe_generate(
            judge_model,
            role="host",
            system=agents.HOST_SYSTEM,
            prompt=agents.host_prompt(request.title, request.challenge, request.challenge_type),
            temperature=0.8,
        )

        first_round = await asyncio.gather(
            *[
                self._safe_generate(
                    contestant,
                    role="contestant",
                    system=agents.CONTESTANT_SYSTEM,
                    prompt=agents.contestant_prompt(request.challenge, request.challenge_type),
                    temperature=request.temperature,
                )
                for contestant in request.contestants
            ]
        )

        critiques = await asyncio.gather(
            *[
                self._safe_generate(
                    judge_model,
                    role="critic",
                    system=agents.CRITIC_SYSTEM,
                    prompt=agents.critic_prompt(
                        request.challenge,
                        contestant.label,
                        first_answer.content,
                    ),
                    temperature=0.4,
                )
                for contestant, first_answer in zip(request.contestants, first_round, strict=True)
            ]
        )

        revisions = await asyncio.gather(
            *[
                self._safe_generate(
                    contestant,
                    role="reviser",
                    system=agents.REVISION_SYSTEM,
                    prompt=agents.revision_prompt(
                        request.challenge,
                        first_answer.content,
                        critique.content,
                    ),
                    temperature=request.temperature,
                )
                for contestant, first_answer, critique in zip(
                    request.contestants,
                    first_round,
                    critiques,
                    strict=True,
                )
            ]
        )

        results = [
            ContestantResult(
                contestant=contestant,
                first_answer=first_answer,
                critique=critique,
                revised_answer=revision,
            )
            for contestant, first_answer, critique, revision in zip(
                request.contestants,
                first_round,
                critiques,
                revisions,
                strict=True,
            )
        ]

        judged = await asyncio.gather(
            *[
                self._judge_result(request, result, judge_model)
                for result in results
            ]
        )

        scorecards = [result.score for result in judged if result.score is not None]
        winner = choose_winner(scorecards)
        if request.use_goal_engine:
            goal_trace = self.goals.evaluate(request.challenge_type, judged)
        learning_signals = []
        if request.use_reinforcement:
            learning_signals = self.learning.learn_from_results(
                challenge_type=request.challenge_type,
                results=judged,
            )
            if scorecards:
                average_reward = sum(score.total for score in scorecards) / (len(scorecards) * 50)
                learning_signals.append(
                    self.learning.update(
                        state=self.learning.state_key(request.challenge_type, "judge"),
                        action=judge_model.label,
                        reward=average_reward,
                        next_state=self.learning.state_key(request.challenge_type, "complete"),
                    )
                )
        final_summary = await self._build_summary(request, judge_model, scorecards)

        return EpisodeResult(
            title=request.title,
            challenge=request.challenge,
            challenge_type=request.challenge_type,
            host_intro=host_intro.content,
            contestants=judged,
            winner=winner,
            final_summary=final_summary.content,
            learning_signals=learning_signals,
            goals=goal_trace,
            decisions=decisions,
        )

    def _select_control_model(
        self,
        request: EpisodeRequest,
    ) -> tuple[ProviderModel, DecisionTrace]:
        state = self.learning.state_key(request.challenge_type, "judge")
        if request.judge_model:
            candidates = (
                self.utility.rank_actions(
                    phase="judge",
                    state=state,
                    candidates=request.contestants,
                )
                if request.use_utility_engine
                else []
            )
            return request.judge_model, DecisionTrace(
                phase="judge",
                algorithm="manual_override",
                state=state,
                selected_action=request.judge_model.label,
                candidates=candidates,
                reason="User explicitly selected the control model.",
            )

        if request.use_utility_engine:
            return self.utility.decide(
                phase="judge",
                state=state,
                candidates=request.contestants,
            )

        if request.use_reinforcement:
            return self.learning.choose_model_with_trace(
                challenge_type=request.challenge_type,
                phase="judge",
                candidates=request.contestants,
            )

        selected = request.contestants[0]
        return selected, DecisionTrace(
            phase="judge",
            algorithm="first_available",
            state=state,
            selected_action=selected.label,
            candidates=[],
            reason="No decision engine was enabled, so the first contestant was used.",
        )

    async def _judge_result(
        self,
        request: EpisodeRequest,
        result: ContestantResult,
        judge_model: ProviderModel,
    ) -> ContestantResult:
        contestant_name = result.contestant.label
        raw_score = await self._safe_generate(
            judge_model,
            role="judge",
            system=agents.JUDGE_SYSTEM,
            prompt=agents.judge_prompt(
                request.challenge,
                contestant_name,
                result.first_answer.content,
                result.critique.content,
                result.revised_answer.content,
            ),
            temperature=0.1,
        )
        try:
            result.score = parse_scorecard(contestant_name, raw_score.content)
        except (ValueError, TypeError) as exc:
            result.score = fallback_scorecard(contestant_name, str(exc))
        return result

    async def _build_summary(
        self,
        request: EpisodeRequest,
        judge_model: ProviderModel,
        scorecards: list,
    ) -> AgentTurn:
        score_lines = [
            f"{score.contestant}: {score.total}/50 - {score.rationale}" for score in scorecards
        ]
        return await self._safe_generate(
            judge_model,
            role="showrunner",
            system=agents.SUMMARY_SYSTEM,
            prompt=agents.summary_prompt(request.challenge, score_lines),
            temperature=0.5,
        )

    async def _safe_generate(
        self,
        model: ProviderModel,
        *,
        role: str,
        system: str,
        prompt: str,
        temperature: float,
    ) -> AgentTurn:
        started = time.perf_counter()
        try:
            provider = self.registry.get(model.provider)
            content = await provider.generate(
                model.model,
                prompt,
                system=system,
                temperature=temperature,
            )
            error = None
        except ProviderError as exc:
            content = ""
            error = str(exc)

        return AgentTurn(
            role=role,
            provider=model.provider,
            model=model.model,
            content=content,
            latency_seconds=round(time.perf_counter() - started, 2),
            error=error,
        )
