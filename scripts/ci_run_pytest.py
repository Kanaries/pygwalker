#!/usr/bin/env python3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

JUNIT_PATH = Path("pytest-results.xml")
HARD_TIMEOUT_SECONDS = 20 * 60
PASS_GRACE_SECONDS = 30
POLL_SECONDS = 1


def _terminate_process(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _junit_all_passed(junit_path: Path) -> bool:
    if not junit_path.exists():
        return False

    try:
        root = ET.parse(junit_path).getroot()
    except ET.ParseError:
        return False

    if root.tag == "testsuite":
        suites = [root]
    else:
        suites = root.findall("testsuite")

    if not suites:
        return False

    total_tests = 0
    total_failures = 0
    total_errors = 0
    for suite in suites:
        total_tests += int(suite.attrib.get("tests", 0))
        total_failures += int(suite.attrib.get("failures", 0))
        total_errors += int(suite.attrib.get("errors", 0))

    return total_tests > 0 and total_failures == 0 and total_errors == 0


def main() -> int:
    cmd = [
        sys.executable,
        "-X",
        "faulthandler",
        "-m",
        "pytest",
        "-o",
        "faulthandler_timeout=300",
        "--junitxml=pytest-results.xml",
        "tests",
    ]

    print("[CI] pytest start", flush=True)
    proc = subprocess.Popen(cmd)
    start_time = time.time()
    pass_detected_at = None

    while True:
        rc = proc.poll()
        if rc is not None:
            print("[CI] pytest end", flush=True)
            return rc

        if _junit_all_passed(JUNIT_PATH):
            if pass_detected_at is None:
                pass_detected_at = time.time()
            elif time.time() - pass_detected_at >= PASS_GRACE_SECONDS:
                print(
                    "[CI] pytest summary indicates success but process is still alive; "
                    "terminating stuck process and continuing.",
                    flush=True
                )
                _terminate_process(proc)
                print("[CI] pytest end", flush=True)
                return 0
        else:
            pass_detected_at = None

        if time.time() - start_time >= HARD_TIMEOUT_SECONDS:
            print("[CI] pytest watchdog timeout reached; terminating process.", flush=True)
            _terminate_process(proc)
            print("[CI] pytest end", flush=True)
            return 1

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    raise SystemExit(main())
