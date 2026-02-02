import os
import requests
from requests.auth import HTTPBasicAuth

def fetch_issue(issue_key: str) -> dict:
    """Fetch a Jira issue by key and return a small normalized dict.

    Expects env vars: JIRA_BASE_URL, JIRA_USER, JIRA_API_TOKEN
    """
    base = os.getenv("JIRA_BASE_URL")
    user = os.getenv("JIRA_USER")
    token = os.getenv("JIRA_API_TOKEN")
    if not all([base, user, token]):
        raise RuntimeError("Set JIRA_BASE_URL, JIRA_USER, JIRA_API_TOKEN in environment")

    url = f"{base.rstrip('/')}/rest/api/2/issue/{issue_key}"
    resp = requests.get(url, auth=HTTPBasicAuth(user, token), headers={"Accept": "application/json"})
    resp.raise_for_status()
    data = resp.json()
    fields = data.get("fields", {})
    return {
        "key": issue_key,
        "summary": fields.get("summary") or "",
        "description": fields.get("description") or "",
        "raw": data,
    }
