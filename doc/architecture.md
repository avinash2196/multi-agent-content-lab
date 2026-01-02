# ContentAlchemy System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                      User Layer                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐         ┌──────────────────────────┐          │
│  │  Streamlit UI    │         │  FastAPI Backend         │          │
│  │  :8501           │◄────────│  :8000                   │          │
│  │  - Query Input   │         │  - /run endpoint         │          │
│  │  - Content View  │         │  - API auth + rate limit │          │
│  │  - Session Mgmt  │         │  - Health checks         │          │
│  └──────────────────┘         └──────────────────────────┘          │
│         │                              │                             │
│         └──────────────┬───────────────┘                             │
│                        │ HTTP/JSON                                   │
└────────────────────────┼───────────────────────────────────────────┘
                         │
┌────────────────────────┼───────────────────────────────────────────┐
│                        ▼                                            │
│              LangGraph Orchestration                                │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │                    Agent Graph                             │     │
│  │                                                            │     │
│  │  ┌─────────────┐     ┌──────────────┐                     │     │
│  │  │   Query     │────►│  Research    │                     │     │
│  │  │   Handler   │     │   Agent      │                     │     │
│  │  └─────────────┘     └──────────────┘                     │     │
│  │         │                    │                            │     │
│  │         ▼                    ▼                            │     │
│  │  Route Decision      ┌──────────────┐                     │     │
│  │         │            │    Image     │                     │     │
│  │         └───────────►│   Agent      │                     │     │
│  │                      └──────────────┘                     │     │
│  │                           │                              │     │
│  │         ┌─────────────────┼─────────────────┐            │     │
│  │         ▼                 ▼                 ▼            │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │     │
│  │  │    Blog      │  │  LinkedIn    │  │ Strategist   │    │     │
│  │  │    Writer    │  │    Writer    │  │    Agent     │    │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘    │     │
│  │         │                 │                 ▲             │     │
│  │         └─────────────────┼─────────────────┘             │     │
│  │                           │                              │     │
│  │                    Final Output                          │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## Agent Architecture

### 1. Query Handler Agent
- **Input**: User query (string)
- **Process**: LLM-based intent classification
- **Output**: Routing decision + topic + context
- **Routing Map**:
  - `research_agent` → Multi-stage research
  - `blog_writer_agent` → Blog generation (flows to research first)
  - `linkedin_writer_agent` → LinkedIn post (flows to research first)
  - `image_agent` → Image generation
  - `strategist_agent` → Content synthesis only
  - `multi` → Multi-format workflow

### 2. Research Agent
- **Input**: Topic + search query
- **Process**:
  - Multi-provider search (SERP → Tavily fallback)
  - Result caching (TTL configurable)
  - Research synthesis and key point extraction
- **Output**: Research summary, key points, sources
- **Resilience**: Circuit breaker, rate limiting

### 3. Blog Writer Agent
- **Input**: Query + research results + key points
- **Process**:
  1. Build content outline from key points
  2. Generate full article via LLM (1500-2000 words)
  3. SEO optimization (keyword embedding)
  4. Brand voice checking + optional rewriting
  5. Quality assessment
- **Output**: Markdown blog post with metadata

### 4. LinkedIn Agent
- **Input**: Query + research results + key points
- **Process**:
  1. Generate engaging post via LLM (250-350 words)
  2. Add hashtags (trending + topic-relevant)
  3. Optional image attachment (if `linkedin_with_images=true`)
  4. Brand voice checking + optional rewriting
- **Output**: LinkedIn post text (plain + hashtags)

### 5. Image Agent
- **Input**: Query + style + aspect ratio
- **Process**:
  1. Optimize prompt via PromptOptimizer
  2. Call DALL-E 3 for image generation
  3. Store in ImageManager with metadata
  4. Generate alt-text via LLM (if enabled)
- **Output**: Image URLs + metadata

### 6. Strategist Agent
- **Input**: All previous outputs (research, blog, LinkedIn, images)
- **Process**:
  1. Summarize content package
  2. Surface research highlights
  3. List managed images with alt-text
  4. Suggest cross-platform optimizations
- **Output**: Strategy summary + recommendations

## Service Layer

### LLM Gateway
```
Request
   │
   ▼
┌──────────────────────────┐
│  LLM Gateway             │
│ (Rate limiting)          │
└──────────────────────────┘
   │
   ├─► OpenAI Provider (primary)
   │
   ├─► Azure OpenAI Provider (fallback)
   │
   └─► Gemini Provider (fallback)
   
Response (first success or error)
```

**Features**:
- Sliding-window rate limiting (configurable RPM)
- Circuit breaker for cascading failure prevention
- LangSmith observability hooks
- Automatic failover to next provider

### Search Gateway
```
Query
  │
  ▼
┌─────────────────────┐
│  Cache Check        │
│  (TTL seconds)      │
└─────────────────────┘
  │
  ├─► Hit: Return cached result
  │
  └─► Miss:
      ▼
      ┌─────────────────────┐
      │  Rate Limiter       │
      └─────────────────────┘
          │
          ▼
      ┌─────────────────────┐
      │  SERP Provider      │ (primary)
      └─────────────────────┘
          │
          ├─► Success: Cache + return
          │
          └─► Failure:
              ▼
              ┌─────────────────────┐
              │  Tavily Provider    │ (fallback)
              └─────────────────────┘
```

## Data Flow

### Full Workflow (Multi-format)

```
User Query
   │
   ▼
Query Handler
   │
   ├─► Intent Classification (LLM)
   ├─► Topic Extraction
   ├─► Context Enrichment
   │
   ▼
Route Decision
   │
   ├─ research_agent, blog_writer_agent, linkedin_writer_agent
   │
   ▼
Research Agent
   │
   ├─► Search Query (SERP/Tavily)
   ├─► Aggregate Results
   ├─► Extract Key Points
   ├─► Synthesize Summary
   │
   ▼
Image Agent
   │
   ├─► Optimize Prompt
   ├─► Call DALL-E 3
   ├─► Store Metadata
   ├─► Generate Alt-Text (optional)
   │
   ▼
Blog Writer Agent
   │
   ├─► Build Outline
   ├─► LLM Article Generation (1500-2000 words)
   ├─► SEO Optimization
   ├─► Brand Voice Check
   │
   ▼
LinkedIn Agent
   │
   ├─► LLM Post Generation (250-350 words)
   ├─► Hashtag Generation
   ├─► Image Attachment (optional)
   ├─► Brand Voice Check
   │
   ▼
Strategist Agent
   │
   ├─► Summarize Package
   ├─► Surface Key Assets
   ├─► Recommendations
   │
   ▼
Response to Client
   │
   ├─ research_results
   ├─ blog_content
   ├─ linkedin_content
   ├─ image_urls
   ├─ final_output (strategy)
   └─ errors (if any)
```

## Technology Stack

| Component | Technology | Alternative |
|-----------|------------|-------------|
| Orchestration | LangGraph | CrewAI, AutoGen |
| LLM | OpenAI GPT-4o-mini | Azure, Gemini, Claude |
| Search | SERP API | Perplexity, You.com, Tavily |
| Images | DALL-E 3 | Midjourney, Stability, Google Imagen |
| Web Framework | FastAPI | Flask, Django |
| Frontend | Streamlit | Gradio, React |
| Observability | LangSmith | Weights & Biases, Helicone |
| State | In-memory | Redis, PostgreSQL |

## Resilience Patterns

### 1. Circuit Breaker
```
Closed (normal)
   │
   ├─► Failure threshold exceeded
   ▼
Open (blocking)
   │
   ├─► After timeout, allow one request
   ▼
Half-Open (testing)
   │
   ├─► Success → Closed
   └─► Failure → Open
```

### 2. Rate Limiting
- **Algorithm**: Sliding window token bucket
- **Per-service configuration**: SERP_RPM, LLM_RPM, SEARCH_CACHE_TTL
- **Enforcement**: Blocks/delays requests when limit exceeded

### 3. Failover
- **Search**: SERP → Tavily
- **LLM**: OpenAI → Azure → Gemini
- **Automatic**: No user intervention required

## Configuration

### Environment Variables

```env
# LLM Providers
OPENAI_API_KEY=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=...
GEMINI_API_KEY=...

# Search
SERPAPI_API_KEY=...
TAVILY_API_KEY=...

# Observability
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=...

# Rate Limits (requests per minute)
LLM_RPM=60
SEARCH_RPM=30
BACKEND_RPM=60

# Caching
SEARCH_CACHE_TTL=300 (seconds)

# Backend
BACKEND_API_KEY=... (optional, for auth)
BACKEND_PORT=8000
```

### Agent Configuration

Each agent can accept config dict:
```python
config = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "use_llm_polish": True,
    "max_tokens": 3000,
    "brand_voice": {
        "tone": "professional",
        "style": "conversational"
    }
}
```

## Deployment Considerations

### Local Development
- Single machine with venv
- In-memory state (lost on restart)
- Suitable for prototyping and testing

### Production
- Containerized (Docker/Kubernetes)
- Distributed state (Redis/PostgreSQL)
- Load balancing for API
- Horizontal scaling of agents
- CDN for image distribution
- Monitoring and alerting

### Cost Optimization
- Cache search results aggressively
- Rate limit to reduce LLM calls
- Prefer faster/cheaper models for polish tasks
- Monitor token usage via LangSmith
- Batch requests when possible

## Quality Assurance & Testing

### Unit Testing (77 tests, 73% coverage)
- **Agent Testing**: Individual agent functionality and error handling
- **Service Testing**: LLM gateway, search gateway, image services
- **Integration Testing**: End-to-end workflows and API endpoints
- **Resilience Testing**: Circuit breaker, rate limiting, fallback mechanisms

### DeepEval LLM Quality Evaluation (24 tests)
- **Research Quality**: AnswerRelevancyMetric, FaithfulnessMetric, ContextualRelevancyMetric
- **Content Quality**: Coherence, toxicity detection, brand voice consistency
- **Platform Optimization**: SEO integration, hashtag quality, engagement elements
- **Safety & Ethics**: Toxicity monitoring across all content formats

### Quality Metrics
- **AnswerRelevancyMetric**: Content relevance to queries (threshold: 0.5-0.7)
- **FaithfulnessMetric**: Factual accuracy and source alignment (threshold: 0.6-0.7)
- **ToxicityMetric**: Content safety monitoring (threshold: <0.3)
- **ContextualRelevancyMetric**: Context-aware evaluation (threshold: 0.7)

### Test Execution
```bash
# Unit tests
pytest tests/ --cov=src --cov-report=html

# DeepEval quality tests
pytest tests/deepeval_tests/ -v

# Combined testing
pytest tests/ tests/deepeval_tests/ -v
```

## Future Enhancements

1. **Streaming Responses**: Return content as generated instead of waiting
2. **Webhook Callbacks**: Async execution with result delivery
3. **Content Templates**: Domain-specific workflows (e-commerce, SaaS, etc.)
4. **Multi-language**: Translate content to multiple languages
5. **Social Scheduling**: Direct publishing to Buffer/Hootsuite
6. **Analytics**: Track content performance metrics
7. **Vector Database**: Semantic search over generated content
8. **Fine-tuned Models**: Custom LLMs for specific domains
