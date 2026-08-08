"""
Failure-pattern memory: bounded, summarized, deterministic (see
ARCHITECTURE.md Section 7). NOT raw historical logs -- only occurrence
counts per canonical pattern type.
"""

import json
import os

from pydantic import ValidationError

from app.config import MEMORY_FILE_PATH
from app.evaluation.schemas import AttemptRecord, FailurePattern, Memory

# Deterministic check-id -> canonical pattern mapping (ARCHITECTURE.md
# Section 7, locked). NOT derived from the evaluator's free-text `fix`
# field -- that wording varies run to run, which would make
# string-matching-based deduplication unreliable.
CHECK_TO_PATTERN = {
    "C1": {
        "pattern_type": "technical_inaccuracy",
        "instruction": "Verify every factual claim against the grounding material before including it.",
    },
    "C2": {
        "pattern_type": "overly_complex_language",
        "instruction": "Use short, direct sentences. Avoid formal/academic phrasing.",
    },
    "C3": {
        "pattern_type": "unexplained_jargon",
        "instruction": "Define technical terms in simple language before using them.",
    },
    "C4": {
        "pattern_type": "missing_required_concept",
        "instruction": "Ensure what/why/how and basic flow are all explicitly covered.",
    },
    "C5": {
        "pattern_type": "missing_or_vague_example",
        "instruction": "Include a complete, concrete, end-to-end worked example.",
    },
    "C6": {
        "pattern_type": "not_standalone_understandable",
        "instruction": "Connect concepts into a clear narrative a beginner could repeat back.",
    },
}


def load_top_patterns(limit: int = 5) -> list[FailurePattern]:
    return _load_memory().top_patterns(limit=limit)


def record_failed_checks_from_attempts(attempts_log: list[AttemptRecord]) -> None:
    """On each FAIL across every attempt in the run, look up the
    deterministic pattern and increment its occurrence count in persisted
    memory (adding it if not seen before). Recording every attempt's
    failures, not just the final one, is what lets memory reflect
    mistakes even in a run that eventually shipped clean -- the
    "self-evolving" signal the brief asks for."""
    failed_ids = [
        check.id
        for record in attempts_log
        for check in record.evaluation.checks
        if check.status == "FAIL"
    ]
    if not failed_ids:
        return

    memory = _load_memory()
    by_type = {p.pattern_type: p for p in memory.patterns}

    for check_id in failed_ids:
        mapped = CHECK_TO_PATTERN.get(check_id)
        if mapped is None:
            continue
        existing = by_type.get(mapped["pattern_type"])
        if existing is not None:
            existing.occurrences += 1
        else:
            new_pattern = FailurePattern(
                pattern_type=mapped["pattern_type"],
                instruction=mapped["instruction"],
                occurrences=1,
            )
            memory.patterns.append(new_pattern)
            by_type[mapped["pattern_type"]] = new_pattern

    _save_memory(memory)


def _load_memory() -> Memory:
    """A corrupted/malformed memory file is an infrastructure problem in
    a non-critical subsystem, not a reason to block generation -- same
    principle as the generator/evaluator error handling in
    ARCHITECTURE.md Section 8. Fall back to empty memory rather than
    crashing the run."""
    if not os.path.exists(MEMORY_FILE_PATH):
        return Memory()
    try:
        with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
            return Memory.model_validate(json.load(f))
    except (json.JSONDecodeError, ValidationError) as e:
        print(f"Warning: {MEMORY_FILE_PATH} is corrupted ({e}); starting from empty memory.")
        return Memory()


def _save_memory(memory: Memory) -> None:
    directory = os.path.dirname(MEMORY_FILE_PATH)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(memory.model_dump(), f, indent=2)
