"""
Generator: builds the first-attempt or targeted-retry prompt and calls
the LLM through the LLMProvider abstraction.

Error handling per ARCHITECTURE.md Section 8: a generator infrastructure
failure (network error, API error, empty/blocked response) is never a
content-quality failure. Retry the call once; if it still fails, raise
GenerationError so the caller can halt the run with status
GENERATION_ERROR rather than silently discarding or fabricating a lesson.
"""

from app.config import GENERATOR_MAX_TOKENS, GENERATOR_MODEL
from app.evaluation.schemas import FailurePattern, RubricCheck
from app.generation.prompts import FIRST_ATTEMPT_PROMPT, RETRY_PROMPT
from app.llm.provider import GeminiProvider, LLMProvider


class GenerationError(Exception):
    """Generator infrastructure failure that survived one retry."""


def _format_grounding_context(chunks: list[str]) -> str:
    return "\n\n".join(chunks)


def _format_memory_patterns(patterns: list[FailurePattern]) -> str:
    if not patterns:
        return "None yet -- this is an early run."
    return "\n".join(f"- {p.instruction}" for p in patterns)


def _format_failed_checks(failed_checks: list[RubricCheck]) -> str:
    return "\n\n".join(
        f"[{c.id}] {c.name}\nEvidence: {c.evidence}\nFix: {c.fix}"
        for c in failed_checks
    )


def _call_with_retry(provider: LLMProvider, prompt: str) -> str:
    try:
        return provider.generate(prompt, max_tokens=GENERATOR_MAX_TOKENS)
    except Exception:
        try:
            return provider.generate(prompt, max_tokens=GENERATOR_MAX_TOKENS)
        except Exception as e:
            raise GenerationError(f"Generator call failed twice: {e}") from e


def generate_first_attempt(
    topic: str,
    grounding_context: list[str],
    memory_patterns: list[FailurePattern],
    provider: LLMProvider | None = None,
) -> str:
    provider = provider or GeminiProvider(model=GENERATOR_MODEL)
    prompt = FIRST_ATTEMPT_PROMPT.format(
        grounding_context=_format_grounding_context(grounding_context),
        memory_patterns=_format_memory_patterns(memory_patterns),
        topic=topic,
    )
    return _call_with_retry(provider, prompt)


def generate_retry(
    grounding_context: list[str],
    previous_lesson: str,
    attempt_number: int,
    failed_checks: list[RubricCheck],
    memory_patterns: list[FailurePattern],
    provider: LLMProvider | None = None,
) -> str:
    provider = provider or GeminiProvider(model=GENERATOR_MODEL)
    prompt = RETRY_PROMPT.format(
        grounding_context=_format_grounding_context(grounding_context),
        previous_lesson=previous_lesson,
        attempt_number=attempt_number,
        failed_checks_with_evidence_and_fixes=_format_failed_checks(failed_checks),
        memory_patterns=_format_memory_patterns(memory_patterns),
    )
    return _call_with_retry(provider, prompt)
