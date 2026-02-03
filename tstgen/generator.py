import json
from typing import Dict, List, Optional
from .llm_client import LLMClient


def make_testcase_prompt(issue: Dict, use_json: bool = True) -> str:
    """Create a prompt for test case generation with optional JSON structure."""
    base = (
        f"Requirement key: {issue.get('key')}\n"
        f"Summary: {issue.get('summary')}\n"
        f"Description: {issue.get('description')}\n\n"
    )
    
    if use_json:
        return (
            base +
            "Generate comprehensive test cases with positive, negative, and edge cases. "
            "Return ONLY valid JSON (no markdown) with this structure:\n"
            "{\n"
            "  \"positive_cases\": [\n"
            "    {\"id\": \"TC-1\", \"title\": \"...\", \"preconditions\": \"...\", "
            "\"steps\": [\"step1\", \"step2\"], \"expected_result\": \"...\"}\n"
            "  ],\n"
            "  \"negative_cases\": [\n"
            "    {\"id\": \"TC-N1\", \"title\": \"...\", \"preconditions\": \"...\", "
            "\"steps\": [...], \"expected_result\": \"...\"}\n"
            "  ],\n"
            "  \"edge_cases\": [\n"
            "    {\"id\": \"TC-E1\", \"title\": \"...\", \"preconditions\": \"...\", "
            "\"steps\": [...], \"expected_result\": \"...\"}\n"
            "  ],\n"
            "  \"test_data\": {\"example_input\": \"...\", \"boundary_values\": []}\n"
            "}"
        )
    else:
        return (
            base +
            "Given the above requirement, produce a set of structured test cases. "
            "For each test case provide: id, title, preconditions, steps (ordered), expected result, and example test data. "
            "Return output in Markdown with clear headings for Positive, Negative, and Edge Cases."
        )


def generate_testcases(issue: Dict, llm: LLMClient, use_json: bool = True) -> Dict:
    """Generate test cases, optionally as structured JSON.
    
    Returns:
        If use_json=True: dict with keys 'positive_cases', 'negative_cases', 'edge_cases', 'test_data'
        If use_json=False: dict with key 'markdown' containing markdown text
    """
    prompt = make_testcase_prompt(issue, use_json=use_json)
    response = llm.generate(prompt, max_tokens=3000, structured_json=use_json)
    
    if use_json:
        try:
            parsed = json.loads(response)
            return parsed
        except json.JSONDecodeError as e:
            # Fallback: return as markdown if JSON parsing fails
            return {
                "positive_cases": [],
                "negative_cases": [],
                "edge_cases": [],
                "test_data": {},
                "raw_markdown": response,
                "parse_error": str(e),
            }
    else:
        return {"markdown": response}


def format_testcases_as_markdown(testcases: Dict) -> str:
    """Convert structured test case dict to readable Markdown."""
    md = "# Test Cases\n\n"
    
    # Positive cases
    if testcases.get("positive_cases"):
        md += "## Positive Cases\n"
        for tc in testcases["positive_cases"]:
            md += f"\n### {tc.get('id', 'N/A')}: {tc.get('title', 'N/A')}\n"
            md += f"- **Preconditions**: {tc.get('preconditions', 'N/A')}\n"
            if tc.get("steps"):
                md += "- **Steps**:\n"
                for i, step in enumerate(tc["steps"], 1):
                    md += f"  {i}. {step}\n"
            md += f"- **Expected Result**: {tc.get('expected_result', 'N/A')}\n"
    
    # Negative cases
    if testcases.get("negative_cases"):
        md += "\n## Negative Cases\n"
        for tc in testcases["negative_cases"]:
            md += f"\n### {tc.get('id', 'N/A')}: {tc.get('title', 'N/A')}\n"
            md += f"- **Preconditions**: {tc.get('preconditions', 'N/A')}\n"
            if tc.get("steps"):
                md += "- **Steps**:\n"
                for i, step in enumerate(tc["steps"], 1):
                    md += f"  {i}. {step}\n"
            md += f"- **Expected Result**: {tc.get('expected_result', 'N/A')}\n"
    
    # Edge cases
    if testcases.get("edge_cases"):
        md += "\n## Edge Cases\n"
        for tc in testcases["edge_cases"]:
            md += f"\n### {tc.get('id', 'N/A')}: {tc.get('title', 'N/A')}\n"
            md += f"- **Preconditions**: {tc.get('preconditions', 'N/A')}\n"
            if tc.get("steps"):
                md += "- **Steps**:\n"
                for i, step in enumerate(tc["steps"], 1):
                    md += f"  {i}. {step}\n"
            md += f"- **Expected Result**: {tc.get('expected_result', 'N/A')}\n"
    
    # Test data
    if testcases.get("test_data"):
        md += "\n## Test Data\n"
        for key, val in testcases["test_data"].items():
            md += f"- **{key}**: {val}\n"
    
    # Include raw markdown if parsing had errors
    if testcases.get("raw_markdown"):
        md += f"\n## Raw LLM Output\n```\n{testcases['raw_markdown']}\n```\n"
    
    return md

def generate_selenium_script(issue: Dict, testcase_markdown: str) -> str:
    # Simple skeleton: uses pytest + selenium webdriver
    name = issue.get("key", "ISSUE")
    return f"""
import pytest
from selenium import webdriver

def test_{name.lower().replace('-', '_')}_smoke():
    # Selenium skeleton generated from requirement {name}
    driver = webdriver.Chrome()
    try:
        # TODO: adapt navigation and assertions from testcase content
        driver.get('http://example.com')
        assert 'Example' in driver.title
    finally:
        driver.quit()
"""

def generate_playwright_script(issue: Dict, testcase_markdown: str) -> str:
    name = issue.get("key", "ISSUE")
    return f"""
from playwright.sync_api import sync_playwright

def test_{name.lower().replace('-', '_')}_smoke():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://example.com')
        assert 'Example' in page.title()
        browser.close()
"""
