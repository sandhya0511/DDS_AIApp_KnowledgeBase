# Copilot Instructions for my_agent

## Purpose
This repo is a small prototype: it fetches a Jira requirement and uses an LLM to generate test cases, test data, and automation skeletons for Selenium and Playwright.

These instructions orient an AI coding agent to be immediately productive with the codebase.

## Key files
- `agent.py` — existing example agent used in prior experiments (Google ADK/gemini).
- `tstgen/jira_client.py` — Jira REST fetcher; expects `JIRA_BASE_URL`, `JIRA_USER`, `JIRA_API_TOKEN`.
- `tstgen/llm_client.py` — thin OpenAI wrapper; requires `OPENAI_API_KEY`, optional `OPENAI_MODEL`.
- `tstgen/generator.py` — prompt templates and code skeleton renderers.
- `tstgen/cli.py` — simple CLI entrypoint: `python -m tstgen.cli ISSUE-123`.

## Environment & run
- Copy `.env.example` → `.env` and fill secrets.
- Install deps: `pip install -r requirements.txt`.
- Run: `python -m tstgen.cli ISSUE-KEY` to produce `outputs/ISSUE-KEY.md`, `.selenium.py`, `.playwright.py`.

## Conventions & patterns
- Tools (Jira fetcher, LLM) are thin wrappers exposing small, testable functions.
- LLM usage is prompt-driven: `generator.py` owns prompt templates and returned artefact formatting.
- Automation skeletons are intentionally minimal — they are scaffolding for engineers to refine.

## Extensions you may be asked to implement
- Add richer prompt engineering (structured JSON output) and a parser that converts LLM JSON -> Python objects.
- Add pytest-based integration tests that validate generated artifacts against a live test site (mocked).
- Add a web API (FastAPI) endpoint to receive issue keys and return generated artifacts.

## Security notes
- Secrets live in env vars. Do not store API keys or tokens in source control.
- Generated code should be reviewed before running in CI or production.

## Suggested next tasks for the agent
1. Add structured LLM output option (JSON) and a validator.
2. Implement optional Jira query by JQL to batch-generate for multiple requirements.
3. Add a `--provider` option to support other LLM providers (Gemini/OpenAI) using pluggable clients.

If anything is missing or you'd like me to prioritize one of the suggested tasks, tell me which to do next.
