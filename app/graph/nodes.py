"""
Node skeleton for the generate-evaluate-retry LangGraph.

Six logical nodes only (ARCHITECTURE.md Section 1) -- the evaluator LLM
call, Pydantic validation, and deterministic pass/fail computation all
live inside evaluate_lesson rather than as separate nodes; rejection-log
writing and memory pattern extraction both live inside finalize.

Each function below is a placeholder implemented in a later build step:
    retrieve_context        -> step 6  (Chroma + MiniLM retrieval)
    load_memory              -> step 10 (bounded failure-pattern memory)
    generate_lesson          -> step 7  (Gemini generator, first + retry prompts)
    evaluate_lesson          -> step 8  (Gemini evaluator + Pydantic validation)
    route_after_evaluation   -> step 9  (conditional router, graph wiring)
    finalize                 -> step 9/10/12 (rejection log, memory update, metrics)

Node functions return a partial state update dict, per LangGraph
convention. route_after_evaluation is a conditional-edge function, not a
state-mutating node, so it returns a routing label string instead.
"""

from app.graph.state import LessonState


def retrieve_context(state: LessonState) -> dict:
    """Retrieve top-k grounding chunks for state["topic"] via Chroma +
    MiniLM embeddings over knowledge/rag_reference.md. Runs exactly once
    per run, before the generate/evaluate loop -- not re-run on retries."""
    raise NotImplementedError("Implemented in build step 6 (retrieval).")


def load_memory(state: LessonState) -> dict:
    """Load memory/failure_patterns.json and select the top N recurring
    patterns to feed into the generator prompt."""
    raise NotImplementedError("Implemented in build step 10 (memory).")


def generate_lesson(state: LessonState) -> dict:
    """Call the generator LLM: first-attempt prompt on attempt 1, targeted
    retry prompt (failed checks + evidence/fix only) on later attempts."""
    raise NotImplementedError("Implemented in build step 7 (generator).")


def evaluate_lesson(state: LessonState) -> dict:
    """Call the evaluator LLM, validate the raw JSON response against
    EvaluationResult, and compute the deterministic overall pass/fail via
    EvaluationResult.deterministic_overall_pass() -- never the LLM's own
    llm_reported_overall_pass. A Pydantic validation failure here is an
    EvaluatorError (infrastructure failure), not a content FAIL."""
    raise NotImplementedError("Implemented in build step 8 (evaluator).")


def route_after_evaluation(state: LessonState) -> str:
    """Conditional edge: PASS -> finalize; FAIL with attempts remaining ->
    generate_lesson (retry); FAIL at max_retries -> finalize."""
    raise NotImplementedError("Implemented in build step 9 (graph wiring).")


def finalize(state: LessonState) -> dict:
    """Write the rejection log, update memory/failure_patterns.json, and
    compute run metrics."""
    raise NotImplementedError("Implemented in build steps 9/10/12.")
