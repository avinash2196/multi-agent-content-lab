from __future__ import annotations

import os
import uuid
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from config import settings
from src.graph.agent_graph import AgentGraph
from src.utils.observability import Observability
from src.utils.rate_limiter import RateLimiter

app = FastAPI(title="ContentAlchemy API", version="0.1.0")

# Shared dependencies
observability = Observability()
rate_limiter = RateLimiter(max_requests=settings.backend_rpm, window_seconds=60)

graph = AgentGraph()
compiled_graph = graph.compile()


class RunRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    generate_images: bool = True
    generate_alt_text: bool = True
    generate_blog: bool = True
    generate_linkedin: bool = True
    linkedin_with_images: bool = False


class RunResponse(BaseModel):
    session_id: str
    final_output: Dict[str, Any]
    research_results: Optional[Dict[str, Any]]
    blog_content: Optional[str]
    linkedin_content: Optional[str]
    image_urls: Optional[list]
    errors: list


def require_api_key(x_api_key: Optional[str] = Header(None)):
    if settings.backend_api_key and settings.backend_api_key.strip():
        if not x_api_key or x_api_key != settings.backend_api_key:
            raise HTTPException(status_code=401, detail="invalid_api_key")
    return True


def build_initial_state(query: str, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "messages": [],
        "current_query": query,
        "session_id": session_id,
        "context": context,
        "routing_decision": None,
        "research_results": None,
        "blog_content": None,
        "linkedin_content": None,
        "image_urls": None,
        "final_output": None,
        "errors": [],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run_workflow(payload: RunRequest, _: bool = Depends(require_api_key)):
    if not rate_limiter.allow():
        raise HTTPException(status_code=429, detail="rate_limited")

    session_id = payload.session_id or str(uuid.uuid4())
    ctx = {**(payload.context or {})}
    ctx.setdefault("generate_images", payload.generate_images)
    ctx.setdefault("generate_alt_text", payload.generate_alt_text)
    ctx.setdefault("generate_blog", payload.generate_blog)
    ctx.setdefault("generate_linkedin", payload.generate_linkedin)
    ctx.setdefault("linkedin_with_images", payload.linkedin_with_images)

    state = build_initial_state(payload.query, session_id, ctx)

    try:
        with observability.span("api.run", {"session_id": session_id}):
            result = await compiled_graph.ainvoke(state)
        return RunResponse(
            session_id=session_id,
            final_output=result.get("final_output") or {},
            research_results=result.get("research_results"),
            blog_content=result.get("blog_content") if payload.generate_blog else None,
            linkedin_content=result.get("linkedin_content") if payload.generate_linkedin else None,
            image_urls=result.get("image_urls"),
            errors=result.get("errors") or [],
        )
    except Exception as e:  # noqa: BLE001
        observability.record_error("api.run.error", e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("BACKEND_PORT", "8000"))
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=port, reload=False)
