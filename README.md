> This repository is intended for learning, experimentation, and reference purposes. It is not designed as a production-grade system.

# multi-agent-content-lab

A learning project demonstrating how to build a multi-agent AI system that generates research-backed blog posts, LinkedIn content, and images from a single natural language query.

## Overview

This project shows how a set of specialized AI agents can be orchestrated to break a complex content creation task into discrete, composable steps  from intent classification and web research to writing, formatting, and visual generation.

Each agent has a single responsibility. They are connected via a LangGraph state machine, share state through a typed dictionary, and are exposed through a FastAPI backend with a Streamlit frontend.

**Why this problem matters:** In real-world systems, complex tasks rarely fit inside a single LLM call. Multi-agent architectures allow you to decompose problems, apply specialized prompting, add caching and rate limiting per step, and make the pipeline observable and testable.

## Real-World Context

Multi-agent content pipelines are used in production by:
- Marketing automation platforms (e.g., Jasper, Copy.ai) that generate brand-consistent content at scale
- SEO tools that combine research, writing, and image generation in a single workflow
- Enterprise CMS systems that use LLM agents to draft, review, and publish structured content

This repo simplifies those patterns to make them understandable and runnable on a laptop.

## What This Repo Demonstrates

- **Multi-agent orchestration** using LangGraph (state machine with typed shared state)
- **LLM gateway pattern**  provider abstraction over OpenAI, Azure OpenAI, and Gemini with automatic failover
- **Circuit breaker + rate limiter**  defensive patterns for unreliable external APIs
- **In-memory TTL cache**  avoiding redundant API calls during a workflow run
- **Intent classification**  routing queries to the right agent(s) based on content type
- **SEO utilities**  keyword embedding, meta description generation, slug creation
- **FastAPI REST backend**  stateless HTTP API with API key auth and request rate limiting
- **Streamlit UI**  thin frontend calling the backend; demonstrates frontend/backend separation
- **Structured testing**  unit tests for utilities, agents, and services; DeepEval for LLM output quality

## Architecture / Component Flow

```
User Query (Streamlit UI or direct HTTP)
        |
        v
+----------------------------------+
|  FastAPI Backend  /run           |
|  - API key auth                  |
|  - Rate limiter                  |
+----------------------------------+
               |
               v invoke LangGraph
+----------------------------------+
|  QueryHandlerAgent               |
|  - Classifies intent             |
|  - Decides: blog / linkedin /    |
|    image / research / multi      |
+----------------------------------+
               |
               v routes to
+----------------------------------+
|  ResearchAgent                   |
|  - Calls SearchGateway           |
|    (SERP API -> Tavily fallback) |
|  - Synthesizes findings          |
|  - Adds sources + key points     |
+----------------------------------+
               |
       +-------+--------+
       v                v
+------------+  +------------------+
| ImageAgent |  | BlogWriterAgent  |
| DALL-E 3   |  | + SEO optimizer  |
+------------+  +------------------+
      |                  |
      +----+-------------+
           v
  +------------------------+
  |  LinkedInAgent         |
  |  post + hashtags       |
  +------------------------+
             |
             v
  +------------------------+
  |  StrategistAgent       |
  |  summary + next steps  |
  +------------------------+
             |
             v
     JSON Response to caller
```

**Step-by-step flow:**
1. User submits a natural language query (e.g., _"Write a blog + LinkedIn post about AI in healthcare"_)
2. `QueryHandlerAgent` classifies intent and determines which content types to generate
3. `ResearchAgent` fetches and synthesizes web results using a failover search gateway
4. `ImageAgent` generates a DALL-E image using an LLM-enhanced prompt
5. `BlogWriterAgent` produces an SEO-optimized markdown article from the research
6. `LinkedInAgent` writes a concise post with hashtags
7. `StrategistAgent` assembles all outputs into a structured summary with next actions
8. The FastAPI `/run` endpoint returns the full result as JSON

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph, LangChain |
| LLM Providers | OpenAI GPT-4o-mini, Azure OpenAI, Google Gemini |
| Image Generation | OpenAI DALL-E 3 |
| Web Search | SerpAPI, Tavily |
| Backend API | FastAPI, Uvicorn |
| Frontend | Streamlit |
| Observability | LangSmith |
| Testing | pytest, pytest-asyncio, DeepEval |
| Config | python-dotenv, Pydantic |

## Project Structure

```
multi-agent-content-lab/
|-- app.py                    # Streamlit frontend
|-- requirements.txt          # Python dependencies
|-- start.bat                 # Windows startup script (runs backend + UI)
|-- .env.example              # Environment variable template
|-- config/
|   |-- settings.py           # App-wide settings loaded from .env
|   `-- agent_config.py       # Per-agent model/parameter configs
|-- src/
|   |-- api/
|   |   `-- server.py         # FastAPI app: /run endpoint, auth, rate limiting
|   |-- agents/
|   |   |-- base_agent.py     # Abstract base class: input/output schemas, run()
|   |   |-- query_handler_agent.py  # Intent classification and routing
|   |   |-- research_agent.py       # Web research + synthesis
|   |   |-- blog_writer_agent.py    # SEO blog generation
|   |   |-- linkedin_agent.py       # LinkedIn post generation
|   |   |-- image_agent.py          # DALL-E image generation
|   |   `-- strategist_agent.py     # Output assembly + next actions
|   |-- graph/
|   |   |-- agent_graph.py    # LangGraph workflow wiring (nodes + edges)
|   |   `-- state_manager.py  # Conversation history + session context
|   |-- services/
|   |   |-- llm_gateway.py    # Multi-provider LLM abstraction with failover
|   |   |-- search_gateway.py # Multi-provider search with failover
|   |   |-- serp_service.py   # SerpAPI integration
|   |   |-- tavily_service.py # Tavily integration
|   |   `-- dalle_service.py  # DALL-E image generation service
|   |-- cache/
|   |   `-- cache_manager.py  # In-memory TTL cache
|   `-- utils/
|       |-- circuit_breaker.py      # Circuit breaker pattern
|       |-- rate_limiter.py         # Sliding-window rate limiter
|       |-- seo_optimizer.py        # Keyword embedding, slugs, meta descriptions
|       |-- blog_generator.py       # Blog outline + markdown rendering
|       |-- hashtag_engine.py       # Topic-based hashtag generation
|       |-- linkedin_formatter.py   # LinkedIn post formatting
|       |-- intent_classifier.py    # Rule-based + LLM-assisted intent detection
|       |-- brand_voice.py          # Brand voice profile + consistency checking
|       |-- content_quality_checker.py  # Readability + quality scoring
|       |-- research_synthesizer.py # Search result synthesis
|       |-- report_formatter.py     # Structured research report formatting
|       |-- text_processor.py       # Text cleaning and normalization
|       |-- prompt_manager.py       # Prompt template management
|       |-- prompt_optimizer.py     # Prompt enhancement for image generation
|       |-- image_manager.py        # Image metadata tracking
|       `-- observability.py        # Tracing spans and event recording
|-- tests/
|   |-- test_circuit_breaker.py
|   |-- test_rate_limiter.py
|   |-- test_cache_manager.py
|   |-- test_seo_utils.py
|   |-- test_research_agent.py
|   |-- test_blog_writer_agent.py
|   |-- test_linkedin_agent.py
|   |-- test_image_agent.py
|   |-- test_llm_gateway.py
|   `-- deepeval_tests/         # LLM output quality tests using DeepEval
`-- doc/
    |-- architecture.md         # Detailed architecture notes
    `-- implementation_guide.md # Step-by-step implementation walkthrough
```

## How to Run Locally

### Prerequisites

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [SerpAPI key](https://serpapi.com/) (for web research)

### Quickest path (Windows)

```bash
# 1. Copy environment template
copy .env.example .env

# 2. Edit .env and add at minimum:
#    OPENAI_API_KEY=sk-...
#    SERPAPI_API_KEY=...

# 3. Run everything (creates venv, installs deps, starts backend + UI)
start.bat
```

Backend will be at `http://localhost:8000` and the UI at `http://localhost:8501`.

### Manual setup (cross-platform)

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env and fill in API keys

# Start the FastAPI backend (terminal 1)
uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# Start the Streamlit UI (terminal 2)
streamlit run app.py
```

## How to Run Tests

```bash
# Activate your virtual environment first
source venv/bin/activate   # or venv\Scripts\activate on Windows

# Run all unit tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Run a specific test file
pytest tests/test_circuit_breaker.py -v

# Run DeepEval LLM quality tests (requires OPENAI_API_KEY)
pytest tests/deepeval_tests/ -v
```

## Example Usage

### Via Streamlit UI

1. Open `http://localhost:8501`
2. Type a query: _"Write a comprehensive blog post and LinkedIn update about the future of remote work, include an image"_
3. Check the content type toggles (Blog, LinkedIn, Images)
4. Click **Run workflow**

### Via API (curl)

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Write a blog post about AI in healthcare",
    "generate_blog": true,
    "generate_linkedin": true,
    "generate_images": false
  }'
```

### Direct FastAPI docs

Visit `http://localhost:8000/docs` to explore the interactive Swagger UI.

## Learning Outcomes

After studying this codebase you will understand:

- How to design a **multi-agent pipeline** using LangGraph's stateful graph
- How a **gateway pattern** abstracts multiple LLM providers behind a single interface
- How **circuit breakers and rate limiters** protect downstream APIs from cascading failures
- How to structure an **async Python application** with FastAPI and async agents
- How to write **testable agent code** by injecting dependencies rather than hard-wiring them
- How to use **DeepEval** to evaluate the quality of LLM-generated outputs beyond simple unit tests
- How **in-memory caching** improves throughput and reduces cost in multi-step pipelines

## Limitations

This is a learning project. It is explicitly **not production-ready**:

- **No persistent storage**  state is in-memory and lost on restart
- **No authentication system**  the API key check is a simplified placeholder
- **No async safety for shared state**  the in-memory cache and rate limiter are not thread-safe under high concurrency
- **No retry logic**  failed LLM calls fall through to the next provider but are not retried independently
- **Search results are not verified**  the research agent uses whatever the search API returns without fact-checking
- **Single-node only**  the architecture assumes one process; horizontal scaling would require external state (Redis, etc.)
- **LLM outputs are non-deterministic**  generated content quality depends on model availability and prompts

## Future Improvements

- Replace in-memory cache with Redis for multi-instance support
- Add persistent session storage (PostgreSQL or SQLite)
- Implement proper retry with exponential backoff per provider
- Add a content approval step (human-in-the-loop node in the graph)
- Stream responses back to the UI instead of waiting for full completion
- Add prompt versioning and A/B testing for content quality improvement

## License

This project is licensed under the MIT License  see the [LICENSE](LICENSE) file for details.
