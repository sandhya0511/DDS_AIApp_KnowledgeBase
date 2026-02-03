# LLM Optimization & Rate Limit Handling

This document describes the LLM optimizations implemented to improve API interactions, handle latency, and respect rate limits.

## Features Implemented

### 1. Retry Logic with Exponential Backoff
**File**: `tstgen/llm_client.py`

- **What**: Automatic retry on transient errors (rate limits, timeouts, API errors)
- **How**: Exponential backoff: 2s, 4s, 8s between retries (configurable `max_retries=3`)
- **Benefits**: Gracefully handles temporary API failures without user intervention
- **Example**:
  ```python
  llm = LLMClient(max_retries=3, timeout=30)
  # Automatically retries on failure
  response = llm.generate(prompt)
  ```

### 2. Response Caching
**File**: `tstgen/cache.py`

- **What**: File-based caching of LLM responses with TTL (time-to-live)
- **How**: 
  - Prompt + model → SHA256 hash → `.cache/` directory
  - Default TTL: 24 hours (configurable)
  - Automatic cleanup of expired entries
- **Benefits**:
  - Reduces redundant API calls for identical prompts
  - Significantly lower API costs
  - Faster response times for cached queries
- **Usage**:
  ```python
  llm = LLMClient(cache_enabled=True, cache_ttl_hours=24)
  response1 = llm.generate(prompt)  # API call
  response2 = llm.generate(prompt)  # Cache hit
  llm.clear_cache()                 # Manual clear
  ```

### 3. Structured JSON Output
**File**: `tstgen/generator.py`

- **What**: Request LLM to return structured JSON for test cases
- **How**: Enhanced prompts request specific JSON format:
  ```json
  {
    "positive_cases": [...],
    "negative_cases": [...],
    "edge_cases": [...],
    "test_data": {...}
  }
  ```
- **Benefits**:
  - Consistent, parseable output
  - Better separation of positive/negative/edge cases
  - Enables downstream processing and filtering
  - Automatic validation of JSON structure
- **Implementation**:
  - Client adds validation instruction to prompt
  - Validates JSON is valid before returning
  - Falls back to markdown if JSON parsing fails

### 4. Rate Limit Awareness
**File**: `tstgen/llm_client.py`

- **What**: Tracks and respects OpenAI rate limits
- **How**:
  - Monitors `RateLimitError` responses
  - Extracts `Retry-After` header when available
  - Automatically waits before retrying
  - Tracks total tokens and API calls
- **Status endpoint**: `/api/status`
  ```json
  {
    "total_api_calls": 5,
    "total_tokens_used": 3421,
    "is_rate_limited": false,
    "rate_limit_resets_in_seconds": null
  }
  ```

### 5. Token Usage Tracking
**File**: `tstgen/llm_client.py`

- **What**: Monitors token consumption for cost estimation
- **How**:
  - Extracts `prompt_tokens` and `completion_tokens` from API response
  - Accumulates in `total_tokens_used`
  - Provides per-call breakdown in logs
- **Benefits**:
  - Visibility into API costs
  - Helps identify high-cost prompts
  - Useful for billing and optimization decisions

### 6. Configurable Timeouts
**File**: `tstgen/llm_client.py`

- **What**: API request timeout configuration
- **How**: `timeout=30` seconds (configurable)
- **Benefits**:
  - Prevents hanging on slow responses
  - Triggers automatic retry on timeout
  - Graceful degradation

### 7. Structured Logging
**File**: `tstgen/llm_client.py`

- **What**: Detailed logging of LLM interactions
- **How**: Using Python's `logging` module
- **Output**: 
  ```
  INFO: API call successful. Tokens: +450 (total: 1200), calls: 3
  WARNING: Rate limit hit. Backing off 2s (attempt 1/3)
  INFO: Cache hit for prompt
  ```

## API Endpoints

### POST `/api/generate`
Generate test cases with rate limit tracking.

**Request**:
```json
{
  "key": "ISSUE-123",
  "summary": "User login feature",
  "description": "Users should be able to login with email and password",
  "use_history": true,
  "mock": false,
  "structured_json": true
}
```

**Response**:
```json
{
  "issue": {...},
  "testcases": {...},
  "testcases_markdown": "...",
  "selenium_script": "...",
  "playwright_script": "...",
  "history": [...],
  "mock": false,
  "rate_limit_status": {
    "model": "gpt-4o-mini",
    "total_api_calls": 3,
    "total_tokens_used": 1200,
    "is_rate_limited": false,
    "rate_limit_resets_in_seconds": null
  }
}
```

### GET `/api/status`
Check current API usage and rate limit status.

**Response**:
```json
{
  "status": "ok",
  "rate_limit_status": {...}
}
```

### POST `/api/clear-cache`
Manually clear the response cache.

**Response**:
```json
{
  "status": "Cache cleared"
}
```

## CLI Usage

```bash
# Standard generation with caching enabled
python -m tstgen.cli ISSUE-123

# Disable cache for fresh responses
python -m tstgen.cli ISSUE-123 --no-cache

# Use mock output (no API calls)
python -m tstgen.cli ISSUE-123 --mock
```

## Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
OPENAI_MODEL=gpt-4o-mini
```

## Performance Considerations

### Caching Impact
- **First call**: ~3-5 seconds (API latency)
- **Cached call**: ~10ms (local file read)
- **Cost savings**: 95%+ reduction for repeated prompts

### Rate Limit Optimization
- **OpenAI limits** (as of Feb 2025):
  - GPT-4o-mini: 500K tokens/minute
  - Standard tier: 3 requests/minute
- **Our strategy**:
  - Cache aggressively for common patterns
  - Batch similar requests
  - Automatic exponential backoff prevents thundering herd

### Token Usage
- Typical test case generation: 400-600 tokens
- Caching reduces token waste for repeated requests
- Monitor `/api/status` to track costs

## Error Handling

### Rate Limit Hit
```
⚠️ Rate limit hit. Backing off 2s (attempt 1/3)
```
- Automatic retry with exponential backoff
- Frontend shows reset time

### JSON Parse Error
```
ERROR: Invalid JSON in response
```
- Falls back to markdown output
- Includes raw response in error field

### API Connection Error
```
ERROR: API connection error
```
- Retried up to `max_retries` times
- Raises if all retries fail

## Best Practices

1. **Always enable caching** in production:
   ```python
   llm = LLMClient(cache_enabled=True)
   ```

2. **Monitor rate limits** via `/api/status` endpoint

3. **Use structured JSON** for consistent parsing:
   ```python
   response = llm.generate(prompt, structured_json=True)
   ```

4. **Check token usage** to estimate costs:
   ```python
   status = llm.get_rate_limit_status()
   print(f"Tokens: {status['total_tokens_used']}")
   ```

5. **Set appropriate timeouts** for your SLA:
   ```python
   llm = LLMClient(timeout=60)
   ```

## Troubleshooting

### "Set OPENAI_API_KEY in environment"
```bash
export OPENAI_API_KEY=sk-...
```

### Frequent rate limits
- Increase cache TTL: `cache_ttl_hours=48`
- Batch requests together
- Consider upgrading to higher tier

### Timeout errors
- Increase timeout: `timeout=60`
- Check OpenAI service status
- Verify network connectivity

## Future Enhancements

- [ ] Async support for concurrent requests
- [ ] Request batching to reduce API calls
- [ ] Cost estimation and alerts
- [ ] Persistent statistics database
- [ ] A/B testing of prompts
- [ ] Multi-provider support (Gemini, Claude, etc.)
