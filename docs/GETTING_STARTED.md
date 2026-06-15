# Getting Started — Run Cortex Arena Locally

This guide helps you clone the repo and run Cortex Arena on your own laptop or workstation in about **10–15 minutes** (plus model download time).

Repository: [github.com/Sarthak6o1/cortex-arena](https://github.com/Sarthak6o1/cortex-arena)

---

## What you need

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Python | 3.10+ | 3.11+ |
| RAM | 8 GB | 16 GB |
| Disk | 10 GB free | 20 GB free |
| GPU | Optional | Helps Ollama run faster |
| Network | For first-time model pull | Offline OK after models download |

You also need **[Ollama](https://ollama.com)** installed and running.

---

## Step 1 — Install Ollama

1. Download Ollama from [ollama.com](https://ollama.com)
2. Install and start the Ollama app (or run `ollama serve`)
3. Confirm it works:

```bash
ollama --version
```

---

## Step 2 — Clone and install Cortex Arena

### Windows (PowerShell)

```powershell
git clone https://github.com/Sarthak6o1/cortex-arena.git
cd cortex-arena
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
pip install -e .[dev]
```

### macOS / Linux

```bash
git clone https://github.com/Sarthak6o1/cortex-arena.git
cd cortex-arena
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install -e .[dev]
```

---

## Step 3 — Pull recommended local models

Cortex Arena works best with four small Ollama models:

```bash
python -m backend.app.cli --pull-recommended
```

Or pull them manually:

```bash
ollama pull llama3.2:3b
ollama pull qwen2.5:3b
ollama pull phi3:mini
ollama pull gemma2:2b
```

Check setup:

```bash
python -m backend.app.cli
```

You should see `Ollama running: True` and the models marked as installed.

---

## Step 4 — Run the dashboard

```bash
python -m streamlit run frontend/streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501)

### First episode in the UI

1. Go to **Setup** — confirm models are installed
2. Go to **Run Episode**
3. Pick 2–3 contestant models (e.g. `qwen2.5:3b`, `gemma2:2b`, `phi3:mini`)
4. Choose a challenge type and paste a prompt
5. Click **Run Episode**
6. Watch host intro → answers → critiques → revisions → scores → winner

---

## Step 5 — Verify everything (automated)

Run all checks from the project root:

### Windows

```powershell
pytest -v
python scripts/verify_live_behavior.py
python scripts/run_model_benchmark.py
```

### macOS / Linux

```bash
pytest -v
python scripts/verify_live_behavior.py
python scripts/run_model_benchmark.py
```

| Script | What it proves | Output file |
|--------|----------------|-------------|
| `pytest -v` | Math, storage, agent logic | terminal |
| `verify_live_behavior.py` | Different queries/models produce different answers | `docs/verification_results.json` |
| `run_model_benchmark.py` | Different challenge types produce different winners | `docs/benchmark_results.json` |

The benchmark takes **15–30 minutes** on a typical laptop because each episode runs a full multi-agent workflow (host, contestants, critic, judge).

---

## Optional — API server

```bash
uvicorn backend.app.main:app --reload
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Example episode request:

```bash
curl -X POST http://127.0.0.1:8000/episodes ^
  -H "Content-Type: application/json" ^
  -d "{\"title\":\"Bug Fix\",\"challenge\":\"Explain a Python None vs empty list bug.\",\"challenge_type\":\"coding\",\"contestants\":[{\"model\":\"qwen2.5:3b\"},{\"model\":\"gemma2:2b\"}]}"
```

(On macOS/Linux, replace `^` with `\`.)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Ollama running: False` | Start the Ollama app or run `ollama serve` |
| `No module named 'backend'` | Run commands from the repo root; activate your venv |
| Model pull is slow | Normal on first run; models are several GB each |
| Episode times out | Close other heavy apps; try fewer contestants first |
| Streamlit port in use | `streamlit run frontend/streamlit_app.py --server.port 8502` |
| Missing models error | Run `python -m backend.app.cli --pull-recommended` |

---

## Where data is stored

- SQLite database: `cortex_arena.db` (episodes, scores, Q-table)
- Verification output: `docs/verification_results.json`
- Benchmark output: `docs/benchmark_results.json`

All stay on your machine by default. No cloud API keys are required for Ollama mode.

---

## Next steps

- Read the full [README](../README.md) for architecture diagrams and API reference
- Try challenges from [`examples/challenges/mixed_challenges.json`](../examples/challenges/mixed_challenges.json)
- Check the **Leaderboard** tab after running several episodes
