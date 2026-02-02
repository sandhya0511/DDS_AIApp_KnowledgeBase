import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from .jira_client import fetch_issue
from .llm_client import LLMClient
from .generator import generate_testcases, generate_selenium_script, generate_playwright_script

load_dotenv()

OUTPUT_DIR = Path.cwd() / "outputs"

def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print("Usage: python -m tstgen.cli ISSUE-KEY")
        sys.exit(2)
    issue_key = argv[0]

    print(f"Fetching {issue_key} from Jira...")
    issue = fetch_issue(issue_key)

    print("Initializing LLM client...")
    llm = LLMClient()

    print("Generating test cases via LLM...")
    test_md = generate_testcases(issue, llm)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = OUTPUT_DIR / issue_key
    base.parent.mkdir(parents=True, exist_ok=True)

    md_file = base.with_suffix('.md')
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(test_md)

    print(f"Generated testcases -> {md_file}")

    print("Generating automation skeletons...")
    selenium_code = generate_selenium_script(issue, test_md)
    playwright_code = generate_playwright_script(issue, test_md)

    (base.with_suffix('.selenium.py')).write_text(selenium_code, encoding='utf-8')
    (base.with_suffix('.playwright.py')).write_text(playwright_code, encoding='utf-8')

    print(f"Wrote Selenium and Playwright skeletons to outputs for {issue_key}")

if __name__ == '__main__':
    main()
