from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Query, HTTPException

from src.services.serp_service import SerpService
from src.services.tavily_service import TavilyService
from src.services.search_gateway import SearchGateway
from src.cache import CacheManager
from src.utils.rate_limiter import RateLimiter

app = FastAPI(title="ContentAlchemy Search MCP", version="0.1.0")


def build_gateway() -> SearchGateway:
    # Configurable via env vars
    ttl = int(os.getenv("SEARCH_CACHE_TTL", "300"))
    rpm = int(os.getenv("SEARCH_RPM", "30"))
    api_key = os.getenv("SERPAPI_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    cache = CacheManager(ttl_seconds=ttl)
    rate = RateLimiter(max_requests=rpm, window_seconds=60)
    serp = SerpService(api_key=api_key, cache=cache, rate_limiter=rate)
    providers = [serp]

    if tavily_key:
        tavily = TavilyService(api_key=tavily_key, cache=cache, rate_limiter=rate)
        providers.append(tavily)

    return SearchGateway(providers=providers, cache=cache, rate_limiter=rate)


gateway: Optional[SearchGateway] = None


def get_gateway() -> SearchGateway:
    global gateway
    if gateway is None:
        gateway = build_gateway()
    return gateway


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/search")
async def search(q: str = Query(..., min_length=2), num: int = Query(5, ge=1, le=20)):
    try:
        gw = get_gateway()
        results = await gw.search(q, num_results=num)
        return {
            "query": q,
            "count": len(results),
            "results": [r.to_dict() if hasattr(r, "to_dict") else r for r in results],
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


# To run:
# uvicorn src.mcp.search_server:app --reload --port 8001
