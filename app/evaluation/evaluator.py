import json

from pydantic import ValidationError

from app.config import EVALUATOR_MAX_TOKENS, EVALUATOR_MODEL
from app.evaluation.prompts import EVALUATOR_PROMPT
from app.evaluation.schemas import EvaluationResult, EvaluatorError
from app.llm.provider import GeminiProvider, LLMProvider


class EvaluatorCallFailed(Exception):
    """Wraps a structured EvaluatorError so callers can catch one
    exception type and still access attempt_number/raw_response/
    error_message for the halted-run record."""

    def __init__(self, error: EvaluatorError) -> None:
        self.error = error
        super().__init__(error.error_message)


def _extract_json(raw: str) -> str:
    """The prompt instructs raw JSON only, but strip markdown code fences
    defensively in case the model wraps the object anyway."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def evaluate_lesson(
    topic: str,
    grounding_context: list[str],
    lesson: str,
    attempt_number: int,
    provider: LLMProvider | None = None,
) -> EvaluationResult:
    provider = provider or GeminiProvider(model=EVALUATOR_MODEL)
    prompt = EVALUATOR_PROMPT.format(
        topic=topic,
        grounding_context="\n\n".join(grounding_context),
        lesson=lesson,
    )

    last_raw = ""
    last_error = ""
    for _ in range(2):
        try:
            raw = provider.generate(prompt, max_tokens=EVALUATOR_MAX_TOKENS)
            last_raw = raw
            payload = json.loads(_extract_json(raw))
            return EvaluationResult.model_validate(payload)
        except (json.JSONDecodeError, ValidationError, RuntimeError) as e:
            last_error = str(e)
            continue

    raise EvaluatorCallFailed(
        EvaluatorError(
            attempt_number=attempt_number,
            raw_response=last_raw,
            error_message=last_error,
        )
    )
