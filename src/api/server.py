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

app = FastAPI(
    title="multi-agent-content-lab API",
    version="0.1.0",
    description=(
        "FastAPI backend for the multi-agent content generation pipeline. "
        "Exposes a single /run endpoint that triggers the full LangGraph workflow. "
        "See README for setup instructions."
    ),
)

# ---------------------------------------------------------------------------
# Shared singletons
# ---------------------------------------------------------------------------
# These are created once at startup and shared across requests.
# In a production service you would typically use FastAPI's dependency
# injection system (lifespan events) rather than module-level globals.
observability = Observability()
rate_limiter = RateLimiter(max_requests=settings.backend_rpm, window_seconds=60)

graph = AgentGraph()
compiled_graph = graph.compile()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RunRequest(BaseModel):
    """Payload for the POST /run endpoint.

    All boolean flags default to True so a minimal request only needs
    a ``query`` string.
    """

    query: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    generate_images: bool = True
    generate_alt_text: bool = True
    generate_blog: bool = True
    generate_linkedin: bool = True
    linkedin_with_images: bool = False


class RunResponse(BaseModel):
    """Structured response returned after the pipeline completes.

    Fields are Optional because some outputs are conditionally generated
    (e.g., ``blog_content`` is None when ``generate_blog=False``).
    """

    session_id: str
    final_output: Dict[str, Any]
    research_results: Optional[Dict[str, Any]]
    blog_content: Optional[str]
    linkedin_content: Optional[str]
    image_urls: Optional[list]
    errors: list


# ---------------------------------------------------------------------------
# Dependency functions
# ---------------------------------------------------------------------------

def require_api_key(x_api_key: Optional[str] = Header(None)):
    """FastAPI dependency that enforces the optional API key guard.

    If ``BACKEND_API_KEY`` is not set in the environment, auth is disabled and
    all requests are allowed.  This is intentional for local development.

    Design note:
        For a production service you would want a proper auth layer
        (OAuth2, JWT, etc.) rather than a single shared secret.
    """
    if settings.backend_api_key and settings.backend_api_key.strip():
        if not x_api_key or x_api_key != settings.backend_api_key:
            raise HTTPException(status_code=401, detail="invalid_api_key")
    return True


def build_initial_state(query: str, session_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Construct the initial LangGraph AgentState dict for a new workflow run.

    LangGraph requires all state keys to be present at graph entry so that
    nodes can safely read them without KeyError.
    """
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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Liveness probe — returns 200 OK when the server is running."""
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run_workflow(payload: RunRequest, _: bool = Depends(require_api_key)):
    """Trigger the full multi-agent content generation pipeline.

    Request lifecycle:
        1. Rate limiter check — rejects with 429 if over the configured RPM.
        2. Build initial LangGraph state from the request payload.
        3. Invoke the compiled graph asynchronously (``ainvoke``).
        4. Extract the relevant fields from the final state and return.

    Scalability note:
        This endpoint is stateless — each call gets an independent session ID
        and graph invocation.  Horizontal scaling is straightforward as long as
        the rate limiter is moved to an external store (Redis) so limits are
        shared across instances.
    """
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
