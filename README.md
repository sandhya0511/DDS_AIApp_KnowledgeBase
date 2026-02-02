# tstgen — Test Scenario Generator

Small prototype that fetches a Jira requirement and generates:
- human-readable test cases
- test data
- automation skeletons for Selenium and Playwright

## Quick start

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Set environment variables (see `.env.example`):

```
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_USER=you@example.com
JIRA_API_TOKEN=your_api_token_here
OPENAI_API_KEY=sk-...your_openai_key_here...
OPENAI_MODEL=gpt-4o-mini
```

3. Run the CLI to generate artifacts for an issue:

```bash
python -m tstgen.cli ISSUE-123
```

Outputs are written to `outputs/`.

## Files to inspect

- `tstgen/jira_client.py` — simple Jira REST API fetcher
- `tstgen/llm_client.py` — thin OpenAI wrapper (uses `OPENAI_API_KEY`)
- `tstgen/generator.py` — prompt templates and renderers
- `tstgen/cli.py` — small command-line entrypoint

## Feedback

If you want additional features (project-level scaffolding for pytest, CI jobs, or direct Jira transitions), tell me which to add next.
