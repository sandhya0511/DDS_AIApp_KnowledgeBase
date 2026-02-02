from pathlib import Path
from tstgen.generator import generate_selenium_script, generate_playwright_script


def run():
    issue = {"key": "SMOKE-1", "summary": "Smoke test summary", "description": "Smoke test description"}
    selenium = generate_selenium_script(issue, "")
    playwright = generate_playwright_script(issue, "")

    out = Path.cwd() / "outputs" / "smoke-test"
    out.mkdir(parents=True, exist_ok=True)
    (out / "smoke.selenium.py").write_text(selenium, encoding="utf-8")
    (out / "smoke.playwright.py").write_text(playwright, encoding="utf-8")

    print("Wrote:", out / "smoke.selenium.py")
    print("Wrote:", out / "smoke.playwright.py")


if __name__ == '__main__':
    run()
