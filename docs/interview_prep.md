# Interview Prep — Q&A

Every answer here should be sayable from memory in under 30 seconds,
without opening this file. This file is the rehearsal aid, not the
script.

---

**Q: Why LangGraph, and not just a Python while-loop?**

A while-loop would work for the happy path, but the retry counter, the
accumulated attempts log, and the routing decision all need to survive
across separate generate/evaluate cycles cleanly. LangGraph makes that
state explicit and typed (`LessonState`) instead of scattered across
closure variables, makes the retry logic a declared conditional edge
instead of an if/else buried in a loop body, and — as a side benefit that
turned out to matter a lot during development — every node execution
auto-traces to LangSmith with zero extra code, which made debugging the
retry loop and diagnosing the evaluator test suite dramatically easier
than print-statement debugging would have been.

**Q: Why one model for both the generator and evaluator roles?**

Two reasons, one practical and one architectural. Practical: no
credit-card-friendly provider offers two distinct free-tier models worth
splitting across roles, and managing two provider integrations for a
36-hour build isn't a good trade. Architectural: the roles are separated
by system prompt, not by model — the generator writes, the evaluator
judges adversarially and is instructed to default to FAIL — so the
separation of concerns is real even with one model underneath. The
`LLMProvider` abstraction (`app/llm/provider.py`) also means swapping to
two different models later is a config change, not a redesign.

**Q: Why Chroma over FAISS?**

The corpus is one small, static markdown file — this was never a
"which vector store scales best" decision. Chroma's Python API is
simpler for the ephemeral, rebuilt-every-run use case this project
needs (no persisted index to manage, no manual ID bookkeeping), and it's
the more common default in the LangChain ecosystem this project already
depends on. FAISS is explicitly excluded — introducing it here would be
solving a scale problem that doesn't exist.

**Q: Why six rubric checks?**

They map directly to the brief's six named dimensions (accurate &
grounded, beginner-friendly language, teaches by example, clear/no
jargon, key points covered, coherent flow) with one binary check each —
C1 through C6. Six was the number of dimensions the brief asked for
weighing; each became its own independent gate rather than folding
several into one check, because independent binary checks are what make
"which fix do I need on retry" a precise, actionable signal instead of a
vague overall score.

**Q: Why max two retries?**

Directly from the brief: "max 1–2 retries, so the loop always
terminates." Two was chosen over one because a single retry doesn't
leave much room to fix more than one failed check convincingly; three or
more starts trading diminishing returns against latency and free-tier
API quota for a 36-hour build. The loop always terminates either way —
`SHIPPED` or `SHIPPED_WITH_KNOWN_ISSUES` after attempt `1 + MAX_RETRIES`.

**Q: Why deterministic validation instead of trusting the evaluator's own verdict?**

This is the project's central thesis, not an implementation detail: an
LLM saying "this passes" is not evidence that it passes. The evaluator
returns `llm_reported_overall_pass` as one field among many in its JSON,
but the actual shipping decision is `all(check.status == "PASS" for
check in checks)`, computed in plain Python
(`EvaluationResult.deterministic_overall_pass()`). The two are logged
side by side specifically so evaluator self-consistency is observable
and never assumed.

**Q: Why no multi-agent framework (CrewAI, etc.)?**

The problem is a linear generate → evaluate → retry loop with one
conditional edge — that's a state machine, not a multi-agent negotiation.
Reaching for a heavier framework here would add orchestration complexity
with nothing real to orchestrate. Restraint was a deliberate,
reconsidered decision, not an oversight: every hour not spent on
unneeded infrastructure was an hour spent hardening the core loop, the
evaluator test suite, and the demo.

**Q: Why Gemini specifically?**

The hard constraint was no credit card, which rules out both Anthropic
and OpenAI's APIs even for trivial usage. Google AI Studio's Gemini API
has a genuine no-card, no-expiration free tier — it was the only
model provider that actually fit the constraint, not a quality-driven
pick among equals.

**Q: Why gemini-flash-lite-latest instead of the originally planned gemini-2.5-flash?**

Implementation proved the plan wrong, twice, in a way that's worth being
able to explain precisely: `gemini-2.5-flash` returns a `404 — "no longer
available to new users"` on a freshly created Google AI Studio key, and
its most obvious replacement, `gemini-flash-latest`, works but resolves
under the hood to a model with only a 20 requests/day free-tier quota —
exhausted mid-session just testing the generator and evaluator once
each. `gemini-flash-lite-latest` is a distinct underlying model with its
own separate quota pool. Neither swap changed the "why Gemini" reasoning
above; both were forced by what a brand-new free-tier key can actually
call, confirmed via live API responses, not guessed at.
