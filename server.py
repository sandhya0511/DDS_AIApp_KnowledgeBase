from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import os
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="tstgen API")

try:
    from tstgen.generator import (
        generate_testcases,
        generate_selenium_script,
        generate_playwright_script,
        format_testcases_as_markdown,
    )
    from tstgen.llm_client import LLMClient
except Exception as e:
    # If imports fail, we'll still allow mock operation
    generate_testcases = None
    generate_selenium_script = None
    generate_playwright_script = None
    format_testcases_as_markdown = None
    LLMClient = None


class GenerateRequest(BaseModel):
    key: Optional[str] = None
    summary: str
    description: Optional[str] = ""
    use_history: Optional[bool] = True
    mock: Optional[bool] = False
    structured_json: Optional[bool] = True


# Global LLM client instance (shared across requests for cache efficiency)
_llm_client = None


def get_llm_client():
    """Get or create a shared LLM client."""
    global _llm_client
    if _llm_client is None:
        try:
            _llm_client = LLMClient(cache_enabled=True)
        except Exception:
            pass
    return _llm_client


def _load_history(query: str, limit: int = 5) -> List[dict]:
    outdir = os.path.join(os.getcwd(), "outputs")
    results = []
    if not os.path.isdir(outdir):
        return results
    for fname in os.listdir(outdir)[:limit]:
        path = os.path.join(outdir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read(1000)
        except Exception:
            text = ""
        results.append({"file": fname, "snippet": text})
    return results


@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    issue = {"key": req.key or "ISSUE-1", "summary": req.summary, "description": req.description}

    # Decide whether to use LLM or mock
    testcases_dict = {}
    testcases_markdown = ""
    selenium_py = ""
    playwright_py = ""

    use_mock = req.mock or os.getenv("OPENAI_API_KEY") is None or LLMClient is None

    if not use_mock:
        try:
            llm = get_llm_client()
            if llm is None:
                use_mock = True
            else:
                # Generate structured test cases
                testcases_dict = generate_testcases(
                    issue, llm, use_json=req.structured_json
                )
                testcases_markdown = format_testcases_as_markdown(testcases_dict)
                selenium_py = generate_selenium_script(issue, testcases_markdown)
                playwright_py = generate_playwright_script(issue, testcases_markdown)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    if use_mock:
        # Basic mock output if LLM unavailable
        testcases_dict = {
            "positive_cases": [
                {
                    "id": "TC-1",
                    "title": "Basic happy path",
                    "preconditions": "User logged in",
                    "steps": ["Navigate to feature", "Perform action", "Verify result"],
                    "expected_result": "Action completes successfully",
                }
            ],
            "negative_cases": [
                {
                    "id": "TC-N1",
                    "title": "Invalid input triggers validation",
                    "preconditions": "User logged in",
                    "steps": ["Enter invalid data", "Submit form"],
                    "expected_result": "Error message displayed",
                }
            ],
            "edge_cases": [
                {
                    "id": "TC-E1",
                    "title": "Boundary value at limit",
                    "preconditions": "User logged in",
                    "steps": ["Enter max value", "Submit"],
                    "expected_result": "Accepted or error shown",
                }
            ],
            "test_data": {"example_input": "test_value", "boundary_values": ["min", "max"]},
        }
        testcases_markdown = format_testcases_as_markdown(testcases_dict)
        selenium_py = "# Mock selenium script\nprint('selenium mock')\n"
        playwright_py = "# Mock playwright script\nprint('playwright mock')\n"

    history = _load_history(req.summary if req.use_history else "") if req.use_history else []

    # Get rate limit status if LLM is available
    rate_limit_status = None
    llm = get_llm_client()
    if llm:
        rate_limit_status = llm.get_rate_limit_status()

    return {
        "issue": issue,
        "testcases": testcases_dict,
        "testcases_markdown": testcases_markdown,
        "selenium_script": selenium_py,
        "playwright_script": playwright_py,
        "history": history,
        "mock": use_mock,
        "rate_limit_status": rate_limit_status,
    }


@app.get("/api/status")
def api_status():
    """Get current API status including rate limits and cache info."""
    llm = get_llm_client()
    if not llm:
        return {"status": "LLM not available", "rate_limit_status": None}

    return {
        "status": "ok",
        "rate_limit_status": llm.get_rate_limit_status(),
    }


@app.post("/api/clear-cache")
def api_clear_cache():
    """Clear the LLM response cache."""
    llm = get_llm_client()
    if llm:
        llm.clear_cache()
        return {"status": "Cache cleared"}
    return {"status": "LLM not available"}


# Serve frontend static files
if os.path.isdir("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
