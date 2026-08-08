"""
Centralized configuration for the self-evaluating lesson generator.

Every tunable value used anywhere in this codebase must be read from
here, not hardcoded inline in generator.py, evaluator.py, retriever.py,
nodes.py, main.py, or anywhere else. This is the single source of truth
so that changing e.g. TOP_K or MAX_RETRIES means editing one line in
.env, not hunting through multiple files.

If a future design decision changes one of these values (or adds a new
tunable), update BOTH this file and the corresponding .env.example entry
together, so they never drift out of sync.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def _get_int(key: str, default: int) -> int:
    return int(os.environ.get(key, default))


def _get_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


# ---------------------------------------------------------------------------
# Model provider
# ---------------------------------------------------------------------------

GENERATOR_MODEL = os.environ.get("GENERATOR_MODEL", "gemini-2.5-flash")
EVALUATOR_MODEL = os.environ.get("EVALUATOR_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your "
        "Gemini API key from Google AI Studio (no credit card required)."
    )

# ---------------------------------------------------------------------------
# Token limits
# ---------------------------------------------------------------------------

GENERATOR_MAX_TOKENS = _get_int("GENERATOR_MAX_TOKENS", 2500)
EVALUATOR_MAX_TOKENS = _get_int("EVALUATOR_MAX_TOKENS", 2200)
MEMORY_MAX_TOKENS = _get_int("MEMORY_MAX_TOKENS", 400)

# ---------------------------------------------------------------------------
# Retrieval / chunking (see ARCHITECTURE.md Section 1a)
# ---------------------------------------------------------------------------

CHUNK_SIZE_TOKENS = _get_int("CHUNK_SIZE_TOKENS", 300)
CHUNK_OVERLAP_TOKENS = _get_int("CHUNK_OVERLAP_TOKENS", 50)
TOP_K = _get_int("TOP_K", 4)

CHUNK_SEPARATORS = ["\n## ", "\n### ", "\n\n", ". ", " ", ""]

KNOWLEDGE_BASE_PATH = "knowledge/rag_reference.md"

# ---------------------------------------------------------------------------
# Retry / rubric
# ---------------------------------------------------------------------------

MAX_RETRIES = _get_int("MAX_RETRIES", 2)
RUBRIC_VERSION = os.environ.get("RUBRIC_VERSION", "v2")

# ---------------------------------------------------------------------------
# LangSmith (optional — see CLAUDE.md build order step 15 for when this is
# actually verified/relied upon; scaffolded early since it's free to set)
# ---------------------------------------------------------------------------

LANGCHAIN_TRACING_V2 = _get_bool("LANGCHAIN_TRACING_V2", False)
LANGCHAIN_API_KEY = os.environ.get("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.environ.get("LANGCHAIN_PROJECT", "content-quality-agent")

# ---------------------------------------------------------------------------
# Input guardrails (see ARCHITECTURE.md Section 9)
# ---------------------------------------------------------------------------

MAX_TOPIC_LENGTH = 200

SUSPICIOUS_PATTERNS = [
    "ignore previous instructions",
    "ignore the above",
    "system prompt",
    "reveal your instructions",
    "disregard your rules",
    "you are now",
]

# ---------------------------------------------------------------------------
# Demo mode (for the Loom deliberate-failure demonstration)
# ---------------------------------------------------------------------------

# One of: "off", "accuracy_failure", "jargon_failure"
DEMO_MODE = os.environ.get("DEMO_MODE", "off")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

MEMORY_FILE_PATH = "memory/failure_patterns.json"
LOGS_DIR = "logs"
OUTPUT_DIR = "output"
