from backend.app.models import ChallengeType


HOST_SYSTEM = """You are the host of Cortex Arena X.
Make the episode feel exciting, but stay concise and useful. Explain the challenge,
rules, and judging criteria in a clear way."""


CONTESTANT_SYSTEM = """You are a contestant in Cortex Arena X.
Your goal is to produce the strongest useful answer. Be direct, practical, and accurate.
You will later receive criticism and get one chance to revise."""


CRITIC_SYSTEM = """You are a sharp critic in Cortex Arena X.
Find flaws, missing details, weak assumptions, hallucination risks, and places where
the contestant can improve. Be tough but constructive."""


REVISION_SYSTEM = """You are a contestant revising your answer after critique.
Use the criticism to produce a stronger final answer. Do not complain about the critique.
Keep the final answer useful and focused."""


JUDGE_SYSTEM = """You are a strict judge in Cortex Arena X.
Score the contestant fairly against the challenge and critique response.
Return only valid JSON with these keys:
correctness, creativity, clarity, resilience, usefulness, rationale.
Each score must be an integer from 0 to 10."""


SUMMARY_SYSTEM = """You are the showrunner summarizer for Cortex Arena X.
Create a concise episode recap: winner, why they won, strongest insight, and what
the other contestants could improve."""


def host_prompt(title: str, challenge: str, challenge_type: ChallengeType) -> str:
    return f"""Episode title: {title}
Challenge type: {challenge_type.value}
Challenge:
{challenge}

Introduce the episode and explain how contestants will be judged."""


def contestant_prompt(challenge: str, challenge_type: ChallengeType) -> str:
    return f"""Challenge type: {challenge_type.value}
Challenge:
{challenge}

Submit your first-round answer."""


def critic_prompt(challenge: str, contestant_name: str, first_answer: str) -> str:
    return f"""Challenge:
{challenge}

Contestant: {contestant_name}
First answer:
{first_answer}

Critique this answer. Focus on correctness, missed edge cases, practicality,
creativity, clarity, and instruction-following."""


def revision_prompt(challenge: str, first_answer: str, critique: str) -> str:
    return f"""Challenge:
{challenge}

Your first answer:
{first_answer}

Critique you received:
{critique}

Revise your answer into a stronger final submission."""


def judge_prompt(
    challenge: str,
    contestant_name: str,
    first_answer: str,
    critique: str,
    revised_answer: str,
) -> str:
    return f"""Challenge:
{challenge}

Contestant: {contestant_name}

First answer:
{first_answer}

Critique:
{critique}

Revised answer:
{revised_answer}

Score the revised answer. Use this JSON shape exactly:
{{
  "correctness": 0,
  "creativity": 0,
  "clarity": 0,
  "resilience": 0,
  "usefulness": 0,
  "rationale": "short explanation"
}}"""


def summary_prompt(challenge: str, score_lines: list[str]) -> str:
    scores = "\n".join(score_lines)
    return f"""Challenge:
{challenge}

Final scores:
{scores}

Write the final episode recap."""
