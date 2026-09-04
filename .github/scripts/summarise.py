"""Turn a JUnit XML file into a markdown summary for the job summary and PR comment."""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def collect(path):
    root = ET.parse(path).getroot()

    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")

    total = failed = errored = skipped = 0
    duration = 0.0
    problems = []

    for suite in suites:
        total += int(suite.get("tests", 0))
        failed += int(suite.get("failures", 0))
        errored += int(suite.get("errors", 0))
        skipped += int(suite.get("skipped", 0))
        duration += float(suite.get("time", 0))

        for case in suite.iter("testcase"):
            bad = case.find("failure") if case.find("failure") is not None else case.find("error")
            if bad is not None:
                name = case.get("name")
                message = (bad.get("message") or "").splitlines()
                problems.append((name, message[0] if message else ""))

    passed = total - failed - errored - skipped

    return {
        "total": total,
        "passed": passed,
        "failed": failed + errored,
        "skipped": skipped,
        "duration": duration,
        "problems": problems,
    }


def render(result):
    icon = "green_circle" if not result["failed"] else "red_circle"

    lines = [
        f":{icon}: **{result['passed']}/{result['total']} passed**"
        f" in {result['duration']:.0f}s",
        "",
        "| Passed | Failed | Skipped | Total |",
        "|---:|---:|---:|---:|",
        f"| {result['passed']} | {result['failed']} | {result['skipped']} | {result['total']} |",
    ]

    if result["problems"]:
        lines += ["", "**Failures**", ""]
        for name, message in result["problems"][:15]:
            lines.append(f"- `{name}`: {message[:160]}")
        if len(result["problems"]) > 15:
            lines.append(f"- …and {len(result['problems']) - 15} more")

    return "\n".join(lines) + "\n"


def main():
    path = Path(sys.argv[1])

    if not path.exists():
        body = ":red_circle: **The suite produced no results.** The run probably failed before tests started.\n"
    else:
        body = render(collect(path))

    print(body)

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write(body)

    # Each step gets its own GITHUB_STEP_SUMMARY file, so the comment step cannot read
    # the one written here. Keep a copy it can pick up.
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(body)


if __name__ == "__main__":
    main()
