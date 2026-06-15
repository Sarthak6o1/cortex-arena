from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class ChallengeType(str, Enum):
    coding = "coding"
    reasoning = "reasoning"
    research = "research"
    creative = "creative"
    security = "security"
    product = "product"


class ProviderModel(BaseModel):
    provider: str = "ollama"
    model: str

    @property
    def label(self) -> str:
        return f"{self.provider}:{self.model}"


class EpisodeRequest(BaseModel):
    title: str
    challenge: str
    challenge_type: ChallengeType = ChallengeType.reasoning
    contestants: list[ProviderModel]
    judge_model: ProviderModel | None = None
    use_reinforcement: bool = True
    use_goal_engine: bool = True
    use_utility_engine: bool = True
    temperature: float = Field(default=0.7, ge=0, le=2)


class AgentTurn(BaseModel):
    role: str
    provider: str
    model: str
    content: str
    latency_seconds: float = 0
    error: str | None = None


class ScoreCard(BaseModel):
    contestant: str
    correctness: int = Field(ge=0, le=10)
    creativity: int = Field(ge=0, le=10)
    clarity: int = Field(ge=0, le=10)
    resilience: int = Field(ge=0, le=10)
    usefulness: int = Field(ge=0, le=10)
    total: int = Field(ge=0, le=50)
    rationale: str


class ContestantResult(BaseModel):
    contestant: ProviderModel
    first_answer: AgentTurn
    critique: AgentTurn
    revised_answer: AgentTurn
    score: ScoreCard | None = None


class ReinforcementSignal(BaseModel):
    state: str
    action: str
    reward: float
    previous_q: float
    next_best_q: float
    updated_q: float
    formula: str


class GoalTrace(BaseModel):
    goal: str
    weight: float
    target: str
    status: str
    evidence: str


class UtilityTrace(BaseModel):
    agent: str
    expected_quality: float
    cost_penalty: float
    risk_penalty: float
    exploration_bonus: float
    utility: float
    formula: str


class DecisionTrace(BaseModel):
    phase: str
    algorithm: str
    state: str
    selected_action: str
    candidates: list[UtilityTrace]
    reason: str


class EpisodeResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    challenge: str
    challenge_type: ChallengeType
    host_intro: str
    contestants: list[ContestantResult]
    winner: str | None = None
    final_summary: str
    learning_signals: list[ReinforcementSignal] = Field(default_factory=list)
    goals: list[GoalTrace] = Field(default_factory=list)
    decisions: list[DecisionTrace] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
