from typing import Literal, Optional, TypedDict

from app.evaluation.schemas import (
    AttemptRecord,
    EvaluationResult,
    FailurePattern,
    RubricCheck,
)

FinalStatus = Literal[
    "SHIPPED", "SHIPPED_WITH_KNOWN_ISSUES", "EVALUATION_ERROR", "GENERATION_ERROR"
]


class LessonState(TypedDict):
    topic: str
    grounding_context: list[str]  # retrieved chunks, top-k from Chroma

    lesson: str  # current lesson text
    rubric_version: str  # "v2"

    evaluation: Optional[EvaluationResult]
    failed_checks: list[RubricCheck]  # derived from evaluation, stored explicitly

    attempt: int  # starts at 1
    max_retries: int  # 2

    generation_latency_seconds: float

    memory_patterns: list[FailurePattern]  # loaded once at start, top N by occurrence

    attempts_log: list[AttemptRecord]  # accumulates every attempt for the rejection log
    final_status: Optional[FinalStatus]