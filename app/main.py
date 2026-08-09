from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import MAX_RETRIES, RUBRIC_VERSION
from app.evaluation.schemas import RunResult
from app.graph.nodes import build_run_result
from app.graph.workflow import build_graph
from app.guardrails.input import validate_topic

app = FastAPI(
    title="Content Quality Agent",
    description=(
        "Self-evaluating lesson content generator: generate -> evaluate -> "
        "regenerate loop for a beginner RAG lesson."
    ),
)

_graph = build_graph()


class GenerateRequest(BaseModel):
    topic: str


class HealthResponse(BaseModel):
    status: str


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/generate", response_model=RunResult)
def generate(request: GenerateRequest) -> RunResult:
    try:
        validate_topic(request.topic)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    initial_state = {
        "topic": request.topic,
        "grounding_context": [],
        "lesson": "",
        "rubric_version": RUBRIC_VERSION,
        "evaluation": None,
        "failed_checks": [],
        "attempt": 1,
        "max_retries": MAX_RETRIES,
        "generation_latency_seconds": 0.0,
        "memory_patterns": [],
        "attempts_log": [],
        "final_status": None,
    }
    result_state = _graph.invoke(initial_state)
    return build_run_result(result_state, result_state["final_status"])