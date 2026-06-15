from dataclasses import dataclass

from backend.app.models import ChallengeType, ContestantResult, GoalTrace


@dataclass(frozen=True)
class GoalSpec:
    name: str
    weight: float
    target: str


class GoalBasedEngine:
    """Maps challenge types into explicit goals and evaluates whether agents met them."""

    def plan_goals(self, challenge_type: ChallengeType) -> list[GoalTrace]:
        return [
            GoalTrace(
                goal=goal.name,
                weight=goal.weight,
                target=goal.target,
                status="planned",
                evidence="Goal selected before the episode starts.",
            )
            for goal in self._goal_specs(challenge_type)
        ]

    def evaluate(self, challenge_type: ChallengeType, results: list[ContestantResult]) -> list[GoalTrace]:
        specs = self._goal_specs(challenge_type)
        if not results:
            return [
                GoalTrace(
                    goal=goal.name,
                    weight=goal.weight,
                    target=goal.target,
                    status="missed",
                    evidence="No contestant results were produced.",
                )
                for goal in specs
            ]

        best_score = max((result.score.total for result in results if result.score), default=0)
        average_score = _average(result.score.total for result in results if result.score)
        successful_revisions = sum(
            1
            for result in results
            if result.revised_answer.content and not result.revised_answer.error
        )
        no_error_runs = sum(1 for result in results if not _has_error(result))

        metrics = {
            "winner_quality": best_score / 50,
            "field_quality": average_score / 50,
            "revision_success": successful_revisions / len(results),
            "reliability": no_error_runs / len(results),
        }

        traces: list[GoalTrace] = []
        for goal in specs:
            value = metrics.get(goal.target, 0)
            status = "met" if value >= 0.72 else "partial" if value >= 0.45 else "missed"
            traces.append(
                GoalTrace(
                    goal=goal.name,
                    weight=goal.weight,
                    target=goal.target,
                    status=status,
                    evidence=f"{goal.target}={value:.2f}",
                )
            )
        return traces

    def _goal_specs(self, challenge_type: ChallengeType) -> list[GoalSpec]:
        base = [
            GoalSpec("Maximize final answer usefulness", 0.35, "winner_quality"),
            GoalSpec("Reward models that improve after critique", 0.25, "revision_success"),
            GoalSpec("Avoid brittle agent runs", 0.15, "reliability"),
        ]
        challenge_goal = {
            ChallengeType.coding: GoalSpec("Prioritize correctness and testability", 0.25, "winner_quality"),
            ChallengeType.security: GoalSpec("Prioritize risk discovery", 0.25, "winner_quality"),
            ChallengeType.creative: GoalSpec("Prioritize novelty with clarity", 0.25, "field_quality"),
            ChallengeType.research: GoalSpec("Prioritize balanced synthesis", 0.25, "field_quality"),
            ChallengeType.product: GoalSpec("Prioritize practical product judgment", 0.25, "winner_quality"),
            ChallengeType.reasoning: GoalSpec("Prioritize robust reasoning", 0.25, "winner_quality"),
        }[challenge_type]
        return [*base, challenge_goal]


def _average(values) -> float:
    numbers = list(values)
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


def _has_error(result: ContestantResult) -> bool:
    return bool(
        result.first_answer.error
        or result.critique.error
        or result.revised_answer.error
    )
