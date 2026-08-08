"""Generate a performance baseline report for the LAAP core test suite."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


CORE_SUITES = [
    "laap/triphase_bridge/tests",
    "tests/unit/test_body_tools.py",
    "tests/test_stability.py",
    "tests/test_cognitive_engine.py",
    "tests/test_affective_dynamics.py",
    "tests/unit/test_capabilities_cli.py",
]


def run_pytest(suites: List[str]) -> Dict[str, Any]:
    """Run pytest with JSON report output and return parsed summary."""
    report_path = Path("benchmarks/baseline_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *suites,
        "-q",
        "--json-report",
        f"--json-report-file={report_path}",
        "--json-report-summary",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    summary = {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }

    if report_path.exists():
        data = json.loads(report_path.read_text(encoding="utf-8"))
        summary["report"] = data.get("summary", {})
        summary["report"]["duration"] = data.get("duration", 0.0)
        summary["tests"] = [
            {
                "nodeid": t.get("nodeid"),
                "outcome": t.get("outcome"),
                "duration": t.get("duration"),
                "setup_duration": t.get("setup", {}).get("duration"),
                "teardown_duration": t.get("teardown", {}).get("duration"),
            }
            for t in data.get("tests", [])
        ]
    else:
        summary["report"] = {}
        summary["tests"] = []

    return summary


def build_baseline(summary: Dict[str, Any]) -> Dict[str, Any]:
    """Build the baseline report object."""
    report = summary.get("report", {})
    tests = summary.get("tests", [])

    passed = report.get("passed", 0)
    failed = report.get("failed", 0)
    skipped = report.get("skipped", 0)
    total = report.get("total", 0)
    duration = report.get("duration", 0.0)

    slowest = sorted(
        [t for t in tests if t.get("duration") is not None],
        key=lambda x: x["duration"],
        reverse=True,
    )[:20]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "suites": CORE_SUITES,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration_seconds": round(duration, 3),
            "tests_per_second": round(total / duration, 2) if duration else 0.0,
        },
        "slowest_tests": [
            {"nodeid": t["nodeid"], "duration_seconds": round(t["duration"], 4)}
            for t in slowest
        ],
    }


def main() -> int:
    print("[INFO] Running core test suites for performance baseline...")
    summary = run_pytest(CORE_SUITES)

    if summary["returncode"] != 0:
        print("[WARN] pytest exited with non-zero code; baseline may include failures.")

    baseline = build_baseline(summary)

    output_path = Path("benchmarks/performance_baseline.json")
    output_path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Baseline written to {output_path}")

    # Also print a concise summary
    s = baseline["summary"]
    print(f"[OK] {s['passed']} passed, {s['failed']} failed, {s['skipped']} skipped")
    print(f"[OK] Total duration: {s['duration_seconds']}s ({s['tests_per_second']} tests/s)")
    return summary["returncode"]


if __name__ == "__main__":
    sys.exit(main())
