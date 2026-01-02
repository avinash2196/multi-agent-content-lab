# ContentAlchemy – Multi-Agent Content Creation Platform

AI-powered multi-agent system that generates research-backed SEO blogs, engaging LinkedIn posts, and AI-optimized images with a unified backend API and Streamlit UI.

## 🎯 Features

- **Six Specialized Agents**
  - Query Handler: Intent routing and classification
  - Research Agent: Web research via SERP + Tavily with synthesis
  - Blog Writer Agent: 1500-2000 word SEO-optimized articles with LLM generation
  - LinkedIn Agent: Engaging 250-350 word posts designed for conversation
  - Image Agent: DALL-E 3 images with optional alt-text generation
  - Strategist Agent: Content synthesis and cross-platform recommendations

- **FastAPI Backend** with:
  - RESTful `/run` endpoint for content generation
  - API key authentication
  - Rate limiting (configurable RPM)
  - LangSmith observability hooks
  - Health checks and monitoring

- **Streamlit Web UI** with:
  - Natural language query interface
  - Individual toggles for blog, LinkedIn, images, alt-text
  - Real-time research display
  - Generated content preview and download
  - Session management

- **Multi-LLM Gateway** supporting:
  - OpenAI (primary)
  - Azure OpenAI (fallback)
  - Google Gemini (fallback)
  - Automatic failover with circuit breakers
  - Rate limiting and caching

- **Robust Search**
  - SERP API + Tavily gateway with failover
  - Caching with TTL configuration
  - Rate limiting per provider

- **Quality Assurance & Testing**
  - 73% code coverage with 77 comprehensive unit tests
  - DeepEval LLM evaluation suite with 24 quality metrics
  - AnswerRelevancyMetric, FaithfulnessMetric, ToxicityMetric, ContextualRelevancyMetric
  - End-to-end content quality validation across all formats

## 🚀 Quick Start

### 1. Setup

```bash
# Clone and navigate
cd content-writing

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env  # Windows
# cp .env.example .env   # macOS/Linux
```

### 2. Environment Configuration

Edit `.env`:

```env
# Required
OPENAI_API_KEY=sk-...
SERPAPI_API_KEY=...

# Optional but recommended
TAVILY_API_KEY=...
GEMINI_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_VERSION=2024-02-15
AZURE_OPENAI_DEPLOYMENT=...

# Observability
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=contentalchemy

# Backend
BACKEND_API_KEY=your-secret-key  # Optional
BACKEND_RPM=60
BACKEND_PORT=8000

# Search
SEARCH_CACHE_TTL=300
SEARCH_RPM=30
LLM_RPM=60

# Quality Evaluation (DeepEval)
DEEPEVAL_API_KEY=...  # Optional, for advanced metrics
```

### 3. Run

**Option A: Dual-window startup (backend + UI)**
```bash
start.bat  # Windows launches both in separate terminals
```

**Option B: Manual**
```bash
# Terminal 1: Backend (FastAPI)
uvicorn src.api.server:app --host 0.0.0.0 --port 8000

# Terminal 2: Frontend (Streamlit)
set BACKEND_URL=http://localhost:8000
streamlit run app.py
```

Then open:
- **UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

## 📖 API Usage

### POST `/run` – Generate Content

**Request:**
```json
{
  "query": "Write about AI in healthcare for blog and LinkedIn",
  "session_id": "optional-uuid",
  "generate_blog": true,
  "generate_linkedin": true,
  "generate_images": true,
  "generate_alt_text": true,
  "linkedin_with_images": false
}
```

**Headers:**
```
Content-Type: application/json
x-api-key: your-secret-key  (if BACKEND_API_KEY is set)
```

**Response:**
```json
{
  "session_id": "uuid",
  "research_results": {
    "summary": "...",
    "key_points": [...],
    "sources": [...]
  },
  "blog_content": "# Full Article...",
  "linkedin_content": "Engaging post text...",
  "image_urls": ["https://..."],
  "final_output": {
    "summary": "Content package summary..."
  },
  "errors": []
}
```

### Curl Example

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-secret-key" \
  -d '{
    "query": "machine learning best practices",
    "generate_blog": true,
    "generate_linkedin": true,
    "generate_images": true
  }'
```

## 📂 Project Structure

```
content-writing/
├── src/
│   ├── api/
│   │   └── server.py              # FastAPI app with /run endpoint
│   ├── agents/
│   │   ├── base_agent.py          # Base class for all agents
│   │   ├── query_handler_agent.py # Intent routing
│   │   ├── research_agent.py      # Web research
│   │   ├── blog_writer_agent.py   # Blog generation (LLM-based)
│   │   ├── linkedin_agent.py      # LinkedIn post generation (LLM-based)
│   │   ├── image_agent.py         # Image generation + alt-text
│   │   └── strategist_agent.py    # Content synthesis
│   ├── services/
│   │   ├── llm_gateway.py         # Multi-LLM failover
│   │   ├── search_gateway.py      # Search provider abstraction
│   │   ├── serp_service.py        # SERP API client
│   │   ├── tavily_service.py      # Tavily API client
│   │   └── dalle_service.py       # DALL-E 3 wrapper
│   ├── graph/
│   │   ├── agent_graph.py         # LangGraph orchestration
│   │   ├── state_manager.py       # Session state management
│   │   └── __init__.py
│   ├── utils/
│   │   ├── blog_generator.py      # Blog template/generation
│   │   ├── brand_voice.py         # Brand consistency utilities
│   │   ├── circuit_breaker.py     # Resilience pattern
│   │   ├── image_manager.py       # Image metadata + alt-text storage
│   │   ├── rate_limiter.py        # Token bucket rate limiting
│   │   ├── observability.py       # LangSmith integration
│   │   ├── prompt_optimizer.py    # Image prompt optimization
│   │   ├── research_synthesizer.py # Research aggregation
│   │   └── text_processor.py      # Text utilities
│   ├── cache/
│   │   └── cache_manager.py       # Multi-provider caching
│   └── mcp/
│       └── search_server.py       # Optional MCP search service
├── app.py                          # Streamlit frontend
├── config/
│   └── settings.py                # Environment configuration
├── tests/
│   ├── deepeval_tests/
│   │   ├── test_research_flow.py   # Research quality evaluation
│   │   ├── test_blog_flow.py       # Blog content quality
│   │   ├── test_linkedin_flow.py   # LinkedIn post quality
│   │   ├── test_image_flow.py      # Image generation quality
│   │   ├── test_end_to_end_flow.py # End-to-end workflow quality
│   │   └── README.md               # DeepEval documentation
│   ├── test_blog_writer.py
│   ├── test_research_agent.py
│   ├── test_image_manager.py
│   └── ... (77 total unit tests)
├── doc/
│   └── implementation_guide.md    # Detailed architecture docs
├── start.bat                       # Windows launcher (both services)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── README.md                      # This file
```

## 🔧 Development

### Tests

```bash
# Unit tests (77 tests, 73% coverage)
pytest tests/ -v --tb=short          # All unit tests
pytest tests/test_blog_writer.py -v  # Specific test
pytest tests/ --cov=src --cov-report=html  # With coverage report

# DeepEval LLM quality tests (24 tests)
pytest tests/deepeval_tests/ -v      # All DeepEval tests
pytest tests/deepeval_tests/test_research_flow.py -v  # Research quality tests
pytest tests/deepeval_tests/test_blog_flow.py -v     # Blog quality tests
pytest tests/deepeval_tests/test_linkedin_flow.py -v # LinkedIn quality tests
pytest tests/deepeval_tests/test_image_flow.py -v    # Image quality tests
pytest tests/deepeval_tests/test_end_to_end_flow.py -v # End-to-end quality tests
```

### Quality Metrics

DeepEval evaluates LLM outputs across multiple dimensions:
- **AnswerRelevancyMetric**: Content relevance to input queries
- **FaithfulnessMetric**: Factual accuracy and source alignment
- **ToxicityMetric**: Content safety and appropriateness
- **ContextualRelevancyMetric**: Context-aware relevance scoring

### Logging

Set `LOG_LEVEL` in `.env`:
```env
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

### LangSmith Tracing

Provide API key to enable tracing:
```env
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=contentalchemy
```

View traces at: https://smith.langchain.com

## 🎨 Customization

### Brand Voice

Configure in agents or pass via API:
```python
# In blog_writer_agent.py or linkedin_agent.py
self.voice_profile = BrandVoiceProfile(
    tone="professional",
    style="conversational",
    preferred_vocab=["innovate", "transform", ...],
    avoid_vocab=["obviously", ...],
)
```

### Image Generation Style

Pass in request context:
```json
{
  "query": "...",
  "context": {
    "style": "photorealistic",
    "aspect_ratio": "1024x1024"
  }
}
```

## 📊 Architecture Diagram

See [doc/architecture.md](doc/architecture.md) for detailed system design.

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Commit: `git commit -am "Add feature"`
3. Push: `git push origin feature/my-feature`
4. Open Pull Request

## 📝 License

MIT

## 🆘 Troubleshooting

**Backend won't start:**
- Check `.env` has `OPENAI_API_KEY` set
- Ensure port 8000 is free: `netstat -ano | findstr :8000`

**No content generated:**
- Verify LLM API key is valid
- Check backend logs for errors
- Ensure research found results: check SERP key

**Alt-text not generating:**
- Set `GEMINI_API_KEY` or ensure OpenAI has Vision API enabled
- Check `generate_alt_text` toggle in UI

**Images not generating:**
- Verify `OPENAI_API_KEY` is set
- Check quota limits on OpenAI account
- Review image generation logs

**DeepEval tests failing:**
- Ensure all required API keys are set (OpenAI, etc.)
- Check DeepEval version compatibility: `deepeval==3.7.7`
- Some metrics may timeout on complex evaluations - this is expected
- Review test logs for specific failure reasons

**Low test coverage:**
- Run `pytest tests/ --cov=src --cov-report=html` for detailed report
- Check `htmlcov/index.html` for uncovered lines
- Add tests for newly added functionality

## 📚 Resources

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [OpenAI API](https://platform.openai.com/docs)
