from typing import Dict
from .llm_client import LLMClient

def make_testcase_prompt(issue: Dict) -> str:
    return (
        "Given the following Jira requirement, produce a set of structured test cases. "
        "For each test case provide: id, title, preconditions, steps (ordered), expected result, and example test data. "
        "Return output in Markdown with clear headings.\n\n"
        f"Requirement key: {issue.get('key')}\n"
        f"Summary: {issue.get('summary')}\n"
        f"Description: {issue.get('description')}\n"
    )

def generate_testcases(issue: Dict, llm: LLMClient) -> str:
    prompt = make_testcase_prompt(issue)
    return llm.generate(prompt)

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
