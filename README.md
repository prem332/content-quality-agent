# Content Quality Agent — Self-Evaluating Lesson Generator

An agentic system that generates a beginner lesson on a given topic,
judges its own output against a rubric of six hard pass/fail checks, and
regenerates (up to 2 retries) until it ships clean or exhausts its
retry budget. Submission topic: **Introduction to RAG
(Retrieval-Augmented Generation)**.

## Core engineering philosophy

> An LLM-generated output is not trusted simply because an LLM produced
> it. Every generated lesson must pass an explicit, evidence-based
> quality contract — validated deterministically in code, not by the
> LLM's own self-report — before it is considered shippable.

Concretely: the evaluator LLM call returns a JSON payload with an
`llm_reported_overall_pass` field. **That field is never used to decide
anything.** Python recomputes the real pass/fail decision as
`all(check.status == "PASS" for check in checks)`
(`EvaluationResult.deterministic_overall_pass()` in
[app/evaluation/schemas.py](app/evaluation/schemas.py)). The two values
are logged side by side so evaluator self-consistency is observable, but
only the deterministic one ever drives routing.

## How it works

```
topic
  │
  ▼
retrieve_context   Chroma (in-memory, rebuilt fresh every run) + local
  │                MiniLM embeddings over knowledge/rag_reference.md
  ▼
load_memory        top recurring failure patterns from past runs
  │
  ▼
generate_lesson ──────────────┐
  │                           │  targeted retry (failed checks + fixes
  ▼                           │  only, not the full evaluation payload)
evaluate_lesson                │
  │                           │
  ├── PASS ──────────────► finalize (SHIPPED)
  ├── FAIL, retries left ─────┘
  └── FAIL, retries exhausted → finalize (SHIPPED_WITH_KNOWN_ISSUES)
```

Six LangGraph nodes total. The evaluator LLM call, JSON validation, and
deterministic pass/fail computation all happen inside `evaluate_lesson`
— they are not separate nodes. Rejection-log writing, memory updates,
and metrics all happen inside `finalize`. See
[app/graph/nodes.py](app/graph/nodes.py) and
[app/graph/workflow.py](app/graph/workflow.py).

### The six rubric checks

Binary, independent, no partial credit — a lesson that's 5/6 great and
1/6 bad still fails that one check.

| ID | Name | Tests |
|----|------|-------|
| C1 | Technical accuracy & grounding | Correct, per the reference material? |
| C2 | Beginner-friendly language | Simple, precise, no idioms, no assumed knowledge? |
| C3 | Jargon explanation | Every necessary technical term defined at first use? |
| C4 | Required concepts covered | What / why / how / basic flow, all present? |
| C5 | Concrete example | A full worked example, not just an abstract description? |
| C6 | Standalone learning outcome | Could the learner explain it back, no outside help? |

### Infrastructure failures vs. content failures

A malformed/truncated evaluator response, or a failed generator call, is
an **infrastructure failure** — never treated as a content-quality FAIL.
The generator retries its own call once (`GenerationError` if it still
fails → run halts with `GENERATION_ERROR`); the evaluator does the same,
and its retry does **not** count against the lesson's own retry budget
(`EvaluatorCallFailed` → `EVALUATION_ERROR`). A broken LLM call must
never silently discard a good lesson or silently ship a bad one.

### Memory (self-evolving)

`memory/failure_patterns.json` holds bounded, summarized failure
patterns — never raw logs. Each failed check maps deterministically to a
canonical pattern via a fixed table (`CHECK_TO_PATTERN` in
[app/memory/memory.py](app/memory/memory.py)), not the evaluator's
free-text `fix` field, since that wording varies run to run and would
make string-matching-based deduplication unreliable. The top 5 most
recurring patterns are fed into the generator prompt on every run.

## Setup

Requires Python 3.10+.

```bash
git clone <this-repo>
cd content-quality-agent
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `GOOGLE_API_KEY` to a real key from
[Google AI Studio](https://aistudio.google.com/apikey) — free tier, no
credit card required. `LANGCHAIN_API_KEY` (from
[smith.langchain.com](https://smith.langchain.com)) is optional; tracing
degrades gracefully to no-op if left as a placeholder.

## Running

**As an API** (Swagger `/docs` is the interaction layer — no frontend):

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`, use `POST /generate` with:

```json
{"topic": "Introduction to RAG (Retrieval-Augmented Generation)"}
```

`GET /health` for a liveness check.

**As a script**, for a quick one-off run without starting a server:

```python
from app.config import MAX_RETRIES, RUBRIC_VERSION
from app.graph.workflow import build_graph

state = {
    "topic": "Introduction to RAG (Retrieval-Augmented Generation)",
    "grounding_context": [], "lesson": "", "rubric_version": RUBRIC_VERSION,
    "evaluation": None, "failed_checks": [], "attempt": 1,
    "max_retries": MAX_RETRIES, "generation_latency_seconds": 0.0,
    "memory_patterns": [], "attempts_log": [], "final_status": None,
}
result = build_graph().invoke(state)
print(result["final_status"], result["lesson"])
```

Either way, a run writes `logs/rejection_log.json` (the full run —
per-attempt checks, evidence, fixes, and metrics) and prints the same
boxed, human-readable rejection log to console — this is the key demo
artifact for showing the evaluator catching and reacting to a failure.

**Evaluator test suite** (TC01–TC07, against the real Gemini evaluator):

```bash
python -m tests.evaluator.run_tests
```

**Demo mode** (deliberate-failure injection for the Loom recording): set
`DEMO_MODE=accuracy_failure` in `.env` to force a known factual defect
into the first generation attempt, so the retry loop firing doesn't
depend on hoping Gemini makes a mistake on camera. Verified reliably
working end-to-end: attempt 1 correctly fails C1 (and C6, a defensible
cascade — a wrong core-mechanism claim genuinely undermines the
standalone learning outcome too), the retry fires with the right
evidence/fix, and attempt 2 ships clean.

`DEMO_MODE=jargon_failure` also exists but proved unreliable in testing
— across four escalating attempts to instruct the model to leave
`embedding`/`vector database`/`semantic search` undefined, it kept
"healing" itself by adding a new, unprompted explanatory section
elsewhere in the lesson (a side effect of how strongly the generator's
own system prompt pushes toward explaining everything — good for lesson
quality, bad for forcing a demo failure via prompt instruction alone).
`accuracy_failure` doesn't have this problem: a stated factual claim
can't be "explained around" the way a missing definition can. Use
`accuracy_failure` for the recording.

## Configuration

Every tunable value lives in [app/config.py](app/config.py), loaded from
`.env` — nothing is hardcoded inline elsewhere. See `.env.example` for
the full list (models, token limits, chunking, retrieval `top_k`,
`MAX_RETRIES`, rubric version, guardrail constants).

**Model note:** the originally planned `gemini-2.5-flash` returned `404
— "no longer available to new users"` on a freshly created Google AI
Studio key. `gemini-flash-latest` works but its underlying model
(`gemini-3.6-flash` at time of writing) carries only a 20 requests/day
free-tier quota. This project runs on `gemini-flash-lite-latest` — a
separate model with its own quota pool — for both the generator and
evaluator roles (same model, different system prompts).

## Project structure

```
app/
├── config.py            # single source of truth for every tunable value
├── llm/provider.py       # LLMProvider interface + GeminiProvider
├── graph/                 # LangGraph state, nodes, wiring
├── evaluation/            # rubric prompt, evaluator, Pydantic schemas
├── generation/             # generator prompts (first-attempt + retry)
├── retrieval/retriever.py # Chroma + MiniLM
├── memory/memory.py        # bounded failure-pattern memory
├── guardrails/input.py     # deterministic input validation
└── main.py                  # FastAPI app
knowledge/rag_reference.md  # grounding source for generation + evaluation
tests/evaluator/             # TC01-TC07 evaluator test suite
memory/, logs/, output/       # runtime-generated, gitignored
```

## Known limitations

- **LLM-judge non-determinism.** The evaluator can disagree with itself
  run to run on borderline calls — confirmed directly during test-suite
  development (byte-identical lesson text produced opposite verdicts on
  two separate evaluator calls). This is a genuine characteristic of
  LLM-based evaluation, not a defect in this codebase; see the evaluator
  test suite results for a full, honest writeup of what was found.
- **Free-tier quota.** `gemini-flash-lite-latest`'s daily request quota
  is finite; heavy iterative testing can exhaust it (resets daily).
