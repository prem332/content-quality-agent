"""
Failure-pattern memory: bounded, summarized, deterministic (see
ARCHITECTURE.md Section 7). Loading is implemented now (needed for the
graph loop to run end-to-end, build step 9); saving/updating patterns
after a FAIL via the deterministic CHECK_TO_PATTERN mapping is added in
build step 10.
"""

import json
import os

from app.config import MEMORY_FILE_PATH
from app.evaluation.schemas import FailurePattern, Memory


def load_top_patterns(limit: int = 5) -> list[FailurePattern]:
    if not os.path.exists(MEMORY_FILE_PATH):
        return []
    with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Memory.model_validate(data).top_patterns(limit=limit)
