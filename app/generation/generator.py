"""
Generator: builds the first-attempt or targeted-retry prompt and calls
the LLM through the LLMProvider abstraction.

Error handling per ARCHITECTURE.md Section 8: a generator infrastructure
failure (network error, API error, empty/blocked response) is never a
content-quality failure. Retry the call once; if it still fails, raise
GenerationError so the caller can halt the run with status
GENERATION_ERROR rather than silently discarding or fabricating a lesson.
"""

from app.config import DEMO_MODE, GENERATOR_MAX_TOKENS, GENERATOR_MODEL
from app.evaluation.schemas import FailurePattern, RubricCheck
from app.generation.prompts import FIRST_ATTEMPT_PROMPT, RETRY_PROMPT
from app.llm.provider import GeminiProvider, LLMProvider


class GenerationError(Exception):
    """Generator infrastructure failure that survived one retry."""


# ARCHITECTURE.md Section 11: deterministically inject one of the known
# TC-style defects into the first generation attempt, so a Loom demo of
# "the evaluator catching a deliberate error" doesn't depend on hoping
# Gemini makes a mistake on camera. Applied only in generate_first_attempt
# (never generate_retry) so the retry has a normal, unmodified chance to
# fix it -- these are the same defect categories already validated by the
# TC01/TC03 evaluator test fixtures, so the evaluator is known to catch
# both reliably.
DEMO_MODE_INSTRUCTIONS = {
    "accuracy_failure": (
        "\n\nDEMO OVERRIDE (this instruction exists only to demonstrate the "
        "evaluator catching an error; ignore normal accuracy rules for it): "
        "State explicitly, in the 'What is RAG?' section, that RAG "
        "permanently teaches the model new information by adding it "
        "directly into the model's memory, so the model remembers it "
        "forever in future unrelated conversations."
    ),
    "jargon_failure": (
        "\n\nDEMO OVERRIDE (this instruction exists only to demonstrate the "
        "evaluator catching an error; ignore normal jargon rules for it, "
        "including the instruction above to define every technical term): "
        "Replace the 'How does RAG work?' section with exactly this numbered "
        "list, unmodified: '1. A user asks a question. 2. The question is "
        "converted into an embedding. 3. The system performs semantic search "
        "over a vector database to find the most relevant chunks. 4. The "
        "retriever selects the top-k chunks. 5. These chunks are given to "
        "the AI model, along with the original question, and the AI writes "
        "an answer using them.' The worked example must reuse these same "
        "exact words -- 'embedding', 'semantic search', 'vector database', "
        "'retriever', 'top-k' -- when describing what happens at each step, "
        "instead of describing the mechanism in different, plainer words. "
        "For example, write 'the system converts the question into an "
        "embedding and performs semantic search over the vector database', "
        "not a plain-language paraphrase of what that means. Do not define, "
        "paraphrase, or explain what any of these terms mean in your own "
        "simpler words anywhere in the lesson -- not in the How It Works "
        "section, not in the worked example, not in the recap. Every time "
        "you would normally explain the mechanism in plain language, use "
        "the jargon word itself instead and move on without elaborating."
    ),
}


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
    prompt += DEMO_MODE_INSTRUCTIONS.get(DEMO_MODE, "")
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
