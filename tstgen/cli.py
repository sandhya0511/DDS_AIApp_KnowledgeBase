import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from .jira_client import fetch_issue
from .llm_client import LLMClient
from .generator import generate_testcases, generate_selenium_script, generate_playwright_script, format_testcases_as_markdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

OUTPUT_DIR = Path.cwd() / "outputs"

def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python -m tstgen.cli ISSUE-KEY [--no-cache] [--mock]")
        sys.exit(2)
    
    issue_key = argv[0]
    use_cache = "--no-cache" not in argv
    use_mock = "--mock" in argv

    print(f"Fetching {issue_key} from Jira...")
    issue = fetch_issue(issue_key)

    print("Initializing LLM client...")
    try:
        llm = LLMClient(cache_enabled=use_cache)
    except RuntimeError as e:
        if use_mock:
            print(f"Warning: {e}. Using mock output.")
            llm = None
        else:
            raise

    print("Generating test cases via LLM...")
    if llm and not use_mock:
        testcases_dict = generate_testcases(issue, llm, use_json=True)
        testcases_md = format_testcases_as_markdown(testcases_dict)
    else:
        # Mock output
        testcases_dict = {
            "positive_cases": [
                {
                    "id": "TC-1",
                    "title": "Basic flow",
                    "preconditions": "Setup complete",
                    "steps": ["Step 1", "Step 2"],
                    "expected_result": "Success",
                }
            ],
            "negative_cases": [],
            "edge_cases": [],
            "test_data": {},
        }
        testcases_md = format_testcases_as_markdown(testcases_dict)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUTPUT_DIR / issue_key
    base.parent.mkdir(parents=True, exist_ok=True)

    md_file = base.with_suffix('.md')
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(testcases_md)

    print(f"Generated testcases -> {md_file}")

    print("Generating automation skeletons...")
    selenium_code = generate_selenium_script(issue, testcases_md)
    playwright_code = generate_playwright_script(issue, testcases_md)

    (base.with_suffix('.selenium.py')).write_text(selenium_code, encoding='utf-8')
    (base.with_suffix('.playwright.py')).write_text(playwright_code, encoding='utf-8')

    print(f"Wrote Selenium and Playwright skeletons to outputs for {issue_key}")
    
    # Show LLM stats if available
    if llm:
        stats = llm.get_rate_limit_status()
        print(f"\nLLM Stats:")
        print(f"  API calls: {stats['total_api_calls']}")
        print(f"  Tokens used: {stats['total_tokens_used']}")
        print(f"  Rate limited: {stats['is_rate_limited']}")

if __name__ == '__main__':
    main()
