"""
Node implementations for the generate-evaluate-retry LangGraph.

Six logical nodes only (ARCHITECTURE.md Section 1) -- the evaluator LLM
call, Pydantic validation, and deterministic pass/fail computation all
live inside evaluate_lesson rather than as separate nodes; rejection-log
writing and memory pattern extraction both live inside finalize.

Error handling: the ASCII flow diagram in ARCHITECTURE.md Section 1 shows
plain unconditional edges (no branch for a generation/evaluation
infrastructure failure) -- that diagram is the happy path, and Section 8's
GENERATION_ERROR/EVALUATION_ERROR handling is layered on top of it here
without changing the graph's edges: generate_lesson and evaluate_lesson
catch their own infra failures and set final_status directly, and every
downstream node/router checks state["final_status"] first and no-ops/
short-circuits to finalize if it's already set. This keeps the graph
topology exactly as documented while still halting the run correctly.
"""

import time

from app.evaluation.evaluator import EvaluatorCallFailed
from app.evaluation.evaluator import evaluate_lesson as call_evaluator
from app.evaluation.schemas import AttemptRecord
from app.generation.generator import (
    GenerationError,
    generate_first_attempt,
    generate_retry,
)
from app.graph.state import LessonState
from app.memory.memory import load_top_patterns
from app.retrieval.retriever import retrieve_top_k


def retrieve_context(state: LessonState) -> dict:
    """Retrieve top-k grounding chunks for state["topic"]. Runs exactly
    once per run, before the generate/evaluate loop -- not re-run on
    retries (the LangGraph edges only route back to generate_lesson, so
    this node is never revisited within a run)."""
    return {"grounding_context": retrieve_top_k(state["topic"])}


def load_memory(state: LessonState) -> dict:
    """Load the top recurring failure patterns to feed into the
    generator prompt."""
    return {"memory_patterns": load_top_patterns()}


def generate_lesson(state: LessonState) -> dict:
    if state.get("final_status"):
        return {}

    start = time.time()
    try:
        if not state["lesson"]:
            lesson = generate_first_attempt(
                topic=state["topic"],
                grounding_context=state["grounding_context"],
                memory_patterns=state["memory_patterns"],
            )
            return {
                "lesson": lesson,
                "generation_latency_seconds": time.time() - start,
            }

        lesson = generate_retry(
            grounding_context=state["grounding_context"],
            previous_lesson=state["lesson"],
            attempt_number=state["attempt"],
            failed_checks=state["failed_checks"],
            memory_patterns=state["memory_patterns"],
        )
        return {
            "lesson": lesson,
            "attempt": state["attempt"] + 1,
            "generation_latency_seconds": time.time() - start,
        }
    except GenerationError:
        return {"final_status": "GENERATION_ERROR"}


def evaluate_lesson(state: LessonState) -> dict:
    if state.get("final_status"):
        return {}

    start = time.time()
    try:
        result = call_evaluator(
            topic=state["topic"],
            grounding_context=state["grounding_context"],
            lesson=state["lesson"],
            attempt_number=state["attempt"],
        )
    except EvaluatorCallFailed:
        return {"final_status": "EVALUATION_ERROR"}

    record = AttemptRecord(
        attempt_number=state["attempt"],
        lesson_text=state["lesson"],
        evaluation=result,
        passed=result.deterministic_overall_pass(),
        generation_latency_seconds=state["generation_latency_seconds"],
        evaluation_latency_seconds=time.time() - start,
    )
    return {
        "evaluation": result,
        "failed_checks": result.failed_checks(),
        "attempts_log": state["attempts_log"] + [record],
    }


def route_after_evaluation(state: LessonState) -> str:
    """PASS -> finalize; FAIL with attempts remaining -> generate_lesson
    (retry); FAIL at max_retries, or an infra failure already recorded in
    final_status -> finalize."""
    if state.get("final_status"):
        return "finalize"
    if state["evaluation"].deterministic_overall_pass():
        return "finalize"
    if state["attempt"] < 1 + state["max_retries"]:
        return "retry"
    return "finalize"


def finalize(state: LessonState) -> dict:
    """Compute final_status for a normal (non-error) run. Rejection-log
    writing and memory pattern extraction are added in build step 10."""
    if state.get("final_status"):
        return {}
    passed = state["evaluation"].deterministic_overall_pass()
    return {"final_status": "SHIPPED" if passed else "SHIPPED_WITH_KNOWN_ISSUES"}
