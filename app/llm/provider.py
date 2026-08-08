"""
Swappable LLM provider abstraction.

Both the generator and evaluator call an LLM only through this interface,
never the Gemini SDK directly, so a future swap to a different provider
(once billing exists -- see CLAUDE.md "Non-negotiable constraints") is a
config change, not a redesign.
"""

from abc import ABC, abstractmethod

from google import genai
from google.genai import types

from app.config import GOOGLE_API_KEY, THINKING_BUDGET_TOKENS


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, max_tokens: int) -> str:
        """Return the raw text response for a single-turn prompt."""


class GeminiProvider(LLMProvider):
    def __init__(self, model: str) -> None:
        self._client = genai.Client(api_key=GOOGLE_API_KEY)
        self._model = model

    def generate(self, prompt: str, max_tokens: int) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                thinking_config=types.ThinkingConfig(
                    thinking_budget=THINKING_BUDGET_TOKENS
                ),
            ),
        )
        if not response.text:
            finish_reason = response.candidates[0].finish_reason if response.candidates else None
            raise RuntimeError(
                f"Gemini returned no text (finish_reason={finish_reason})"
            )
        return response.text
