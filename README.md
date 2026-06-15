# Cortex Arena X

**A local-first agentic AI evaluation platform for company model testing, private prompt benchmarking, and HIPAA-aligned on-premise workflows.**

Cortex Arena X helps teams evaluate large language models on their own hardware without sending prompts, scores, or replay history to a hosted AI service by default. Local Ollama models compete in structured episodes, receive critique, revise their answers, get scored by judge agents, and build long-term selection memory through goal-based reasoning, utility-based decisions, Q-learning, and UCB exploration.

Designed for **company-local evaluation**, **internal AI labs**, and **privacy-sensitive environments** where data residency, auditability, and controlled model selection matter.

> **Important:** Cortex Arena X is designed with a **HIPAA-aligned local posture**. It is **not** a certified HIPAA product, medical device, or compliance guarantee by itself. Your organization remains responsible for policies, access control, encryption, retention, BAAs, and approved deployment practices.

---

## Table of Contents

- [Major Use Case](#major-use-case)
- [Company Evaluation and HIPAA-Aligned Design](#company-evaluation-and-hipaa-aligned-design)
- [Why This Project Exists](#why-this-project-exists)
- [System Architecture](#system-architecture)
- [Episode Flow](#episode-flow)
- [Agentic Decision Stack](#agentic-decision-stack)
- [Data and Memory Layer](#data-and-memory-layer)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quickstart](#quickstart)
- [Verify Everything Works](#verify-everything-works)
- [API Endpoints](#api-endpoints)
- [Mathematical Core](#mathematical-core)
- [Project Structure](#project-structure)
- [Security Model](#security-model)
- [Roadmap](#roadmap)
- [License and Contribution](#license-and-contribution)

---

## Major Use Case

Cortex Arena X is built for **company-local LLM evaluation** in environments where teams need evidence-backed model selection without exposing internal prompts to public cloud APIs.

Use it when you want to:

- compare local models on the same internal prompt, workflow, or policy task
- benchmark agentic behavior instead of one-shot chat responses
- decide which model to use for coding, security, product, clinical ops support, or reasoning work
- keep prompts, scores, critiques, and replay history on company-controlled hardware
- run evaluation episodes before approving a model for internal production use
- experiment with mathematical agent selection policies in a private lab setting

**In one line:** a private on-premise arena where local LLMs compete, improve, get judged, and leave an auditable trace.

---

## Company Evaluation and HIPAA-Aligned Design

Cortex Arena X is intended for organizations that need **local evaluation** of AI models in privacy-sensitive contexts, including healthcare-adjacent, HR, finance, legal, and internal operations workflows.

### What "HIPAA-aligned local design" means here

This project supports a **local-first privacy posture** that aligns with common HIPAA technical safeguard goals, such as:

| Safeguard goal | How Cortex Arena X supports it |
|----------------|--------------------------------|
| **Minimum necessary exposure** | Default Ollama mode keeps prompts and outputs on the local machine |
| **Data residency** | Episode replays, scores, Q-values, and leaderboards stay in local SQLite |
| **No maintainer cloud dependency** | The repo does not ship shared API keys or force hosted inference |
| **Controlled optional egress** | Cloud providers are disabled unless the company explicitly configures BYOK |
| **Auditability** | Episodes store host intros, answers, critiques, revisions, scores, and decision traces |
| **Explainability** | Goal, utility, and reinforcement traces show why a model was selected or rewarded |
| **Separation of duties** | Backend reads secrets from `.env`; frontend never receives API key values |

### Trust boundary diagram

```mermaid
flowchart LR
    subgraph company [Company Controlled Environment]
        User[Authorized Evaluator]
        UI[Local Streamlit UI]
        API[Local FastAPI Backend]
        Arena[Agentic Evaluation Engine]
        DB[(Local SQLite)]
        Ollama[Local Ollama Models]
    end

    subgraph optional [Optional External Zone - Company Decision Only]
        Cloud[BYOK Cloud Provider]
    end

    User --> UI
    UI --> API
    API --> Arena
    Arena --> Ollama
    Arena --> DB
    Arena -. optional configured path .-> Cloud

    note1[Default path stays inside company boundary]
    note2[No cloud required for core evaluation]
```

### Recommended company deployment model

For privacy-sensitive evaluation, deploy Cortex Arena X as an **internal local lab**:

1. Install on a company-managed laptop, workstation, or on-premise VM
2. Use **Ollama-only mode** for evaluation of sensitive prompts
3. Store SQLite data on encrypted company storage
4. Restrict access to authorized evaluators only
5. Disable optional cloud providers unless legal/security approves them
6. Use synthetic, de-identified, or approved test prompts during model selection
7. Keep production PHI out of experimental episodes unless explicitly approved by policy

### What this platform is good for in a company

- selecting the best local model for internal copilots
- comparing model quality on approved non-production test cases
- testing agentic workflows before rollout to staff-facing tools
- building an internal leaderboard of model performance by task type
- documenting why one model was chosen over another

### What this platform does not replace

Cortex Arena X does **not** by itself provide:

- HIPAA certification
- a Business Associate Agreement (BAA)
- enterprise IAM / SSO
- centralized audit log shipping
- automatic PHI de-identification
- legal or compliance sign-off

Those remain organizational responsibilities. This project gives you a **local evaluation framework** that supports privacy-conscious deployment patterns.

### Suggested GitHub positioning

**Repo name:** `cortex-arena-x`

**Short description:**

> Local-first agentic AI evaluation platform for company model testing, private prompt benchmarking, and HIPAA-aligned on-premise LLM comparison with replayable audit traces.

**Detailed description:**

> Cortex Arena X is an on-premise agentic AI lab for organizations that need to compare, critique, score, and learn from local LLMs without sending evaluation data to hosted services by default. It supports company-local model selection, explainable agent decisions, SQLite replay history, and optional bring-your-own-key cloud providers for teams operating under privacy-sensitive and HIPAA-aligned workflows.

---

## Why This Project Exists

Most local LLM demos are simple chatbots. Cortex Arena X goes further:

| Typical chatbot demo | Cortex Arena X |
|----------------------|----------------|
| One prompt, one answer | Multi-round agent workflow |
| No comparison | Side-by-side model competition |
| No memory | Q-table + leaderboard + replays |
| No reasoning trace | Goal, utility, and policy decisions saved |
| Cloud dependent | Ollama-first, offline after model download |

This makes the project useful for GitHub showcases, internal AI labs, model selection research, and agentic AI experimentation.

---

## System Architecture

High-level view of the full platform:

```mermaid
flowchart TB
    subgraph client [Client Layer]
        UI[Streamlit Dashboard]
    end

    subgraph api [API Layer]
        FastAPI[FastAPI Backend]
    end

    subgraph orchestration [Orchestration Layer]
        Arena[Arena Runner]
        Host[Host Agent]
        Contestants[Contestant Agents]
        Critic[Critic Agent]
        Judge[Judge Agent]
        Summary[Showrunner Summary]
    end

    subgraph intelligence [Agentic Intelligence Layer]
        Goals[Goal-Based Engine]
        Utility[Utility-Based Engine]
        RL[Q-Learning + UCB Engine]
    end

    subgraph providers [Model Provider Layer]
        Ollama[Ollama Local Models]
        HF[Optional Hugging Face BYOK]
        NV[Optional NVIDIA BYOK]
    end

    subgraph persistence [Persistence Layer]
        SQLite[(SQLite)]
        Episodes[Episode Replays]
        Scores[Leaderboard Scores]
        QTable[Q-Values]
    end

    UI --> FastAPI
    UI --> Arena
    FastAPI --> Arena
    Arena --> Host
    Arena --> Contestants
    Arena --> Critic
    Arena --> Judge
    Arena --> Summary
    Arena --> Goals
    Arena --> Utility
    Arena --> RL
    Contestants --> Ollama
    Contestants --> HF
    Contestants --> NV
    Judge --> Ollama
    RL --> SQLite
    Arena --> SQLite
    SQLite --> Episodes
    SQLite --> Scores
    SQLite --> QTable
```

---

## Episode Flow

What happens when you run one episode:

```mermaid
sequenceDiagram
    participant User
    participant Arena
    participant Host
    participant Models as Contestant Models
    participant Critic
    participant Judge
    participant Goals as Goal Engine
    participant Utility as Utility Engine
    participant RL as Q-Learning Engine
    participant DB as SQLite

    User->>Arena: Start episode with challenge
    Arena->>Utility: Rank/select control model
    Arena->>Host: Introduce challenge
    Host-->>Arena: Host intro

    par First answers
        Arena->>Models: Submit first answer
    end
    Models-->>Arena: Initial responses

    par Critique round
        Arena->>Critic: Attack each answer
    end
    Critic-->>Arena: Critiques

    par Revision round
        Arena->>Models: Revise after critique
    end
    Models-->>Arena: Revised answers

    par Judging
        Arena->>Judge: Score each contestant
    end
    Judge-->>Arena: Scorecards + winner

    Arena->>Goals: Evaluate task goals
    Arena->>RL: Update Q-values from rewards
    Arena->>DB: Save replay, scores, traces
    Arena-->>User: Winner, recap, agent traces
```

---

## Agentic Decision Stack

How the app chooses and learns from models:

```mermaid
flowchart LR
    subgraph inputs [Inputs]
        Challenge[Challenge Type]
        Phase[Episode Phase]
        Candidates[Candidate Models]
        History[Past Episode Results]
    end

    subgraph goalAgent [Goal-Based Agent]
        GoalPlan[Define weighted goals]
        GoalEval[Evaluate success]
    end

    subgraph utilityAgent [Utility-Based Agent]
        Prior[Model prior]
        Cost[Local cost penalty]
        Risk[Provider risk penalty]
        Explore[UCB exploration bonus]
        UtilityScore[Utility score]
    end

    subgraph rlAgent [Reinforcement Agent]
        QValue[Learned Q-value]
        Epsilon[Epsilon-greedy explore]
        Bellman[Bellman update]
    end

    subgraph output [Output]
        Selected[Selected model/action]
        Trace[Explainable decision trace]
        Memory[Updated policy memory]
    end

    Challenge --> GoalPlan
    Phase --> UtilityScore
    Candidates --> UtilityScore
    History --> QValue
    Prior --> UtilityScore
    Cost --> UtilityScore
    Risk --> UtilityScore
    Explore --> UtilityScore
    QValue --> UtilityScore
    UtilityScore --> Selected
    Epsilon --> Selected
    Selected --> Trace
    GoalEval --> Memory
    Bellman --> Memory
```

---

## Data and Memory Layer

What gets stored locally after each episode:

```mermaid
erDiagram
    EPISODES ||--o{ SCORES : contains
    EPISODES {
        string id PK
        string title
        string challenge_type
        string winner
        string created_at
        json payload
    }
    SCORES {
        int id PK
        string episode_id FK
        string contestant
        string provider
        string model
        int total
        int correctness
        int creativity
        int clarity
        int resilience
        int usefulness
        string rationale
    }
    Q_VALUES {
        string state PK
        string action PK
        float q_value
        int updates
    }
```

Stored concepts:

| Concept | Meaning |
|---------|---------|
| `state` | `challenge_type:phase` such as `coding:judge` |
| `action` | `provider:model` such as `ollama:qwen2.5:3b` |
| Episode payload | Full replay: answers, critiques, revisions, goals, decisions |
| Leaderboard | Aggregated score history per model |
| Q-table | Learned model preference memory |

---

## Features

- **Local-first execution** with Ollama and no required API keys
- **Multi-agent episodes** with host, contestants, critic, judge, and recap agents
- **Mixed challenge types**: coding, reasoning, research, creative, security, product
- **Goal-based evaluation** of whether an episode met its objectives
- **Utility-based model ranking** with explainable scoring
- **Q-learning memory** that improves model selection over time
- **UCB exploration** for under-tested models
- **Replay history** and season leaderboard in SQLite
- **Streamlit dashboard** for setup, episodes, agent traces, and analytics
- **FastAPI backend** for programmatic access
- **Unit tests** for math, storage, and agent logic

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.10+ |
| API | FastAPI + Uvicorn |
| UI | Streamlit |
| Models | Ollama (default), optional Hugging Face / NVIDIA BYOK |
| Storage | SQLite |
| Validation | Pydantic |
| HTTP client | httpx |
| Tests | pytest |

Recommended local models:

- `llama3.2:3b`
- `qwen2.5:3b`
- `phi3:mini`
- `gemma2:2b`

---

## Quickstart

### 1. Install Ollama

Download from [ollama.com](https://ollama.com).

### 2. Install the project

```bash
git clone <your-repo-url>
cd proj_idea

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -e .
pip install -e .[dev]
```

### 3. Check setup

```bash
python -m backend.app.cli
```

Expected:

```text
Ollama running: True
Recommended free models:
  - llama3.2:3b [installed]
  - qwen2.5:3b [installed]
  ...
```

### 4. Pull recommended models

```bash
python -m backend.app.cli --pull-recommended
```

Or manually:

```bash
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
ollama pull phi3:mini
ollama pull gemma2:2b
```

### 5. Run the dashboard

```bash
python -m streamlit run frontend/streamlit_app.py
```

Open: [http://localhost:8501](http://localhost:8501)

### 6. Optional API server

```bash
uvicorn backend.app.main:app --reload
```

Open: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Verify Everything Works

### Level 1: Infrastructure

```bash
python -m backend.app.cli
```

You should see `Ollama running: True` and installed models.

### Level 2: Core logic

```bash
pytest -v
```

Expected: all tests pass.

Current test coverage:

| Test | Validates |
|------|-----------|
| Q-learning update | Bellman rule and SQLite Q-value persistence |
| Utility engine | Higher-Q model is selected |
| Goal engine | Strong episodes mark goals as met |
| Episode store | Replay, leaderboard, and Q-table persistence |

### Level 3: Full end-to-end episode

1. Open the Streamlit app
2. Go to **Run Episode**
3. Select 2 or more contestant models
4. Enable goal, utility, and reinforcement engines
5. Start an episode
6. Confirm you see:
   - host intro
   - first answers
   - critiques
   - revised answers
   - scorecards
   - winner
   - Q-learning updates
   - saved replay

If all of that appears, the app is working end-to-end.

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Service health check |
| `GET` | `/setup` | Ollama status and recommended models |
| `POST` | `/setup/pull/{model_id}` | Pull a recommended Ollama model |
| `GET` | `/models` | List configured provider models |
| `POST` | `/episodes` | Run a full agentic episode |
| `GET` | `/episodes` | List saved episodes |
| `GET` | `/episodes/{id}` | Fetch one replay |
| `GET` | `/leaderboard` | Season leaderboard |
| `GET` | `/reinforcement/q-table` | Learned Q-values |

---

## Mathematical Core

### Utility-based agent

```text
U(a) = 0.62*Q + 0.23*prior + exploration_bonus - cost_penalty - risk_penalty
```

Used to rank candidate models for control roles such as judge/host/critic selection.

### Hybrid Q-learning + UCB

```text
Q_UCB(a) = Q(s,a) + c * exploration_bonus
```

Used when reinforcement mode selects among previously seen actions.

### Standard Q-learning update

```text
Q(s,a) = Q(s,a) + alpha * (reward + gamma * maxQ(s_next) - Q(s,a))
```

Default policy:

| Parameter | Value | Role |
|-----------|-------|------|
| `alpha` | `0.35` | Learning rate |
| `gamma` | `0.65` | Future reward discount |
| `epsilon` | `0.12` | Random exploration rate |
| `ucb_c` | `0.18` | Exploration pressure |

Reward signals include:

- judge score
- latency penalty
- error penalty
- revision resilience

---

## Project Structure

```text
proj_idea/
├── backend/
│   └── app/
│       ├── agentic/              Goal-based and utility-based engines
│       ├── providers/            Ollama, Hugging Face, NVIDIA adapters
│       ├── reinforcement/        Q-learning and UCB policy engine
│       ├── agents.py             Role prompts for episode agents
│       ├── arena.py              Multi-agent episode orchestration
│       ├── branding.py           App identity constants
│       ├── cli.py                Setup helper and model pull command
│       ├── config.py             Backend-only settings and secret loading
│       ├── judge.py              Score parsing and winner selection
│       ├── main.py               FastAPI entrypoint
│       ├── models.py             Pydantic schemas
│       ├── setup.py              Ollama health checks and recommended models
│       └── storage.py            SQLite replay, leaderboard, Q-table
├── frontend/
│   └── streamlit_app.py          Local dashboard
├── examples/
│   └── challenges/
│       └── mixed_challenges.json Sample challenge pack
├── tests/
│   └── test_agentic_engines.py   Unit tests for math and storage
├── .env.example                  Optional BYOK provider variables
├── pyproject.toml
└── README.md
```

---

## Security Model

Cortex Arena X is designed for **company-local evaluation** and a **HIPAA-aligned privacy posture**, not for exposing shared maintainer API credentials or sending evaluation data to cloud services by default.

### Default secure posture

- **Ollama-only mode** keeps inference local
- **No required API keys** for core functionality
- **Local SQLite storage** for episodes, scores, and Q-values
- **Backend-only secret loading** from `.env`
- **Frontend never receives secret values**
- **Optional cloud providers remain disabled** unless explicitly configured
- **Replayable audit traces** for answers, critiques, revisions, scores, and agent decisions

### Company controls you should add

For privacy-sensitive or healthcare-adjacent environments, organizations should also apply:

- full-disk or database encryption
- role-based access to the evaluation machine
- approved prompt datasets only
- retention and deletion policies for SQLite replay data
- network restrictions on optional cloud providers
- legal/security review before enabling BYOK inference
- separate production and evaluation environments

### Optional provider warning

If you enable Hugging Face, NVIDIA, or other hosted providers:

- prompts may leave the local trust boundary
- your company must confirm provider terms, data handling, and BAA requirements
- these paths should be treated as **non-default** and **explicitly approved**

Example local configuration:

```bash
copy .env.example .env
```

```env
HUGGINGFACE_API_KEY=
NVIDIA_API_KEY=
```

Never commit real keys.

### Compliance note

Cortex Arena X helps teams adopt a **local, auditable, privacy-conscious evaluation workflow**. It does **not** automatically make your organization HIPAA compliant. Compliance depends on how you deploy, govern, and operate the system.

---

## Roadmap

### Model integrations

- LM Studio, llama.cpp server, vLLM, TGI, OpenAI-compatible local endpoints
- OpenRouter, Groq, Gemini, Together AI, Fireworks, enterprise gateways
- Company-local model registries with capability tags and benchmark history

### Mathematical improvements

- Thompson sampling and softmax/Boltzmann exploration
- Elo/Glicko-style ratings across seasons
- Multi-objective optimization for quality, latency, cost, and reliability
- Bayesian confidence intervals and Pareto frontier comparison views

### Agentic improvements

- Planner / executor / verifier chains
- Red-team / blue-team security episodes
- Tool-using agents for local files, tests, and report generation
- Long-term per-model memory
- Enterprise challenge packs for private workflows

---

## License and Contribution

This project is intended as a **company-local AI evaluation lab** for privacy-sensitive model testing, internal benchmarking, and agentic AI research.

Suggested GitHub repository description:

> Local-first agentic AI evaluation platform for company model testing, private prompt benchmarking, and HIPAA-aligned on-premise LLM comparison with replayable audit traces.

Contributions welcome in areas such as:

- new local model providers
- stronger evaluation metrics
- better mathematical selection policies
- enterprise challenge packs
- UI and reporting improvements

---

## Sample Challenge Pack

See [`examples/challenges/mixed_challenges.json`](examples/challenges/mixed_challenges.json) for starter prompts across product, coding, reasoning, security, and creative tasks.

Example:

```json
{
  "title": "Red Team Login",
  "type": "security",
  "challenge": "Review a simple email/password login design for a SaaS app. Find security risks and propose practical mitigations for a small team."
}
```

---

**Cortex Arena X** — compare local models like a lab, not a chatbot. Built for company evaluation and HIPAA-aligned on-premise workflows.
