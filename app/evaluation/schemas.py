"""
Core schemas for the self-evaluating lesson generator.

Design principles locked during planning:
1. The LLM provides evaluation evidence; deterministic Python logic owns
   the final shipping decision. We never trust the LLM's own claimed
   overall_pass -- we recompute it from individual check results.
2. Evaluator infrastructure failures (malformed/truncated JSON) are a
   distinct failure category from content-quality failures. A bad
   evaluator response must never be silently treated as "the lesson
   failed" -- see EvaluatorError.
3. Memory stores summarized, reusable failure patterns -- never raw
   historical logs.
4. The rubric is versioned so runs are reproducible even if the rubric
   wording changes later.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

RUBRIC_VERSION = "v2"

CheckStatus = Literal["PASS", "FAIL"]

# Fixed order/id set for the six rubric checks. Used to validate that the
# evaluator returned exactly these checks -- no more, no fewer, no typos
# in an id that would let a check silently vanish from consideration.
RUBRIC_CHECK_IDS = ["C1", "C2", "C3", "C4", "C5", "C6"]

RUBRIC_CHECK_NAMES = {
    "C1": "Technical accuracy & grounding",
    "C2": "Beginner-friendly language",
    "C3": "Jargon explanation",
    "C4": "Required concepts covered",
    "C5": "Concrete example",
    "C6": "Standalone learning outcome",
}


# ---------------------------------------------------------------------------
# Evaluator output
# ---------------------------------------------------------------------------

class RubricCheck(BaseModel):
    """A single binary quality gate result, with evidence -- not a bare
    PASS/FAIL. Evidence is what lets targeted regeneration work: without
    it we could only say "try again", not "fix specifically this"."""

    id: str = Field(..., description="One of C1-C6")
    name: str
    status: CheckStatus
    evidence: str = Field(
        ...,
        min_length=1,
        description="Specific, concrete reference to what in the lesson supports this status.",
    )
    fix: Optional[str] = Field(
        default=None,
        description="Actionable instruction for regeneration. Required when status=FAIL, must be null when PASS.",
    )

    @field_validator("id")
    @classmethod
    def id_must_be_known(cls, v: str) -> str:
        if v not in RUBRIC_CHECK_IDS:
            raise ValueError(f"Unknown check id '{v}', expected one of {RUBRIC_CHECK_IDS}")
        return v

    @field_validator("fix")
    @classmethod
    def fix_required_on_fail(cls, v: Optional[str], info):
        status = info.data.get("status")
        if status == "FAIL" and not v:
            raise ValueError("A 'fix' must be provided when a check FAILs")
        if status == "PASS" and v:
            raise ValueError("'fix' must be null when a check PASSes")
        return v


class EvaluationResult(BaseModel):
    """
    Full evaluator output for one attempt.

    `llm_reported_overall_pass` is what the LLM itself claimed -- kept
    only for logging/comparison against what we actually decided. It is
    NEVER used for routing. The graph router uses
    deterministic_overall_pass() instead.
    """

    rubric_version: str = RUBRIC_VERSION
    llm_reported_overall_pass: bool = Field(
        ..., description="The LLM's own claimed verdict. Advisory only -- not used for routing decisions."
    )
    checks: list[RubricCheck]
    summary: str = Field(..., min_length=1)

    @field_validator("checks")
    @classmethod
    def must_have_all_six_checks_exactly_once(cls, v: list[RubricCheck]) -> list[RubricCheck]:
        ids = [c.id for c in v]
        if sorted(ids) != sorted(RUBRIC_CHECK_IDS):
            raise ValueError(
                f"Evaluator must return exactly the checks {RUBRIC_CHECK_IDS} once each, got {ids}"
            )
        return v

    def deterministic_overall_pass(self) -> bool:
        """The only source of truth for whether the lesson ships.
        Computed in Python, never trusted from the LLM's own claim."""
        return all(c.status == "PASS" for c in self.checks)

    def failed_checks(self) -> list[RubricCheck]:
        return [c for c in self.checks if c.status == "FAIL"]

    def llm_and_deterministic_agree(self) -> bool:
        """Useful for logging evaluator self-consistency over many runs."""
        return self.llm_reported_overall_pass == self.deterministic_overall_pass()


class EvaluatorError(BaseModel):
    """
    Represents an evaluator INFRASTRUCTURE failure (malformed/truncated
    JSON, schema violation, API error) -- distinct from a content-quality
    FAIL. A lesson must never be regenerated because the evaluator itself
    broke; that's a different problem with a different response (retry
    the evaluator call, or halt the run with an explicit error status).
    """

    attempt_number: int
    raw_response: str
    error_message: str


# ---------------------------------------------------------------------------
# Memory (persistent, summarized failure patterns -- not raw logs)
# ---------------------------------------------------------------------------

class FailurePattern(BaseModel):
    pattern_type: str
    instruction: str
    occurrences: int = 1


class Memory(BaseModel):
    patterns: list[FailurePattern] = Field(default_factory=list)

    def top_patterns(self, limit: int = 5) -> list[FailurePattern]:
        """Feed only the most recurring patterns back into generation,
        not the entire history."""
        return sorted(self.patterns, key=lambda p: p.occurrences, reverse=True)[:limit]


# ---------------------------------------------------------------------------
# Run-level records (rejection log + final result)
# ---------------------------------------------------------------------------

class AttemptRecord(BaseModel):
    """One generate+evaluate attempt, as stored in the rejection log."""

    attempt_number: int
    lesson_text: str
    evaluation: EvaluationResult
    passed: bool
    generation_latency_seconds: float
    evaluation_latency_seconds: float


RunStatus = Literal[
    "SHIPPED", "SHIPPED_WITH_KNOWN_ISSUES", "EVALUATION_ERROR", "GENERATION_ERROR"
]


class AttemptMetrics(BaseModel):
    attempt_number: int
    checks_passed: int
    checks_total: int
    generation_latency_seconds: float
    evaluation_latency_seconds: float


class RunMetrics(BaseModel):
    """Aggregate run-level metrics (CLAUDE.md build step 12: attempts,
    retries, checks passed, latency, per attempt). Always computed from
    RunResult.attempts rather than tracked separately, so there is only
    one source of truth for per-attempt data."""

    total_attempts: int
    total_retries: int
    final_checks_passed: int
    final_checks_total: int
    total_latency_seconds: float
    per_attempt: list[AttemptMetrics]


class RunResult(BaseModel):
    """Final output of a full run: what gets written to output/ and logs/,
    and what the API returns."""

    topic: str
    rubric_version: str = RUBRIC_VERSION
    status: RunStatus
    final_lesson: str
    attempts: list[AttemptRecord]
    total_attempts: int
    remaining_failures: list[str] = Field(default_factory=list)
    total_latency_seconds: float

    def compute_metrics(self) -> RunMetrics:
        per_attempt = [
            AttemptMetrics(
                attempt_number=r.attempt_number,
                checks_passed=sum(1 for c in r.evaluation.checks if c.status == "PASS"),
                checks_total=len(r.evaluation.checks),
                generation_latency_seconds=r.generation_latency_seconds,
                evaluation_latency_seconds=r.evaluation_latency_seconds,
            )
            for r in self.attempts
        ]
        final = per_attempt[-1] if per_attempt else None
        return RunMetrics(
            total_attempts=self.total_attempts,
            total_retries=max(self.total_attempts - 1, 0),
            final_checks_passed=final.checks_passed if final else 0,
            final_checks_total=final.checks_total if final else 0,
            total_latency_seconds=self.total_latency_seconds,
            per_attempt=per_attempt,
        )

    def to_rejection_log_text(self) -> str:
        """Human-readable, boxed rejection log -- THE key demo artifact
        (ARCHITECTURE.md Section 6). Shows per-attempt PASS/FAIL per
        check, evidence, fix, and what was preserved vs. fixed on retry."""
        width = 54
        lines = [
            "=" * width,
            "          CONTENT GENERATION RUN",
            "=" * width,
            f"Topic: {self.topic}",
            "",
        ]
        for record in self.attempts:
            checks = record.evaluation.checks
            passed_checks = [c for c in checks if c.status == "PASS"]
            failed_checks = [c for c in checks if c.status == "FAIL"]

            lines.append("-" * width)
            lines.append(f"ATTEMPT {record.attempt_number}")
            lines.append("-" * width)
            lines.append(f"Result: {'SHIPPED' if record.passed else 'REJECTED'}")
            lines.append(f"Checks: {len(passed_checks)}/{len(checks)} PASS")
            lines.append("")

            if record.passed:
                for i in range(0, len(checks), 3):
                    row = checks[i : i + 3]
                    lines.append("  ".join(f"[PASS] {c.id}" for c in row))
            else:
                for c in failed_checks:
                    lines.append(f"[FAIL] {c.id} -- {c.name}")
                    lines.append(f"   Evidence: {c.evidence}")
                    lines.append(f"   Fix: {c.fix}")
                    lines.append("")
                preserved = ", ".join(c.id for c in passed_checks) or "none"
                fixing = ", ".join(c.id for c in failed_checks)
                lines.append(f"Preserving: {preserved}")
                lines.append(f"Fixing:     {fixing}")
            lines.append("")

        lines.append(f"Total Attempts: {self.total_attempts}")
        lines.append(f"Final Status: {self.status}")
        return "\n".join(lines)
