# tstgen — Test Scenario Generator

Small prototype that fetches a Jira requirement and generates:
- **Structured test cases** (positive, negative, edge cases with JSON output)
- **Test data** with boundary values
- **Automation skeletons** for Selenium and Playwright

## Key Features

### LLM Optimization & Rate Limiting
- ✅ **Automatic retry** with exponential backoff for transient failures
- ✅ **Response caching** to reduce API calls and costs (configurable TTL)
- ✅ **Structured JSON output** for consistent, parseable test cases
- ✅ **Rate limit awareness** with automatic backoff
- ✅ **Token usage tracking** for cost monitoring
- ✅ **Timeout handling** with graceful degradation

See [LLM_OPTIMIZATION.md](LLM_OPTIMIZATION.md) for detailed documentation.

## Quick Start

### 1. Setup

```bash
# Create virtual environment
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` → `.env` and add your credentials:

```
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_USER=you@example.com
JIRA_API_TOKEN=your_api_token_here
OPENAI_API_KEY=sk-...your_openai_key_here...
OPENAI_MODEL=gpt-4o-mini
```

### 3. Run the Web UI

Start the FastAPI server + static frontend:

```bash
uvicorn server:app --reload --port 8000
```

Open **http://localhost:8000** in your browser. Enter a user story and generate test cases with positive, negative, and edge case categories.

**Features:**
- ✓ Real-time test case generation
- ✓ Rate limit status display
- ✓ Historical story references
- ✓ Mock mode (no API key required for demo)
- ✓ Selenium + Playwright automation skeletons

### 4. CLI Usage

Generate test cases from the command line:

```bash
# Standard generation (caching enabled)
python -m tstgen.cli ISSUE-123

# Disable cache for fresh responses
python -m tstgen.cli ISSUE-123 --no-cache

# Use mock output (no API calls)
python -m tstgen.cli ISSUE-123 --mock
```

Outputs are written to `outputs/ISSUE-123.md`, `.selenium.py`, `.playwright.py`.

## API Endpoints

### POST `/api/generate`
Generate test cases for a user story.

**Request:**
```json
{
  "key": "ISSUE-123",
  "summary": "User login",
  "description": "Users log in with email and password",
  "use_history": true,
  "structured_json": true
}
```

**Response includes:**
- `testcases`: Structured JSON with positive/negative/edge cases
- `testcases_markdown`: Formatted markdown for display
- `selenium_script` & `playwright_script`: Automation skeletons
- `rate_limit_status`: API usage and rate limit info
- `history`: Historical test cases from previous runs

### GET `/api/status`
Check current API usage and rate limit status.

### POST `/api/clear-cache`
Manually clear the response cache.

## File Structure

```
.
├── server.py                    # FastAPI backend
├── frontend/
│   ├── index.html              # Web UI
│   └── app.js                  # Frontend logic
├── tstgen/
│   ├── llm_client.py           # Enhanced OpenAI wrapper (retry, cache, rate limits)
│   ├── cache.py                # File-based response cache
│   ├── generator.py            # Prompt templates & structured output
│   ├── jira_client.py          # Jira REST API wrapper
│   └── cli.py                  # Command-line interface
├── test_llm_optimizations.py   # Test suite for LLM features
├── LLM_OPTIMIZATION.md         # Detailed optimization docs
└── requirements.txt
```

## LLM Optimization Highlights

### Caching
- **Impact**: 95%+ cost reduction for repeated prompts
- **Mechanism**: SHA256 hash of prompt+model → `.cache/` directory
- **TTL**: 24 hours (configurable)

```python
llm = LLMClient(cache_enabled=True, cache_ttl_hours=24)
response = llm.generate(prompt)  # API call
response = llm.generate(prompt)  # Cache hit (~10ms)
```

### Retry Logic
- **Automatic exponential backoff**: 2s, 4s, 8s between retries
- **Handles**: Rate limits, timeouts, transient API errors
- **Transparent**: No code changes needed

```python
llm = LLMClient(max_retries=3, timeout=30)
response = llm.generate(prompt)  # Retries automatically on failure
```

### Structured JSON Output
- **Format**: Consistent JSON schema for test cases
- **Validation**: Automatic JSON validation with fallback to markdown
- **Benefits**: Parseable, filterable, downstream-friendly

```json
{
  "positive_cases": [...],
  "negative_cases": [...],
  "edge_cases": [...],
  "test_data": {...}
}
```

### Rate Limit Tracking
```python
status = llm.get_rate_limit_status()
# {
#   "total_api_calls": 5,
#   "total_tokens_used": 2100,
#   "is_rate_limited": false,
#   "rate_limit_resets_in_seconds": null
# }
```

## Testing

Run the optimization test suite:

```bash
python test_llm_optimizations.py
```

Tests cache functionality, retry logic, JSON parsing, and API integration.

## Troubleshooting

**"Set OPENAI_API_KEY in environment"**
```bash
export OPENAI_API_KEY=sk-...
```

**Frequent rate limits**
- Enable caching: `cache_enabled=True`
- Increase TTL: `cache_ttl_hours=48`
- Use mock mode for testing: `--mock`

**Timeout errors**
- Increase timeout: `timeout=60`
- Check OpenAI service status

## Next Steps

See [Copilot Instructions](https://github.com/.../copilot-instructions.md) for suggested extensions:
1. Add pytest integration tests
2. Implement FastAPI async support for concurrency
3. Add Gemini / Claude provider support
4. Build jira-sync mode for batch generation
